# VibeDNA MCP Server Tests
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""Tests for MCP server implementations."""

import pytest
from vibedna.agents.mcp_servers.base_server import (
    MCPServerConfig,
    MCPTool,
    MCPToolParameter,
    MCPResource,
)
from vibedna.agents.mcp_servers.core_server import VibeDNACoreMCPServer
from vibedna.agents.mcp_servers.fs_server import VibeDNAFSMCPServer
from vibedna.agents.mcp_servers.compute_server import VibeDNAComputeMCPServer
from vibedna.agents.mcp_servers.monitor_server import VibeDNAMonitorMCPServer
from vibedna.agents.mcp_servers.search_server import VibeDNASearchMCPServer
from vibedna.agents.mcp_servers.synth_server import VibeDNASynthMCPServer


class TestMCPServerConfig:
    """Tests for MCPServerConfig."""

    def test_config_creation(self):
        """Test creating MCP server config."""
        config = MCPServerConfig(
            name="Test Server",
            version="1.0.0",
            description="A test server",
        )

        assert config.name == "Test Server"
        assert config.version == "1.0.0"


class TestMCPTool:
    """Tests for MCPTool."""

    def test_tool_creation(self):
        """Test creating MCP tool."""
        tool = MCPTool(
            name="encode_binary",
            description="Encode binary data",
            parameters=[
                MCPToolParameter(
                    name="data",
                    param_type="string",
                    description="Data to encode",
                ),
            ],
        )

        assert tool.name == "encode_binary"
        assert tool.description == "Encode binary data"
        assert len(tool.parameters) == 1

    def test_tool_schema(self):
        """Test tool schema generation."""
        tool = MCPTool(
            name="test_tool",
            description="Test tool",
            parameters=[
                MCPToolParameter(
                    name="input",
                    param_type="string",
                    description="Input data",
                    required=True,
                ),
            ],
        )
        schema = tool.to_schema()

        assert schema["name"] == "test_tool"
        assert "inputSchema" in schema


class TestMCPResource:
    """Tests for MCPResource."""

    def test_resource_creation(self):
        """Test creating MCP resource."""
        resource = MCPResource(
            uri="vibedna://core/status",
            name="Core Status",
            description="System status",
            mime_type="application/json",
        )

        assert resource.uri == "vibedna://core/status"
        assert resource.name == "Core Status"
        assert resource.mime_type == "application/json"


class TestVibeDNAMCPServers:
    """Tests for VibeDNA MCP Servers."""

    def test_core_server_instantiation(self):
        """Test creating core MCP server."""
        server = VibeDNACoreMCPServer()
        assert server.config is not None
        assert server.config.name is not None

    def test_fs_server_instantiation(self):
        """Test creating FS MCP server."""
        server = VibeDNAFSMCPServer()
        assert server.config is not None

    def test_compute_server_instantiation(self):
        """Test creating Compute MCP server."""
        server = VibeDNAComputeMCPServer()
        assert server.config is not None

    def test_monitor_server_instantiation(self):
        """Test creating Monitor MCP server."""
        server = VibeDNAMonitorMCPServer()
        assert server.config is not None

    def test_search_server_instantiation(self):
        """Test creating Search MCP server."""
        server = VibeDNASearchMCPServer()
        assert server.config is not None

    def test_synth_server_instantiation(self):
        """Test creating Synth MCP server."""
        server = VibeDNASynthMCPServer()
        assert server.config is not None


# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
