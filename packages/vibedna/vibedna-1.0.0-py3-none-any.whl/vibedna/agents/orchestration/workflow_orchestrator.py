# VibeDNA Workflow Orchestrator
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""
Workflow Orchestrator - Tactical workflow manager for the VibeDNA system.

The Workflow Orchestrator is responsible for:
- Workflow graph construction
- Parallel task scheduling
- State management and checkpointing
- Dependency resolution
- Rollback and recovery
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set
import asyncio
import uuid
import yaml

from vibedna.agents.base.agent_base import (
    BaseAgent,
    AgentConfig,
    AgentCapability,
    AgentTier,
)
from vibedna.agents.base.message import (
    TaskRequest,
    TaskResponse,
    TaskStatus,
    OperationType,
    WorkflowStep,
)
from vibedna.agents.base.context import WorkflowContext, WorkflowState


@dataclass
class WorkflowDefinition:
    """Definition of a workflow."""
    name: str
    version: str = "1.0"
    triggers: List[Dict[str, Any]] = field(default_factory=list)
    variables: Dict[str, str] = field(default_factory=dict)
    steps: List[Dict[str, Any]] = field(default_factory=list)
    error_handlers: List[Dict[str, Any]] = field(default_factory=list)
    outputs: Dict[str, str] = field(default_factory=dict)


