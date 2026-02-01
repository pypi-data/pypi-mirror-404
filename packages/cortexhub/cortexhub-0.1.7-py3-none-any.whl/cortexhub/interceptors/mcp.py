"""MCP (Model Context Protocol) server interceptor.

Intercepts calls to MCP servers and enforces policies before execution.
"""

from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class MCPInterceptor:
    """Intercepts and governs MCP server calls.

    MCP provides:
    - Tool/resource discovery
    - Prompts and sampling
    - Bidirectional communication with context providers
    """

    def __init__(self, cortex_hub: Any):  # Type: CortexHub
        """Initialize MCP interceptor.

        Args:
            cortex_hub: CortexHub instance for policy enforcement
        """
        self.cortex_hub = cortex_hub
        logger.info("MCP interceptor initialized")

    def intercept_mcp_client(self) -> None:
        """Intercept MCP client calls."""
        try:
            # MCP client library (if available)
            from mcp import Client

            if hasattr(Client, "_original_call_tool"):
                logger.info("MCP client already intercepted")
                return

            original_call_tool = Client.call_tool

            async def governed_call_tool(self, server_name: str, tool_name: str, arguments: dict):
                from cortexhub.policy.models import AuthorizationRequest

                request = AuthorizationRequest.create(
                    principal_id=self.cortex_hub.session_id,
                    action_name=f"mcp.{tool_name}",
                    resource_id=f"{server_name}.{tool_name}",
                    args=arguments,
                    framework="mcp",
                )

                self.cortex_hub.enforce(request)
                return await original_call_tool(self, server_name, tool_name, arguments)

            Client.call_tool = governed_call_tool
            Client._original_call_tool = original_call_tool

            logger.info("MCP client interceptor applied")

        except ImportError:
            logger.debug("MCP client not available, skipping interception")
        except Exception as e:
            logger.error("Failed to intercept MCP client", error=str(e))

    def apply_all(self) -> None:
        """Apply all MCP interceptors."""
        self.intercept_mcp_client()
        logger.info("All MCP interceptors applied")

    async def discover_mcp_tools(self, mcp_client) -> list[dict]:
        """Discover tools from MCP server via list_tools()."""

        tools: list[dict] = []
        try:
            result = await mcp_client.list_tools()
            for tool in result.tools:
                tools.append(
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters_schema": {
                            "type": "object",
                            "properties": tool.inputSchema.get("properties", {}),
                            "required": tool.inputSchema.get("required", []),
                        }
                        if tool.inputSchema
                        else None,
                        "source": "mcp",
                        "mcp_server_name": getattr(mcp_client, "server_name", None),
                    }
                )
        except Exception as e:
            logger.warning("Failed to discover MCP tools", error=str(e))
        return tools
