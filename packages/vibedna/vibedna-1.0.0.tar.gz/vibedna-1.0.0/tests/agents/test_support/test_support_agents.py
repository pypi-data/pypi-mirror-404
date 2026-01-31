# VibeDNA Support Agent Tests
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""Tests for support tier agents."""

import pytest
from vibedna.agents.support.index_agent import IndexAgent
from vibedna.agents.support.metrics_agent import MetricsAgent
from vibedna.agents.support.logging_agent import LoggingAgent
from vibedna.agents.support.docs_agent import DocsAgent
from vibedna.agents.support.security_agent import SecurityAgent
from vibedna.agents.base.message import TaskRequest
from vibedna.agents.base.agent_base import AgentTier


class TestIndexAgent:
    """Tests for IndexAgent."""

    def test_creation(self):
        """Test creating index agent."""
        agent = IndexAgent()

        assert agent.config.agent_id == "vibedna-index-agent"
        assert agent.config.tier == AgentTier.SUPPORT

    def test_system_prompt(self):
        """Test system prompt."""
        agent = IndexAgent()
        prompt = agent.get_system_prompt()

        assert "Index Agent" in prompt

    @pytest.mark.asyncio
    async def test_index_sequence(self):
        """Test indexing a sequence."""
        agent = IndexAgent()

        request = TaskRequest(
            request_id="test-001",
            task_type="index",
            parameters={
                "action": "index",
                "sequence_id": "seq-001",
                "sequence": "ATCGATCG",
                "metadata": {"name": "test"},
            },
        )

        response = await agent.handle_task(request)
        assert response.success is True

    @pytest.mark.asyncio
    async def test_search_index(self):
        """Test searching the index."""
        agent = IndexAgent()

        request = TaskRequest(
            request_id="test-002",
            task_type="search",
            parameters={
                "action": "search",
                "query": "test",
            },
        )

        response = await agent.handle_task(request)
        assert response.success is True
        assert "results" in response.result


class TestMetricsAgent:
    """Tests for MetricsAgent."""

    def test_creation(self):
        """Test creating metrics agent."""
        agent = MetricsAgent()

        assert agent.config.agent_id == "vibedna-metrics-agent"
        assert agent.config.tier == AgentTier.SUPPORT

    @pytest.mark.asyncio
    async def test_record_metric(self):
        """Test recording a metric."""
        agent = MetricsAgent()

        request = TaskRequest(
            request_id="test-001",
            task_type="record",
            parameters={
                "action": "record",
                "name": "encoding_duration_ms",
                "value": 150.5,
                "tags": {"agent": "encoder"},
            },
        )

        response = await agent.handle_task(request)
        assert response.success is True

    @pytest.mark.asyncio
    async def test_get_metrics(self):
        """Test getting metrics."""
        agent = MetricsAgent()

        # First record some metrics
        await agent.handle_task(TaskRequest(
            request_id="record-1",
            task_type="record",
            parameters={
                "action": "record",
                "name": "test_metric",
                "value": 100,
            },
        ))

        # Then query
        request = TaskRequest(
            request_id="test-002",
            task_type="query",
            parameters={
                "action": "query",
                "name": "test_metric",
            },
        )

        response = await agent.handle_task(request)
        assert response.success is True


class TestLoggingAgent:
    """Tests for LoggingAgent."""

    def test_creation(self):
        """Test creating logging agent."""
        agent = LoggingAgent()

        assert agent.config.agent_id == "vibedna-logging-agent"
        assert agent.config.tier == AgentTier.SUPPORT

    @pytest.mark.asyncio
    async def test_log_entry(self):
        """Test logging an entry."""
        agent = LoggingAgent()

        request = TaskRequest(
            request_id="test-001",
            task_type="log",
            parameters={
                "action": "log",
                "level": "info",
                "message": "Test log message",
                "source": "test",
            },
        )

        response = await agent.handle_task(request)
        assert response.success is True

    @pytest.mark.asyncio
    async def test_query_logs(self):
        """Test querying logs."""
        agent = LoggingAgent()

        # First add a log
        await agent.handle_task(TaskRequest(
            request_id="log-1",
            task_type="log",
            parameters={
                "action": "log",
                "level": "info",
                "message": "Test message",
                "source": "test",
            },
        ))

        # Then query
        request = TaskRequest(
            request_id="test-002",
            task_type="query",
            parameters={
                "action": "query",
                "level": "info",
                "limit": 10,
            },
        )

        response = await agent.handle_task(request)
        assert response.success is True
        assert "logs" in response.result


class TestDocsAgent:
    """Tests for DocsAgent."""

    def test_creation(self):
        """Test creating docs agent."""
        agent = DocsAgent()

        assert agent.config.agent_id == "vibedna-docs-agent"
        assert agent.config.tier == AgentTier.SUPPORT

    @pytest.mark.asyncio
    async def test_generate_docs(self):
        """Test generating documentation."""
        agent = DocsAgent()

        request = TaskRequest(
            request_id="test-001",
            task_type="generate",
            parameters={
                "action": "generate",
                "doc_type": "api",
                "target": "encoder",
            },
        )

        response = await agent.handle_task(request)
        assert response.request_id == "test-001"

    @pytest.mark.asyncio
    async def test_search_docs(self):
        """Test searching documentation."""
        agent = DocsAgent()

        request = TaskRequest(
            request_id="test-002",
            task_type="search",
            parameters={
                "action": "search",
                "query": "encoding",
            },
        )

        response = await agent.handle_task(request)
        assert response.success is True


class TestSecurityAgent:
    """Tests for SecurityAgent."""

    def test_creation(self):
        """Test creating security agent."""
        agent = SecurityAgent()

        assert agent.config.agent_id == "vibedna-security-agent"
        assert agent.config.tier == AgentTier.SUPPORT

    @pytest.mark.asyncio
    async def test_check_access(self):
        """Test checking access."""
        agent = SecurityAgent()

        request = TaskRequest(
            request_id="test-001",
            task_type="check_access",
            parameters={
                "action": "check_access",
                "user_id": "user-001",
                "resource": "sequences/*",
                "requested_action": "read",
            },
        )

        response = await agent.handle_task(request)
        assert response.success is True
        assert "allowed" in response.result

    @pytest.mark.asyncio
    async def test_create_policy(self):
        """Test creating security policy."""
        agent = SecurityAgent()

        request = TaskRequest(
            request_id="test-002",
            task_type="create_policy",
            parameters={
                "action": "create_policy",
                "policy_id": "test-policy",
                "name": "Test Policy",
                "permissions": [
                    {"resource": "sequences/*", "actions": ["read"]},
                ],
            },
        )

        response = await agent.handle_task(request)
        assert response.success is True

    @pytest.mark.asyncio
    async def test_validate_request(self):
        """Test validating request for security issues."""
        agent = SecurityAgent()

        request = TaskRequest(
            request_id="test-003",
            task_type="validate_request",
            parameters={
                "action": "validate_request",
                "data": "normal data without issues",
            },
        )

        response = await agent.handle_task(request)
        assert response.success is True
        assert response.result["is_safe"] is True

    @pytest.mark.asyncio
    async def test_validate_request_with_injection(self):
        """Test detecting injection attempt."""
        agent = SecurityAgent()

        request = TaskRequest(
            request_id="test-004",
            task_type="validate_request",
            parameters={
                "action": "validate_request",
                "data": "<script>alert('xss')</script>",
            },
        )

        response = await agent.handle_task(request)
        assert response.success is True
        assert response.result["is_safe"] is False
        assert len(response.result["issues"]) > 0

    @pytest.mark.asyncio
    async def test_get_audit_log(self):
        """Test getting audit log."""
        agent = SecurityAgent()

        # First make an access check to generate audit entry
        await agent.handle_task(TaskRequest(
            request_id="access-check",
            task_type="check_access",
            parameters={
                "action": "check_access",
                "user_id": "test-user",
                "resource": "test",
                "requested_action": "read",
            },
        ))

        # Then get audit log
        request = TaskRequest(
            request_id="test-005",
            task_type="get_audit_log",
            parameters={
                "action": "get_audit_log",
                "limit": 10,
            },
        )

        response = await agent.handle_task(request)
        assert response.success is True
        assert "audit_log" in response.result


# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