@dataclass
class ExecutionState:
    """State of a workflow execution."""
    execution_id: str
    workflow_name: str
    status: str = "running"
    current_step: Optional[str] = None
    completed_steps: List[str] = field(default_factory=list)
    failed_steps: List[str] = field(default_factory=list)
    step_outputs: Dict[str, Any] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class WorkflowOrchestrator(BaseAgent):
    """
    Workflow Orchestrator for the VibeDNA Agent System.

    Manages complex multi-step workflows, handles parallel execution,
    maintains state, and coordinates handoffs between agents.
    """

    # Built-in workflow definitions
    BUILTIN_WORKFLOWS = {
        "encode_simple": WorkflowDefinition(
            name="encode_simple",
            version="1.0",
            steps=[
                {"id": "validate", "agent": "validation-agent", "action": "validate_binary"},
                {"id": "encode", "agent": "encoder-agent", "action": "encode"},
            ],
            outputs={"sequence": "${steps.encode.output.sequence}"},
        ),
        "encode_with_ec": WorkflowDefinition(
            name="encode_with_ec",
            version="1.0",
            steps=[
                {"id": "validate", "agent": "validation-agent", "action": "validate_binary"},
                {"id": "encode", "agent": "encoder-agent", "action": "encode"},
                {"id": "add_ec", "agent": "error-correction-agent", "action": "apply_reed_solomon"},
                {"id": "validate_output", "agent": "validation-agent", "action": "validate_sequence"},
            ],
            outputs={
                "sequence": "${steps.add_ec.output.sequence}",
                "checksum": "${steps.add_ec.output.checksum}",
            },
        ),
        "decode_simple": WorkflowDefinition(
            name="decode_simple",
            version="1.0",
            steps=[
                {"id": "validate", "agent": "validation-agent", "action": "validate_sequence"},
                {"id": "decode", "agent": "decoder-agent", "action": "decode"},
            ],
            outputs={"data": "${steps.decode.output.data}"},
        ),
        "decode_with_repair": WorkflowDefinition(
            name="decode_with_repair",
            version="1.0",
            steps=[
                {"id": "validate", "agent": "validation-agent", "action": "validate_sequence"},
                {"id": "repair", "agent": "error-correction-agent", "action": "decode_reed_solomon"},
                {"id": "decode", "agent": "decoder-agent", "action": "decode"},
                {"id": "verify", "agent": "validation-agent", "action": "verify_checksum"},
            ],
            error_handlers=[
                {"id": "repair_failed", "action": "continue_with_warning"},
            ],
            outputs={
                "data": "${steps.decode.output.data}",
                "errors_corrected": "${steps.repair.output.errors_corrected}",
            },
        ),
        "store_and_index": WorkflowDefinition(
            name="store_and_index",
            version="1.0",
            steps=[
                {"id": "encode", "agent": "encoder-agent", "action": "encode", "conditional": "input.needs_encoding"},
                {"id": "store", "agent": "filesystem-agent", "action": "create_file"},
                {"id": "index", "agent": "index-agent", "action": "add_to_catalog", "parallel_with": "store"},
            ],
            outputs={
                "file_id": "${steps.store.output.file_id}",
                "path": "${steps.store.output.path}",
            },
        ),
    }

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize the Workflow Orchestrator."""
        if config is None:
            config = AgentConfig(
                agent_id="vibedna-workflow-orchestrator",
                version="1.0.0",
                tier=AgentTier.ORCHESTRATION,
                role="Tactical Workflow Manager",
                description="Manages complex multi-step workflows",
                capabilities=[
                    AgentCapability(
                        name="workflow_execution",
                        description="Execute multi-step workflows",
                    ),
                    AgentCapability(
                        name="parallel_scheduling",
                        description="Schedule and execute parallel tasks",
                    ),
                    AgentCapability(
                        name="state_management",
                        description="Manage workflow state and checkpoints",
                    ),
                    AgentCapability(
                        name="dependency_resolution",
                        description="Resolve step dependencies",
                    ),
                ],
                tools=[
                    "workflow_parser",
                    "step_executor",
                    "state_manager",
                    "checkpoint_handler",
                    "parallel_scheduler",
                ],
                mcp_connections=[
                    "vibedna-core",
                    "vibedna-monitor",
                ],
            )

        super().__init__(config)

        # Workflow registry
        self._workflows: Dict[str, WorkflowDefinition] = dict(self.BUILTIN_WORKFLOWS)

        # Active executions
        self._executions: Dict[str, ExecutionState] = {}

        # Agent registry (populated by Master Orchestrator)
        self._agents: Dict[str, BaseAgent] = {}

        # State store for checkpoints
        self._checkpoints: Dict[str, List[Dict[str, Any]]] = {}

    def get_system_prompt(self) -> str:
        """Get the Workflow Orchestrator's system prompt."""
        return """You are the VibeDNA Workflow Orchestrator, responsible for tactical execution
of multi-step DNA processing workflows.

## Workflow Definition Language

Define workflows using YAML DSL:

```yaml
workflow:
  name: encode_and_store
  version: 1.0

  triggers:
    - event: encode_request
      condition: "input.store_after == true"

  variables:
    input_data: "${trigger.data}"
    encoding_scheme: "${trigger.scheme || 'quaternary'}"

  steps:
    - id: validate_input
      agent: validation-agent
      action: validate_binary
      input:
        data: "${variables.input_data}"
      on_success: encode_data
      on_failure: abort_with_error

    - id: encode_data
      agent: encoder-agent
      action: encode
      input:
        data: "${steps.validate_input.output.validated_data}"
        scheme: "${variables.encoding_scheme}"
      on_success: add_error_correction
      on_failure: retry_with_fallback

  outputs:
    sequence_id: "${steps.store_sequence.output.file_id}"
```

## Execution Protocol

1. Initialize execution state
2. Resolve variable references
3. Execute steps in dependency order
4. Handle parallel groups concurrently
5. Checkpoint after each step
6. Handle errors with defined handlers
7. Return final outputs

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC."""

    async def handle_task(self, request: TaskRequest) -> TaskResponse:
        """Handle a workflow execution request."""
        self.logger.info(f"Handling workflow task: {request.request_id}")

        action = request.parameters.get("action", "execute")

        if action == "execute":
            return await self._execute_workflow(request)
        elif action == "register":
            return await self._register_workflow(request)
        elif action == "get_status":
            return await self._get_execution_status(request)
        elif action == "cancel":
            return await self._cancel_execution(request)
        elif action == "list":
            return await self._list_workflows(request)
        else:
            return TaskResponse.failure(
                request.request_id,
                f"Unknown action: {action}",
            )

    async def _execute_workflow(self, request: TaskRequest) -> TaskResponse:
        """Execute a workflow."""
        workflow_name = request.parameters.get("workflow_name")
        plan = request.parameters.get("plan")
        input_data = request.parameters.get("input", {})

        # Get workflow definition
        if workflow_name and workflow_name in self._workflows:
            workflow = self._workflows[workflow_name]
        elif plan:
            # Create workflow from plan
            workflow = WorkflowDefinition(
                name=f"plan_{request.request_id[:8]}",
                steps=plan.get("steps", []),
                outputs=plan.get("outputs", {}),
            )
        else:
            return TaskResponse.failure(
                request.request_id,
                "No workflow_name or plan provided",
            )

        # Create execution state
        execution = ExecutionState(
            execution_id=request.request_id,
            workflow_name=workflow.name,
            variables=self._resolve_initial_variables(workflow, input_data),
        )
        self._executions[execution.execution_id] = execution

        try:
            # Build dependency graph
            step_order = self._resolve_dependencies(workflow.steps)

            # Execute steps
            for step_group in step_order:
                if len(step_group) == 1:
                    # Sequential execution
                    step = self._get_step(workflow.steps, step_group[0])
                    await self._execute_step(execution, step, input_data)
                else:
                    # Parallel execution
                    await self._execute_parallel_steps(execution, workflow.steps, step_group, input_data)

                # Checkpoint after each group
                self._create_checkpoint(execution)

            # Resolve outputs
            outputs = self._resolve_outputs(workflow, execution)

            execution.status = "completed"
            execution.completed_at = datetime.utcnow()

            return TaskResponse.success(
                request.request_id,
                outputs,
                workflow_trace=self._get_trace(execution),
                metadata={
                    "workflow_name": workflow.name,
                    "steps_completed": len(execution.completed_steps),
                },
            )

        except Exception as e:
            execution.status = "failed"
            execution.error = str(e)

            # Try error handlers
            handled = await self._handle_workflow_error(execution, workflow, e)
            if handled:
                return TaskResponse.partial(
                    request.request_id,
                    self._resolve_outputs(workflow, execution),
                    str(e),
                    workflow_trace=self._get_trace(execution),
                )

            return TaskResponse.failure(
                request.request_id,
                str(e),
                workflow_trace=self._get_trace(execution),
            )

    async def _execute_step(
        self,
        execution: ExecutionState,
        step: Dict[str, Any],
        input_data: Dict[str, Any],
    ) -> None:
        """Execute a single workflow step."""
        step_id = step["id"]
        agent_id = step.get("agent")
        action = step.get("action")

        self.logger.info(f"Executing step: {step_id} with agent {agent_id}")
        execution.current_step = step_id

        # Check conditional
        condition = step.get("conditional")
        if condition and not self._evaluate_condition(condition, execution, input_data):
            self.logger.info(f"Skipping step {step_id}: condition not met")
            execution.completed_steps.append(step_id)
            execution.step_outputs[step_id] = {"skipped": True}
            return

        # Resolve step inputs
        step_input = step.get("input", {})
        resolved_input = self._resolve_variables(step_input, execution, input_data)

        # Get agent
        agent = self._agents.get(agent_id)

        if agent:
            # Create task request for agent
            step_request = TaskRequest(
                operation=OperationType(action) if action in [e.value for e in OperationType] else OperationType.COMPUTE,
                parameters=resolved_input,
            )

            response = await agent.process_task(step_request)

            if response.status == TaskStatus.FAILED:
                execution.failed_steps.append(step_id)
                raise RuntimeError(f"Step {step_id} failed: {response.error}")

            execution.step_outputs[step_id] = {"output": response.result}
        else:
            # Simulate step execution
            self.logger.warning(f"Agent {agent_id} not registered, simulating")
            execution.step_outputs[step_id] = {"output": {"simulated": True}}

        execution.completed_steps.append(step_id)
        execution.current_step = None

    async def _execute_parallel_steps(
        self,
        execution: ExecutionState,
        steps: List[Dict[str, Any]],
        step_ids: List[str],
        input_data: Dict[str, Any],
    ) -> None:
        """Execute multiple steps in parallel."""
        self.logger.info(f"Executing parallel steps: {step_ids}")

        tasks = []
        for step_id in step_ids:
            step = self._get_step(steps, step_id)
            task = asyncio.create_task(
                self._execute_step(execution, step, input_data)
            )
            tasks.append(task)

        # Wait for all to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check for errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                raise result

    def _resolve_dependencies(self, steps: List[Dict[str, Any]]) -> List[List[str]]:
        """Resolve step dependencies and return execution order."""
        # Build dependency graph
        dependencies: Dict[str, Set[str]] = {}
        parallel_groups: Dict[str, str] = {}

        for step in steps:
            step_id = step["id"]
            dependencies[step_id] = set()

            # Check for explicit dependencies
            if "depends_on" in step:
                deps = step["depends_on"]
                if isinstance(deps, str):
                    dependencies[step_id].add(deps)
                else:
                    dependencies[step_id].update(deps)

            # Check for parallel_with
            if "parallel_with" in step:
                parallel_groups[step_id] = step["parallel_with"]

        # Topological sort with parallel grouping
        result = []
        completed = set()

        while len(completed) < len(steps):
            # Find steps with all dependencies satisfied
            ready = []
            for step in steps:
                step_id = step["id"]
                if step_id not in completed:
                    if all(dep in completed for dep in dependencies[step_id]):
                        ready.append(step_id)

            if not ready:
                raise RuntimeError("Circular dependency detected in workflow")

            # Group parallel steps together
            group = []
            for step_id in ready:
                if step_id in parallel_groups:
                    partner = parallel_groups[step_id]
                    if partner in ready and partner not in group:
                        group.append(step_id)
                        group.append(partner)
                elif step_id not in group:
                    if not group:
                        group.append(step_id)
                    else:
                        # Start new group if current is parallel
                        result.append(group)
                        group = [step_id]

            if group:
                result.append(group)

            completed.update(ready)

        return result

    def _get_step(self, steps: List[Dict[str, Any]], step_id: str) -> Dict[str, Any]:
        """Get a step by ID."""
        for step in steps:
            if step["id"] == step_id:
                return step
        raise ValueError(f"Step not found: {step_id}")

    def _resolve_initial_variables(
        self,
        workflow: WorkflowDefinition,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Resolve initial workflow variables."""
        variables = {}
        for name, expression in workflow.variables.items():
            variables[name] = self._resolve_expression(expression, {"input": input_data})
        return variables

    def _resolve_variables(
        self,
        data: Any,
        execution: ExecutionState,
        input_data: Dict[str, Any],
    ) -> Any:
        """Resolve variable references in data."""
        if isinstance(data, str):
            return self._resolve_expression(data, {
                "input": input_data,
                "variables": execution.variables,
                "steps": execution.step_outputs,
            })
        elif isinstance(data, dict):
            return {k: self._resolve_variables(v, execution, input_data) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._resolve_variables(item, execution, input_data) for item in data]
        return data

    def _resolve_expression(self, expression: str, context: Dict[str, Any]) -> Any:
        """Resolve a variable expression."""
        if not isinstance(expression, str):
            return expression

        if not expression.startswith("${") or not expression.endswith("}"):
            return expression

        path = expression[2:-1]  # Remove ${ and }

        # Handle default values with ||
        if "||" in path:
            parts = path.split("||", 1)
            path = parts[0].strip()
            default = parts[1].strip().strip("'\"")
        else:
            default = None

        # Navigate path
        parts = path.split(".")
        current = context

        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                current = None
                break

        return current if current is not None else default

    def _resolve_outputs(
        self,
        workflow: WorkflowDefinition,
        execution: ExecutionState,
    ) -> Dict[str, Any]:
        """Resolve workflow outputs."""
        outputs = {}
        for name, expression in workflow.outputs.items():
            outputs[name] = self._resolve_expression(expression, {
                "steps": execution.step_outputs,
                "variables": execution.variables,
            })
        return outputs

    def _evaluate_condition(
        self,
        condition: str,
        execution: ExecutionState,
        input_data: Dict[str, Any],
    ) -> bool:
        """Evaluate a condition expression."""
        # Simple condition evaluation
        resolved = self._resolve_expression(f"${{{condition}}}", {
            "input": input_data,
            "variables": execution.variables,
            "steps": execution.step_outputs,
        })
        return bool(resolved)

    def _create_checkpoint(self, execution: ExecutionState) -> None:
        """Create a checkpoint of execution state."""
        checkpoint = {
            "checkpoint_id": str(uuid.uuid4()),
            "created_at": datetime.utcnow().isoformat(),
            "execution_id": execution.execution_id,
            "current_step": execution.current_step,
            "completed_steps": execution.completed_steps.copy(),
            "step_outputs": dict(execution.step_outputs),
            "variables": dict(execution.variables),
        }

        if execution.execution_id not in self._checkpoints:
            self._checkpoints[execution.execution_id] = []
        self._checkpoints[execution.execution_id].append(checkpoint)

    async def _handle_workflow_error(
        self,
        execution: ExecutionState,
        workflow: WorkflowDefinition,
        error: Exception,
    ) -> bool:
        """Handle workflow error using defined handlers."""
        for handler in workflow.error_handlers:
            action = handler.get("action")

            if action == "continue_with_warning":
                self.logger.warning(f"Continuing with warning: {error}")
                return True
            elif action == "restart_from_step":
                step_id = handler.get("step")
                self.logger.info(f"Restarting from step: {step_id}")
                # Would implement restart logic here
                return False
            elif action == "terminate":
                return False

        return False

    def _get_trace(self, execution: ExecutionState) -> List[Dict[str, Any]]:
        """Get execution trace."""
        trace = []
        for step_id in execution.completed_steps + execution.failed_steps:
            output = execution.step_outputs.get(step_id, {})
            trace.append({
                "step_id": step_id,
                "status": "failed" if step_id in execution.failed_steps else "completed",
                "output": output,
            })
        return trace

    async def _register_workflow(self, request: TaskRequest) -> TaskResponse:
        """Register a new workflow definition."""
        definition = request.parameters.get("definition")

        if not definition:
            return TaskResponse.failure(request.request_id, "No definition provided")

        # Parse YAML if string
        if isinstance(definition, str):
            definition = yaml.safe_load(definition)

        workflow = WorkflowDefinition(
            name=definition.get("name", f"workflow_{uuid.uuid4().hex[:8]}"),
            version=definition.get("version", "1.0"),
            steps=definition.get("steps", []),
            outputs=definition.get("outputs", {}),
        )

        self._workflows[workflow.name] = workflow

        return TaskResponse.success(
            request.request_id,
            {"workflow_name": workflow.name, "registered": True},
        )

    async def _get_execution_status(self, request: TaskRequest) -> TaskResponse:
        """Get status of an execution."""
        execution_id = request.parameters.get("execution_id")

        if execution_id not in self._executions:
            return TaskResponse.failure(request.request_id, f"Execution not found: {execution_id}")

        execution = self._executions[execution_id]

        return TaskResponse.success(
            request.request_id,
            {
                "execution_id": execution.execution_id,
                "status": execution.status,
                "current_step": execution.current_step,
                "completed_steps": execution.completed_steps,
                "failed_steps": execution.failed_steps,
                "started_at": execution.started_at.isoformat(),
                "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            },
        )

    async def _cancel_execution(self, request: TaskRequest) -> TaskResponse:
        """Cancel a running execution."""
        execution_id = request.parameters.get("execution_id")

        if execution_id not in self._executions:
            return TaskResponse.failure(request.request_id, f"Execution not found: {execution_id}")

        execution = self._executions[execution_id]
        execution.status = "cancelled"

        return TaskResponse.success(request.request_id, {"cancelled": True})

    async def _list_workflows(self, request: TaskRequest) -> TaskResponse:
        """List available workflows."""
        workflows = [
            {"name": name, "version": wf.version, "steps": len(wf.steps)}
            for name, wf in self._workflows.items()
        ]

        return TaskResponse.success(request.request_id, {"workflows": workflows})

    def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent for workflow execution."""
        self._agents[agent.agent_id] = agent
