"""Policy Sync - downloads policy bundles from CortexHub cloud.

This is the INBOUND flow: policies created by security/compliance team
in the cloud UI are synced to the SDK for local enforcement.

Key invariants:
- Policies are PULLED by SDK, never pushed
- SDK can operate 100% offline with local policies
- Cloud policies override local policies when connected
"""

import json
from pathlib import Path
from typing import Any

import httpx
import structlog

logger = structlog.get_logger(__name__)


class PolicySync:
    """Syncs policy bundles from CortexHub cloud.
    
    Flow:
    1. Security team creates policies in cloud UI
    2. SDK periodically pulls policy bundle
    3. SDK enforces policies locally
    4. No customer data involved in sync
    """
    
    def __init__(
        self,
        api_key: str | None,
        backend_url: str,
        local_policies_dir: str = "./policies",
        auto_sync: bool = True,
        sync_interval_seconds: int = 300,  # 5 minutes
    ):
        """Initialize policy sync.
        
        Args:
            api_key: API key for authentication
            backend_url: Backend API URL
            local_policies_dir: Directory for local policy cache
            auto_sync: Whether to auto-sync on init
            sync_interval_seconds: How often to sync (if background sync enabled)
        """
        self.api_key = api_key
        self.backend_url = backend_url.rstrip("/")
        self.local_policies_dir = Path(local_policies_dir)
        self.auto_sync = auto_sync
        self.sync_interval_seconds = sync_interval_seconds
        
        self._client: httpx.Client | None = None
        self._last_sync_version: str | None = None
        
        if api_key:
            self._client = httpx.Client(
                base_url=self.backend_url,
                headers={"X-API-Key": api_key},
                timeout=30.0,
            )
        
        # Ensure local directory exists
        self.local_policies_dir.mkdir(parents=True, exist_ok=True)
        
        # Auto-sync on init if enabled
        if auto_sync and api_key:
            self.sync()
    
    def sync(self) -> bool:
        """Sync policies from cloud.
        
        Returns:
            True if sync successful or no update needed
        """
        if not self.api_key or not self._client:
            logger.debug("No API key - using local policies only")
            return False
        
        try:
            # Check for updates first (lightweight)
            current_version = self._get_remote_version()
            
            if current_version == self._last_sync_version:
                logger.debug("Policies up to date", version=current_version)
                return True
            
            # Download full bundle
            bundle = self._download_bundle()
            
            if bundle:
                self._save_bundle(bundle)
                self._last_sync_version = current_version
                logger.info(
                    "Policies synced from cloud",
                    version=current_version,
                    policy_count=len(bundle.get("policies", [])),
                )
                return True
            
            return False
            
        except httpx.ConnectError:
            logger.warning("Backend unreachable - using local policies")
            return False
        except Exception as e:
            logger.error("Policy sync error", error=str(e))
            return False
    
    def _get_remote_version(self) -> str | None:
        """Get current policy bundle version from cloud."""
        if not self._client:
            return None
        
        try:
            response = self._client.get("/policies/version")
            if response.status_code == 200:
                return response.json().get("version")
        except Exception:
            pass
        
        return None
    
    def _download_bundle(self) -> dict[str, Any] | None:
        """Download full policy bundle from cloud."""
        if not self._client:
            return None
        
        try:
            response = self._client.get("/policies/bundle")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error("Failed to download policy bundle", error=str(e))
        
        return None
    
    def _save_bundle(self, bundle: dict[str, Any]) -> None:
        """Save policy bundle to local cache."""
        # Save Cedar policies
        cedar_dir = self.local_policies_dir / "cedar"
        cedar_dir.mkdir(parents=True, exist_ok=True)
        
        # Save main policies file
        policies_content = bundle.get("policies_cedar", "")
        if policies_content:
            (cedar_dir / "policies.cedar").write_text(policies_content)
        
        # Save schema
        schema = bundle.get("schema", {})
        if schema:
            (cedar_dir / "schema.json").write_text(json.dumps(schema, indent=2))
        
        # Save metadata
        metadata = {
            "version": bundle.get("version"),
            "synced_at": bundle.get("synced_at"),
            "policy_count": len(bundle.get("policies", [])),
        }
        (self.local_policies_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
        
        logger.debug(
            "Policy bundle saved locally",
            path=str(self.local_policies_dir),
        )
    
    def get_local_version(self) -> str | None:
        """Get version of locally cached policies."""
        metadata_file = self.local_policies_dir / "metadata.json"
        if metadata_file.exists():
            try:
                metadata = json.loads(metadata_file.read_text())
                return metadata.get("version")
            except Exception:
                pass
        return None
    
    def close(self):
        """Close the HTTP client."""
        if self._client:
            self._client.close()
