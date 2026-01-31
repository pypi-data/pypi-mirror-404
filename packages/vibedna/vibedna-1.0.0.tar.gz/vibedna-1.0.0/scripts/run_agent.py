#!/usr/bin/env python3
# VibeDNA Agent Runner
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""
Entry point for running VibeDNA agents in Docker containers.

Reads configuration from environment variables and starts the appropriate agent.
"""

import asyncio
import logging
import os
import signal
import sys
from typing import Optional

# Configure logging
logging.basicConfig(
    level=os.environ.get("VIBEDNA_LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("vibedna.agent.runner")


# Agent type to class mapping
AGENT_REGISTRY = {
    # Orchestration Tier
    "master-orchestrator": (
        "vibedna.agents.orchestration.master_orchestrator",
        "MasterOrchestrator",
    ),
    "workflow-orchestrator": (
        "vibedna.agents.orchestration.workflow_orchestrator",
        "WorkflowOrchestrator",
    ),
    "resource-orchestrator": (
        "vibedna.agents.orchestration.resource_orchestrator",
        "ResourceOrchestrator",
    ),
    # Specialist Tier
    "encoder": (
        "vibedna.agents.specialist.encoder_agent",
        "EncoderAgent",
    ),
    "decoder": (
        "vibedna.agents.specialist.decoder_agent",
        "DecoderAgent",
    ),
    "error-correction": (
        "vibedna.agents.specialist.error_correction_agent",
        "ErrorCorrectionAgent",
    ),
    "compute": (
        "vibedna.agents.specialist.compute_agent",
        "ComputeAgent",
    ),
    "filesystem": (
        "vibedna.agents.specialist.filesystem_agent",
        "FileSystemAgent",
    ),
    "validation": (
        "vibedna.agents.specialist.validation_agent",
        "ValidationAgent",
    ),
    "visualization": (
        "vibedna.agents.specialist.visualization_agent",
        "VisualizationAgent",
    ),
    "synthesis": (
        "vibedna.agents.specialist.synthesis_agent",
        "SynthesisAgent",
    ),
    # Support Tier
    "index": (
        "vibedna.agents.support.index_agent",
        "IndexAgent",
    ),
    "metrics": (
        "vibedna.agents.support.metrics_agent",
        "MetricsAgent",
    ),
    "logging": (
        "vibedna.agents.support.logging_agent",
        "LoggingAgent",
    ),
    "docs": (
        "vibedna.agents.support.docs_agent",
        "DocsAgent",
    ),
    "security": (
        "vibedna.agents.support.security_agent",
        "SecurityAgent",
    ),
}


class AgentServer:
    """HTTP server wrapper for agents."""

    def __init__(self, agent, port: int):
        self.agent = agent
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
                response = self._json_response({"status": "healthy", "agent": self.agent.config.agent_id})
            elif path == "/info":
                response = self._json_response({
                    "agent_id": self.agent.config.agent_id,
                    "version": self.agent.config.version,
                    "tier": self.agent.config.tier.value,
                    "role": self.agent.config.role,
                })
            elif path == "/task" and method == "POST":
                # Read body
                content_length = int(headers.get("content-length", 0))
                body = await reader.read(content_length)

                import json
                from vibedna.agents.base.message import TaskRequest

                try:
                    task_data = json.loads(body.decode("utf-8"))
                    request = TaskRequest(
                        request_id=task_data.get("request_id", ""),
                        task_type=task_data.get("task_type", ""),
                        parameters=task_data.get("parameters", {}),
                        priority=task_data.get("priority", 2),
                    )
                    result = await self.agent.handle_task(request)
                    response = self._json_response(result.to_dict())
                except Exception as e:
                    response = self._json_response({"error": str(e)}, status=500)
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
        """Start the agent server."""
        self._server = await asyncio.start_server(
            self.handle_request,
            "0.0.0.0",
            self.port,
        )
        logger.info(f"Agent server started on port {self.port}")

        async with self._server:
            await self._shutdown_event.wait()

    async def stop(self):
        """Stop the agent server."""
        self._shutdown_event.set()
        if self._server:
            self._server.close()
            await self._server.wait_closed()


def get_agent(agent_type: str):
    """Get agent instance by type."""
    if agent_type not in AGENT_REGISTRY:
        raise ValueError(f"Unknown agent type: {agent_type}")

    module_path, class_name = AGENT_REGISTRY[agent_type]

    # Import module dynamically
    import importlib
    module = importlib.import_module(module_path)
    agent_class = getattr(module, class_name)

    return agent_class()


async def main():
    """Main entry point."""
    agent_type = os.environ.get("AGENT_TYPE", "encoder")
    agent_port = int(os.environ.get("AGENT_PORT", "8300"))

    logger.info(f"Starting VibeDNA Agent: {agent_type}")
    logger.info(f"Port: {agent_port}")

    try:
        agent = get_agent(agent_type)
        logger.info(f"Agent initialized: {agent.config.agent_id}")

        server = AgentServer(agent, agent_port)

        # Setup signal handlers
        loop = asyncio.get_event_loop()

        def signal_handler():
            logger.info("Shutdown signal received")
            asyncio.create_task(server.stop())

        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, signal_handler)

        await server.start()

    except Exception as e:
        logger.error(f"Agent startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
