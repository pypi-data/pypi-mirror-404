#!/usr/bin/env python3
# VibeDNA MCP Server Runner
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""
Entry point for running VibeDNA MCP servers in Docker containers.

Reads configuration from environment variables and starts the appropriate MCP server.
"""

import asyncio
import logging
import os
import signal
import sys

# Configure logging
logging.basicConfig(
    level=os.environ.get("VIBEDNA_LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("vibedna.mcp.runner")


# MCP server type to class mapping
MCP_SERVER_REGISTRY = {
    "core": (
        "vibedna.agents.mcp_servers.core_server",
        "VibeDNACoreMCPServer",
    ),
    "fs": (
        "vibedna.agents.mcp_servers.fs_server",
        "VibeDNAFSMCPServer",
    ),
    "compute": (
        "vibedna.agents.mcp_servers.compute_server",
        "VibeDNAComputeMCPServer",
    ),
    "monitor": (
        "vibedna.agents.mcp_servers.monitor_server",
        "VibeDNAMonitorMCPServer",
    ),
    "search": (
        "vibedna.agents.mcp_servers.search_server",
        "VibeDNASearchMCPServer",
    ),
    "synth": (
        "vibedna.agents.mcp_servers.synth_server",
        "VibeDNASynthMCPServer",
    ),
}


class MCPHTTPServer:
    """HTTP wrapper for MCP servers providing JSON-RPC endpoint."""

    def __init__(self, mcp_server, port: int):
        self.mcp_server = mcp_server
        self.port = port
        self._server = None
        self._shutdown_event = asyncio.Event()

    async def handle_request(self, reader, writer):
        """Handle incoming HTTP request."""
        try:
            # Read request line
            request_line = await reader.readline()
            request_str = request_line.decode("utf-8").strip()

            if not request_str:
                writer.close()
                await writer.wait_closed()
                return

            method, path, _ = request_str.split(" ", 2)

            # Read headers
            headers = {}
            while True:
                header_line = await reader.readline()
                if header_line == b"\r\n" or header_line == b"\n":
                    break
                if b":" in header_line:
                    key, value = header_line.decode("utf-8").strip().split(":", 1)
                    headers[key.lower()] = value.strip()

            # Handle health check
            if path == "/health":
                response = self._json_response({"status": "healthy", "server": self.mcp_server.config.server_id})
            elif path == "/info":
                response = self._json_response({
                    "server_id": self.mcp_server.config.server_id,
                    "name": self.mcp_server.config.name,
                    "version": self.mcp_server.config.version,
                    "tools": [t.name for t in self.mcp_server._tools.values()],
                    "resources": [r.uri for r in self.mcp_server._resources.values()],
                })
            elif path == "/rpc" and method == "POST":
                # Read body
                content_length = int(headers.get("content-length", 0))
                body = await reader.read(content_length)

                import json

                try:
                    message = json.loads(body.decode("utf-8"))
                    result = await self.mcp_server.handle_message(message)
                    response = self._json_response(result)
                except Exception as e:
                    response = self._json_response({
                        "jsonrpc": "2.0",
                        "error": {"code": -32603, "message": str(e)},
                        "id": None,
                    })
            elif path == "/tools":
                tools = []
                for tool in self.mcp_server._tools.values():
                    tools.append({
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.input_schema,
                    })
                response = self._json_response({"tools": tools})
            elif path == "/resources":
                resources = []
                for resource in self.mcp_server._resources.values():
                    resources.append({
                        "uri": resource.uri,
                        "name": resource.name,
                        "description": resource.description,
                        "mime_type": resource.mime_type,
                    })
                response = self._json_response({"resources": resources})
            else:
                response = self._json_response({"error": "Not found"}, status=404)

            writer.write(response.encode("utf-8"))
            await writer.drain()

        except Exception as e:
            logger.error(f"Request handling error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    def _json_response(self, data: dict, status: int = 200) -> str:
        """Create JSON HTTP response."""
        import json
        body = json.dumps(data)
        status_text = "OK" if status == 200 else "Error"
        return (
            f"HTTP/1.1 {status} {status_text}\r\n"
            f"Content-Type: application/json\r\n"
            f"Content-Length: {len(body)}\r\n"
            f"\r\n"
            f"{body}"
        )

    async def start(self):
        """Start the MCP HTTP server."""
        self._server = await asyncio.start_server(
            self.handle_request,
            "0.0.0.0",
            self.port,
        )
        logger.info(f"MCP HTTP server started on port {self.port}")

        async with self._server:
            await self._shutdown_event.wait()

    async def stop(self):
        """Stop the MCP HTTP server."""
        self._shutdown_event.set()
        if self._server:
            self._server.close()
            await self._server.wait_closed()


def get_mcp_server(server_type: str):
    """Get MCP server instance by type."""
    if server_type not in MCP_SERVER_REGISTRY:
        raise ValueError(f"Unknown MCP server type: {server_type}")

    module_path, class_name = MCP_SERVER_REGISTRY[server_type]

    # Import module dynamically
    import importlib
    module = importlib.import_module(module_path)
    server_class = getattr(module, class_name)

    return server_class()


async def main():
    """Main entry point."""
    server_type = os.environ.get("MCP_SERVER_TYPE", "core")
    server_port = int(os.environ.get("MCP_SERVER_PORT", "8100"))

    logger.info(f"Starting VibeDNA MCP Server: {server_type}")
    logger.info(f"Port: {server_port}")

    try:
        mcp_server = get_mcp_server(server_type)
        logger.info(f"MCP Server initialized: {mcp_server.config.server_id}")

        http_server = MCPHTTPServer(mcp_server, server_port)

        # Setup signal handlers
        loop = asyncio.get_event_loop()

        def signal_handler():
            logger.info("Shutdown signal received")
            asyncio.create_task(http_server.stop())

        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, signal_handler)

        await http_server.start()

    except Exception as e:
        logger.error(f"MCP server startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
