#!/usr/bin/env python3
"""Main MCP server that transforms FastAPI servers into MCP tools."""

import argparse
import asyncio
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Optional
from urllib.parse import urljoin

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


@dataclass
class AuthConfig:
    """Authentication configuration for API requests."""

    auth_type: Optional[str] = None  # 'bearer', 'apikey', 'basic', or None
    token: Optional[str] = None  # For bearer tokens
    api_key: Optional[str] = None  # For API keys
    api_key_header: str = "X-API-Key"  # Header name for API key
    username: Optional[str] = None  # For basic auth
    password: Optional[str] = None  # For basic auth
    custom_headers: dict[str, str] = field(default_factory=dict)  # Additional headers

    def get_headers(self) -> dict[str, str]:
        """Get HTTP headers for authentication."""
        headers = {}

        if self.auth_type == "bearer" and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        elif self.auth_type == "apikey" and self.api_key:
            headers[self.api_key_header] = self.api_key

        # Add custom headers
        headers.update(self.custom_headers)

        return headers

    def get_auth(self) -> Optional[tuple[str, str]]:
        """Get basic auth tuple if configured."""
        if self.auth_type == "basic" and self.username and self.password:
            return (self.username, self.password)
        return None


class FastAPIMCPServer:
    """MCP server that wraps a FastAPI server."""

    def __init__(self, fastapi_url: str, auth_config: Optional[AuthConfig] = None):
        self.fastapi_url = fastapi_url.rstrip("/")
        self.auth_config = auth_config or AuthConfig()
        self.openapi_schema: Optional[dict] = None
        self.tools: list[Tool] = []

        # Create HTTP client with auth
        client_kwargs = {"timeout": 30.0}

        # Add headers if available
        headers = self.auth_config.get_headers()
        if headers:
            client_kwargs["headers"] = headers

        # Add basic auth if configured
        auth = self.auth_config.get_auth()
        if auth:
            client_kwargs["auth"] = auth

        self.http_client = httpx.AsyncClient(**client_kwargs)

    async def fetch_openapi_schema(self) -> dict:
        """Fetch the OpenAPI schema from the FastAPI server."""
        openapi_url = f"{self.fastapi_url}/openapi.json"
        try:
            response = await self.http_client.get(openapi_url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise RuntimeError(f"Failed to fetch OpenAPI schema from {openapi_url}: {e}")

    def _convert_openapi_param_to_json_schema(self, param: dict) -> dict:
        """Convert OpenAPI parameter to JSON schema format."""
        schema = param.get("schema", {})
        return {
            "type": schema.get("type", "string"),
            "description": param.get("description", ""),
            **({"enum": schema["enum"]} if "enum" in schema else {}),
            **({"default": schema["default"]} if "default" in schema else {}),
        }

    def _parse_tools_from_schema(self, schema: dict) -> list[Tool]:
        """Parse OpenAPI schema and create MCP tools."""
        tools = []
        paths = schema.get("paths", {})

        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method.upper() not in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    continue

                # Create tool name from operationId or fallback to method_path
                operation_id = operation.get("operationId", f"{method}_{path.replace('/', '_')}")
                tool_name = operation_id.replace(" ", "_").lower()

                # Build description
                description = operation.get("summary", operation.get("description", f"{method.upper()} {path}"))

                # Build input schema
                properties = {}
                required = []

                # Add path parameters
                parameters = operation.get("parameters", [])
                for param in parameters:
                    param_name = param["name"]
                    properties[param_name] = self._convert_openapi_param_to_json_schema(param)
                    if param.get("required", False):
                        required.append(param_name)

                # Add request body if present
                request_body = operation.get("requestBody")
                if request_body:
                    content = request_body.get("content", {})
                    if "application/json" in content:
                        body_schema = content["application/json"].get("schema", {})
                        # If it's a reference, note it; otherwise use the schema
                        if "$ref" in body_schema:
                            ref_name = body_schema["$ref"].split("/")[-1]
                            properties["body"] = {
                                "type": "object",
                                "description": f"Request body (schema: {ref_name})"
                            }
                        else:
                            properties["body"] = body_schema

                        if request_body.get("required", False):
                            required.append("body")

                input_schema = {
                    "type": "object",
                    "properties": properties,
                }
                if required:
                    input_schema["required"] = required

                # Store method and path in the tool for later use
                tool = Tool(
                    name=tool_name,
                    description=f"{description}\n\nHTTP: {method.upper()} {path}",
                    inputSchema=input_schema
                )
                tools.append(tool)

        return tools

    async def initialize(self):
        """Initialize by fetching and parsing the OpenAPI schema."""
        self.openapi_schema = await self.fetch_openapi_schema()
        self.tools = self._parse_tools_from_schema(self.openapi_schema)
        print(f"Discovered {len(self.tools)} tools from FastAPI server", file=sys.stderr)

    def _get_operation_details(self, tool_name: str) -> tuple[str, str]:
        """Get HTTP method and path for a tool."""
        paths = self.openapi_schema.get("paths", {})

        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method.upper() not in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    continue

                operation_id = operation.get("operationId", f"{method}_{path.replace('/', '_')}")
                if operation_id.replace(" ", "_").lower() == tool_name:
                    return method.upper(), path

        raise ValueError(f"Tool {tool_name} not found in schema")

    async def call_tool(self, tool_name: str, arguments: dict) -> list[TextContent]:
        """Execute a tool by calling the FastAPI endpoint."""
        method, path = self._get_operation_details(tool_name)

        # Replace path parameters
        url_path = path
        params = {}
        body = None

        for key, value in arguments.items():
            if key == "body":
                body = value
            elif f"{{{key}}}" in url_path:
                url_path = url_path.replace(f"{{{key}}}", str(value))
            else:
                params[key] = value

        url = f"{self.fastapi_url}{url_path}"

        try:
            # Make HTTP request
            if method == "GET":
                response = await self.http_client.get(url, params=params)
            elif method == "DELETE":
                response = await self.http_client.delete(url, params=params)
            elif method in ["POST", "PUT", "PATCH"]:
                response = await self.http_client.request(
                    method, url, params=params, json=body
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()

            # Return response
            try:
                result = response.json()
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
            except json.JSONDecodeError:
                return [TextContent(
                    type="text",
                    text=response.text
                )]

        except httpx.HTTPError as e:
            error_msg = f"HTTP error calling {method} {url}: {str(e)}"
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_detail = e.response.json()
                    error_msg += f"\nDetails: {json.dumps(error_detail, indent=2)}"
                except:
                    error_msg += f"\nResponse: {e.response.text}"

            return [TextContent(
                type="text",
                text=error_msg
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]

    async def cleanup(self):
        """Cleanup resources."""
        await self.http_client.aclose()


async def run_server(fastapi_url: str, auth_config: Optional[AuthConfig] = None):
    """Run the MCP server."""
    fastapi_server = FastAPIMCPServer(fastapi_url, auth_config)

    # Initialize and fetch schema
    await fastapi_server.initialize()

    # Create MCP server
    server = Server("gmcp")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return fastapi_server.tools

    @server.call_tool()
    async def call_tool(name: str, arguments: Any) -> list[TextContent]:
        return await fastapi_server.call_tool(name, arguments or {})

    try:
        # Run the server
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())
    finally:
        await fastapi_server.cleanup()


async def list_tools_mode(fastapi_url: str, auth_config: Optional[AuthConfig] = None):
    """List available tools without starting the MCP server."""
    fastapi_server = FastAPIMCPServer(fastapi_url, auth_config)

    try:
        await fastapi_server.initialize()

        print(f"\n✅ Successfully connected to {fastapi_url}", file=sys.stderr)
        print(f"📦 Discovered {len(fastapi_server.tools)} tools:\n", file=sys.stderr)

        for tool in fastapi_server.tools:
            print(f"  • {tool.name}", file=sys.stderr)
            print(f"    {tool.description.split(chr(10))[0]}", file=sys.stderr)
            if tool.inputSchema.get("properties"):
                params = list(tool.inputSchema["properties"].keys())
                if params:
                    print(f"    Parameters: {', '.join(params)}", file=sys.stderr)
            print("", file=sys.stderr)

        print("✅ gmcp is ready! Add it to ~/.claude/mcp_settings.json to use with Claude Code.", file=sys.stderr)
        print(f'\nExample configuration:', file=sys.stderr)
        print(f'  "gmcp-server": {{"command": "gmcp", "args": ["{fastapi_url}"]}}\n', file=sys.stderr)

    finally:
        await fastapi_server.cleanup()


def expand_env_var(value: Optional[str]) -> Optional[str]:
    """Expand environment variables in format $VAR or ${VAR}."""
    if not value:
        return value

    # If value starts with $ or env:, treat it as env var reference
    if value.startswith("$"):
        var_name = value[1:].strip("{}")
        return os.getenv(var_name)
    elif value.startswith("env:"):
        var_name = value[4:]
        return os.getenv(var_name)

    return value


def parse_auth_config(args: argparse.Namespace) -> Optional[AuthConfig]:
    """Parse authentication configuration from CLI arguments."""
    if not args.auth_type:
        return None

    auth_config = AuthConfig(auth_type=args.auth_type)

    if args.auth_type == "bearer":
        auth_config.token = expand_env_var(args.auth_token)
        if not auth_config.token:
            print("Error: --auth-token required for bearer authentication", file=sys.stderr)
            sys.exit(1)

    elif args.auth_type == "apikey":
        auth_config.api_key = expand_env_var(args.auth_token)
        auth_config.api_key_header = args.auth_header or "X-API-Key"
        if not auth_config.api_key:
            print("Error: --auth-token required for API key authentication", file=sys.stderr)
            sys.exit(1)

    elif args.auth_type == "basic":
        auth_config.username = expand_env_var(args.auth_username)
        auth_config.password = expand_env_var(args.auth_password)
        if not auth_config.username or not auth_config.password:
            print("Error: --auth-username and --auth-password required for basic authentication", file=sys.stderr)
            sys.exit(1)

    # Parse custom headers
    if args.auth_headers:
        for header in args.auth_headers:
            if ":" not in header:
                print(f"Error: Invalid header format '{header}'. Use 'Name: Value'", file=sys.stderr)
                sys.exit(1)
            name, value = header.split(":", 1)
            auth_config.custom_headers[name.strip()] = expand_env_var(value.strip())

    return auth_config


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Transform a FastAPI server into an MCP server",
        epilog="Note: gmcp runs as an MCP server using stdio. For testing, use --list-tools."
    )
    parser.add_argument(
        "url",
        help="URL of the FastAPI server (e.g., http://localhost:5000)"
    )
    parser.add_argument(
        "--list-tools",
        action="store_true",
        help="List available tools and exit (test mode)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force MCP server mode even in interactive terminal"
    )

    # Authentication arguments
    auth_group = parser.add_argument_group("authentication")
    auth_group.add_argument(
        "--auth-type",
        choices=["bearer", "apikey", "basic"],
        help="Authentication type"
    )
    auth_group.add_argument(
        "--auth-token",
        help="Token for bearer/apikey auth. Use $VAR or env:VAR for environment variables"
    )
    auth_group.add_argument(
        "--auth-header",
        default="X-API-Key",
        help="Header name for API key authentication (default: X-API-Key)"
    )
    auth_group.add_argument(
        "--auth-username",
        help="Username for basic authentication. Use $VAR or env:VAR for environment variables"
    )
    auth_group.add_argument(
        "--auth-password",
        help="Password for basic authentication. Use $VAR or env:VAR for environment variables"
    )
    auth_group.add_argument(
        "--auth-headers",
        action="append",
        help="Additional custom headers in format 'Name: Value'. Can be used multiple times"
    )

    args = parser.parse_args()

    # Parse authentication configuration
    auth_config = parse_auth_config(args)

    try:
        if args.list_tools:
            asyncio.run(list_tools_mode(args.url, auth_config))
        else:
            # Detect if running in an interactive terminal
            if not args.force and sys.stdin.isatty() and sys.stdout.isatty():
                print("⚠️  gmcp is an MCP server and shouldn't be run directly from the terminal.\n", file=sys.stderr)
                print("To test gmcp, use:", file=sys.stderr)
                print(f"  gmcp --list-tools {args.url}\n", file=sys.stderr)
                print("To use with Claude Code, add to ~/.claude/mcp_settings.json:", file=sys.stderr)
                print('  {', file=sys.stderr)
                print('    "mcpServers": {', file=sys.stderr)
                print('      "my-api": {', file=sys.stderr)
                print('        "command": "gmcp",', file=sys.stderr)
                print(f'        "args": ["{args.url}"]', file=sys.stderr)
                print('      }', file=sys.stderr)
                print('    }', file=sys.stderr)
                print('  }\n', file=sys.stderr)
                print("To force MCP server mode anyway, use: --force", file=sys.stderr)
                sys.exit(0)

            print(f"Starting gmcp MCP server...", file=sys.stderr)
            print(f"Connected to: {args.url}", file=sys.stderr)
            if auth_config and auth_config.auth_type:
                print(f"Authentication: {auth_config.auth_type}", file=sys.stderr)
            print(f"Use Ctrl+C to stop", file=sys.stderr)
            print(f"", file=sys.stderr)
            asyncio.run(run_server(args.url, auth_config))
    except KeyboardInterrupt:
        print("\nShutting down...", file=sys.stderr)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
