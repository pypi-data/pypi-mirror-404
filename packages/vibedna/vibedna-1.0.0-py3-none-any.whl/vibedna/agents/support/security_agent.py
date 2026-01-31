# VibeDNA Security Agent
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""
Security Agent - Access control and security validation.

Handles:
- Access control and authorization
- Request validation
- Security auditing
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from vibedna.agents.base.agent_base import (
    BaseAgent,
    AgentConfig,
    AgentCapability,
    AgentTier,
)
from vibedna.agents.base.message import (
    TaskRequest,
    TaskResponse,
)


@dataclass
class Permission:
    """A permission grant."""
    resource: str
    actions: Set[str]
    conditions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityPolicy:
    """Security policy for a user or role."""
    policy_id: str
    name: str
    permissions: List[Permission] = field(default_factory=list)


@dataclass
class AuditEntry:
    """Security audit log entry."""
    timestamp: datetime
    user_id: str
    action: str
    resource: str
    allowed: bool
    reason: str = ""


class SecurityAgent(BaseAgent):
    """
    Security Agent for access control.

    Manages access control policies, validates requests,
    and maintains security audit logs.
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize the Security Agent."""
        if config is None:
            config = AgentConfig(
                agent_id="vibedna-security-agent",
                version="1.0.0",
                tier=AgentTier.SUPPORT,
                role="Access Control and Security",
                description="Manages access control and security validation",
                capabilities=[
                    AgentCapability(
                        name="access_control",
                        description="Control access to resources",
                    ),
                    AgentCapability(
                        name="request_validation",
                        description="Validate security of requests",
                    ),
                    AgentCapability(
                        name="audit_logging",
                        description="Log security events",
                    ),
                ],
                tools=[
                    "policy_manager",
                    "access_validator",
                    "audit_logger",
                ],
                mcp_connections=["vibedna-monitor"],
            )

        super().__init__(config)
        self._policies: Dict[str, SecurityPolicy] = {}
        self._user_policies: Dict[str, str] = {}  # user_id -> policy_id
        self._audit_log: List[AuditEntry] = []

        # Create default policy
        self._create_default_policy()

    def _create_default_policy(self) -> None:
        """Create default permissive policy."""
        default = SecurityPolicy(
            policy_id="default",
            name="Default Policy",
            permissions=[
                Permission(
                    resource="*",
                    actions={"read", "write", "execute"},
                ),
            ],
        )
        self._policies["default"] = default

    def get_system_prompt(self) -> str:
        """Get the Security Agent's system prompt."""
        return """You are the VibeDNA Security Agent, managing access control.

## Capabilities

1. Access Control - Manage permissions and policies
2. Request Validation - Validate request authorization
3. Audit Logging - Log security events

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC."""

    async def handle_task(self, request: TaskRequest) -> TaskResponse:
        """Handle a security task."""
        action = request.parameters.get("action", "check_access")

        if action == "check_access":
            return await self._check_access(request)
        elif action == "create_policy":
            return await self._create_policy(request)
        elif action == "assign_policy":
            return await self._assign_policy(request)
        elif action == "get_audit_log":
            return await self._get_audit_log(request)
        elif action == "validate_request":
            return await self._validate_request(request)
        else:
            return TaskResponse.failure(request.request_id, f"Unknown action: {action}")

    async def _check_access(self, request: TaskRequest) -> TaskResponse:
        """Check if access is allowed."""
        try:
            user_id = request.parameters.get("user_id", "anonymous")
            resource = request.parameters.get("resource", "*")
            action = request.parameters.get("requested_action", "read")

            # Get user's policy
            policy_id = self._user_policies.get(user_id, "default")
            policy = self._policies.get(policy_id)

            if not policy:
                allowed = False
                reason = "No policy found"
            else:
                allowed = False
                reason = "No matching permission"

                for perm in policy.permissions:
                    if self._matches_resource(perm.resource, resource):
                        if action in perm.actions or "*" in perm.actions:
                            allowed = True
                            reason = f"Granted by policy {policy.name}"
                            break

            # Audit log
            self._audit_log.append(AuditEntry(
                timestamp=datetime.utcnow(),
                user_id=user_id,
                action=action,
                resource=resource,
                allowed=allowed,
                reason=reason,
            ))

            return TaskResponse.success(
                request.request_id,
                {
                    "allowed": allowed,
                    "reason": reason,
                    "user_id": user_id,
                    "resource": resource,
                    "action": action,
                },
            )

        except Exception as e:
            return TaskResponse.failure(request.request_id, str(e))

    async def _create_policy(self, request: TaskRequest) -> TaskResponse:
        """Create a new security policy."""
        try:
            policy_id = request.parameters.get("policy_id")
            name = request.parameters.get("name", "Unnamed Policy")
            permissions = request.parameters.get("permissions", [])

            if not policy_id:
                return TaskResponse.failure(request.request_id, "policy_id required")

            policy = SecurityPolicy(
                policy_id=policy_id,
                name=name,
                permissions=[
                    Permission(
                        resource=p.get("resource", "*"),
                        actions=set(p.get("actions", ["read"])),
                    )
                    for p in permissions
                ],
            )

            self._policies[policy_id] = policy

            return TaskResponse.success(
                request.request_id,
                {"created": True, "policy_id": policy_id},
            )

        except Exception as e:
            return TaskResponse.failure(request.request_id, str(e))

    async def _assign_policy(self, request: TaskRequest) -> TaskResponse:
        """Assign a policy to a user."""
        try:
            user_id = request.parameters.get("user_id")
            policy_id = request.parameters.get("policy_id")

            if not user_id or not policy_id:
                return TaskResponse.failure(
                    request.request_id,
                    "user_id and policy_id required",
                )

            if policy_id not in self._policies:
                return TaskResponse.failure(
                    request.request_id,
                    f"Policy not found: {policy_id}",
                )

            self._user_policies[user_id] = policy_id

            return TaskResponse.success(
                request.request_id,
                {"assigned": True, "user_id": user_id, "policy_id": policy_id},
            )

        except Exception as e:
            return TaskResponse.failure(request.request_id, str(e))

    async def _get_audit_log(self, request: TaskRequest) -> TaskResponse:
        """Get security audit log."""
        try:
            limit = request.parameters.get("limit", 100)
            user_id = request.parameters.get("user_id")

            entries = []
            for entry in reversed(self._audit_log):
                if user_id and entry.user_id != user_id:
                    continue

                entries.append({
                    "timestamp": entry.timestamp.isoformat(),
                    "user_id": entry.user_id,
                    "action": entry.action,
                    "resource": entry.resource,
                    "allowed": entry.allowed,
                    "reason": entry.reason,
                })

                if len(entries) >= limit:
                    break

            return TaskResponse.success(
                request.request_id,
                {"audit_log": entries, "count": len(entries)},
            )

        except Exception as e:
            return TaskResponse.failure(request.request_id, str(e))

    async def _validate_request(self, request: TaskRequest) -> TaskResponse:
        """Validate a request for security issues."""
        try:
            data = request.parameters.get("data", "")
            check_injection = request.parameters.get("check_injection", True)

            issues = []

            # Check for potential injection patterns
            if check_injection and isinstance(data, str):
                dangerous_patterns = ["<script", "javascript:", "eval(", "exec("]
                for pattern in dangerous_patterns:
                    if pattern.lower() in data.lower():
                        issues.append({
                            "type": "injection",
                            "severity": "high",
                            "message": f"Potential injection pattern: {pattern}",
                        })

            is_safe = len(issues) == 0

            return TaskResponse.success(
                request.request_id,
                {
                    "is_safe": is_safe,
                    "issues": issues,
                },
            )

        except Exception as e:
            return TaskResponse.failure(request.request_id, str(e))

    def _matches_resource(self, pattern: str, resource: str) -> bool:
        """Check if a resource matches a pattern."""
        if pattern == "*":
            return True
        if pattern == resource:
            return True
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            return resource.startswith(prefix)
        return False
