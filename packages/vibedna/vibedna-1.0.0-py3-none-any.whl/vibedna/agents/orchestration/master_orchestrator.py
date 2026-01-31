# VibeDNA Master Orchestrator
# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

"""
Master Orchestrator - Top-level coordinator for the VibeDNA system.

The Master Orchestrator is responsible for:
- Request parsing and intent classification
- Workflow decomposition and planning
- Agent delegation and coordination
- Result aggregation and synthesis
- Error escalation and recovery
- Quality gate enforcement
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Type
import asyncio
import uuid

from vibedna.agents.base.agent_base import (
    BaseAgent,
    AgentConfig,
    AgentCapability,
    AgentTier,
    AgentStatus,
)
from vibedna.agents.base.message import (
    TaskRequest,
    TaskResponse,
    TaskStatus,
    TaskPriority,
    OperationType,
    QualityReport,
    DelegationMatrix,
)
from vibedna.agents.base.tool import Tool, ToolResult, FunctionTool
from vibedna.agents.base.context import AgentContext, WorkflowContext


@dataclass
class WorkflowPlan:
    """Plan for executing a workflow."""
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    operation: OperationType = OperationType.ENCODE
    steps: List[Dict[str, Any]] = field(default_factory=list)
    parallel_groups: List[List[str]] = field(default_factory=list)
    quality_gates: List[str] = field(default_factory=list)
    estimated_duration_seconds: float = 0.0
    resource_requirements: Dict[str, Any] = field(default_factory=dict)


class MasterOrchestrator(BaseAgent):
    """
    Master Orchestrator for the VibeDNA Agent System.

    This is the top-level coordinator that receives user requests,
    decomposes them into executable workflows, delegates to specialist
    agents, and ensures quality standards are met.
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize the Master Orchestrator."""
        if config is None:
            config = AgentConfig(
                agent_id="vibedna-master-orchestrator",
                version="1.0.0",
                tier=AgentTier.ORCHESTRATION,
                role="Strategic Coordinator",
                description="Top-level coordinator for VibeDNA system",
                capabilities=[
                    AgentCapability(
                        name="request_parsing",
                        description="Parse and classify incoming requests",
                    ),
                    AgentCapability(
                        name="workflow_planning",
                        description="Decompose requests into execution plans",
                    ),
                    AgentCapability(
                        name="agent_delegation",
                        description="Delegate tasks to specialist agents",
                    ),
                    AgentCapability(
                        name="result_aggregation",
                        description="Aggregate results from multiple agents",
                    ),
                    AgentCapability(
                        name="quality_enforcement",
                        description="Enforce quality gates and standards",
                    ),
                ],
                tools=[
                    "workflow_planner",
                    "agent_invoker",
                    "result_aggregator",
                    "quality_gate_checker",
                    "error_escalator",
                ],
                mcp_connections=[
                    "vibedna-monitor",
                    "vibedna-search",
                ],
                personality={
                    "communication_style": "precise, technical, status-oriented",
                    "decision_approach": "analytical with fallback strategies",
                    "error_handling": "graceful degradation with detailed logging",
                },
            )

        super().__init__(config)

        # Delegation matrix
        self._delegation_matrix = DelegationMatrix()

        # Agent registry
        self._agents: Dict[str, BaseAgent] = {}

        # Workflow orchestrator reference
        self._workflow_orchestrator: Optional[BaseAgent] = None

        # Resource orchestrator reference
        self._resource_orchestrator: Optional[BaseAgent] = None

        # Active workflows
        self._active_workflows: Dict[str, WorkflowContext] = {}

    def get_system_prompt(self) -> str:
        """Get the Master Orchestrator's system prompt."""
        return """You are the VibeDNA Master Orchestrator, the strategic coordinator for DNA-based
computing operations. Your responsibilities:

## Core Functions

1. **Request Analysis**: Parse incoming requests to determine:
   - Operation type (encode, decode, compute, store, retrieve, validate)
   - Data characteristics (size, format, sensitivity)
   - Quality requirements (error tolerance, speed vs accuracy)
   - Resource constraints (memory, time limits)

2. **Workflow Planning**: Decompose requests into execution plans:
   - Identify required specialist agents
   - Determine execution order (sequential vs parallel)
   - Allocate resources via Resource Orchestrator
   - Set quality checkpoints

3. **Delegation Protocol**:
   For each task in workflow:
     1. Select appropriate specialist agent
     2. Prepare task context and parameters
     3. Invoke agent with timeout
     4. Collect and validate results
     5. Handle failures with retry or escalation

4. **Quality Enforcement**:
   - Verify all checksums and integrity markers
   - Ensure error correction thresholds met
   - Validate output format compliance
   - Confirm footer presence on all outputs

## Delegation Matrix

| Request Type      | Primary Agent     | Support Agents              |
|-------------------|-------------------|-----------------------------|
| encode            | Encoder           | Validation, ErrorCorrection |
| decode            | Decoder           | ErrorCorrection, Validation |
| compute           | Compute           | Validation                  |
| store             | FileSystem        | Encoder, Index              |
| retrieve          | FileSystem        | Decoder, Index              |
| validate          | Validation        | ErrorCorrection             |
| visualize         | Visualization     | Decoder                     |
| batch_process     | Workflow          | All specialists             |

## Error Handling

- Level 1: Retry with same agent (max 3 attempts)
- Level 2: Fallback to alternative encoding scheme
- Level 3: Partial result with degradation notice
- Level 4: Escalate to human with diagnostic bundle

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC."""

    async def handle_task(self, request: TaskRequest) -> TaskResponse:
        """
        Handle an incoming task request.

        This is the main entry point for all requests to the VibeDNA system.
        """
        self.logger.info(f"Received task: {request.request_id} - {request.operation.value}")

        try:
            # Step 1: Parse and analyze request
            analysis = await self._analyze_request(request)

            # Step 2: Create workflow plan
            plan = await self._create_workflow_plan(request, analysis)

            # Step 3: Allocate resources
            allocation = await self._allocate_resources(plan)

            # Step 4: Execute workflow
            result = await self._execute_workflow(request, plan)

            # Step 5: Validate results
            quality_report = await self._validate_results(result, request)

            # Step 6: Return aggregated response
            return TaskResponse(
                request_id=request.request_id,
                status=TaskStatus.COMPLETED if quality_report.validation_passed else TaskStatus.PARTIAL,
                result=result,
                quality_report=quality_report.to_dict(),
                workflow_trace=self._get_workflow_trace(request.request_id),
                metadata={
                    "plan_id": plan.plan_id,
                    "operation": request.operation.value,
                },
            )

        except Exception as e:
            self.logger.error(f"Task {request.request_id} failed: {e}")
            return await self._handle_error(request, e)

    async def _analyze_request(self, request: TaskRequest) -> Dict[str, Any]:
        """Analyze the incoming request to determine requirements."""
        analysis = {
            "operation": request.operation.value,
            "priority": request.priority.value,
            "has_deadline": request.deadline is not None,
            "parameters": request.parameters,
        }

        # Determine data characteristics
        data = request.parameters.get("data")
        if data:
            if isinstance(data, (bytes, bytearray)):
                analysis["data_size"] = len(data)
                analysis["data_type"] = "binary"
            elif isinstance(data, str):
                analysis["data_size"] = len(data)
                analysis["data_type"] = "string"
                # Check if it's a DNA sequence
                if all(c in "ATCGatcg" for c in data):
                    analysis["data_type"] = "dna_sequence"

        # Determine quality requirements
        analysis["quality_requirements"] = {
            "error_tolerance": request.parameters.get("error_tolerance", "normal"),
            "verify_checksum": request.parameters.get("verify_checksum", True),
            "add_error_correction": request.parameters.get("add_error_correction", True),
        }

        return analysis

    async def _create_workflow_plan(
        self,
        request: TaskRequest,
        analysis: Dict[str, Any],
    ) -> WorkflowPlan:
        """Create an execution plan for the request."""
        plan = WorkflowPlan(operation=request.operation)

        # Get agents for this operation
        agents = self._delegation_matrix.get_agents_for_operation(request.operation.value)
        primary_agents = agents.get("primary", [])
        support_agents = agents.get("support", [])

        # Build workflow steps based on operation type
        if request.operation == OperationType.ENCODE:
            plan.steps = [
                {"id": "validate_input", "agent": "validation-agent", "action": "validate_binary"},
                {"id": "encode_data", "agent": "encoder-agent", "action": "encode"},
                {"id": "add_error_correction", "agent": "error-correction-agent", "action": "apply_reed_solomon"},
                {"id": "validate_output", "agent": "validation-agent", "action": "validate_sequence"},
            ]
            plan.quality_gates = ["input_validation", "encoding_complete", "output_validation"]

        elif request.operation == OperationType.DECODE:
            plan.steps = [
                {"id": "validate_sequence", "agent": "validation-agent", "action": "validate_sequence"},
                {"id": "apply_error_correction", "agent": "error-correction-agent", "action": "decode_reed_solomon"},
                {"id": "decode_data", "agent": "decoder-agent", "action": "decode"},
                {"id": "verify_checksum", "agent": "validation-agent", "action": "verify_checksum"},
            ]
            plan.quality_gates = ["sequence_valid", "decoding_complete", "checksum_valid"]

        elif request.operation == OperationType.COMPUTE:
            plan.steps = [
                {"id": "validate_sequences", "agent": "validation-agent", "action": "validate_sequences"},
                {"id": "execute_operation", "agent": "compute-agent", "action": request.parameters.get("operation", "and")},
                {"id": "validate_result", "agent": "validation-agent", "action": "validate_sequence"},
            ]
            plan.quality_gates = ["input_valid", "computation_complete"]

        elif request.operation == OperationType.STORE:
            plan.steps = [
                {"id": "encode_if_needed", "agent": "encoder-agent", "action": "encode", "conditional": True},
                {"id": "store_file", "agent": "filesystem-agent", "action": "create_file"},
                {"id": "index_file", "agent": "index-agent", "action": "add_to_catalog"},
            ]
            plan.parallel_groups = [["store_file", "index_file"]]
            plan.quality_gates = ["storage_complete", "indexing_complete"]

        elif request.operation == OperationType.RETRIEVE:
            plan.steps = [
                {"id": "lookup_file", "agent": "index-agent", "action": "lookup"},
                {"id": "read_file", "agent": "filesystem-agent", "action": "read_file"},
                {"id": "decode_if_needed", "agent": "decoder-agent", "action": "decode", "conditional": True},
            ]
            plan.quality_gates = ["retrieval_complete"]

        elif request.operation == OperationType.VALIDATE:
            plan.steps = [
                {"id": "validate_format", "agent": "validation-agent", "action": "validate_format"},
                {"id": "validate_structure", "agent": "validation-agent", "action": "validate_structure"},
                {"id": "verify_integrity", "agent": "validation-agent", "action": "verify_integrity"},
            ]
            plan.quality_gates = ["validation_complete"]

        else:
            # Default single-step plan
            plan.steps = [
                {"id": "execute", "agent": primary_agents[0] if primary_agents else "master-orchestrator", "action": request.operation.value},
            ]

        # Estimate duration
        plan.estimated_duration_seconds = len(plan.steps) * 1.0  # 1 second per step baseline

        return plan

    async def _allocate_resources(self, plan: WorkflowPlan) -> Dict[str, Any]:
        """Allocate resources for the workflow."""
        if self._resource_orchestrator:
            # Delegate to Resource Orchestrator
            resource_request = TaskRequest(
                operation=OperationType.COMPUTE,
                parameters={
                    "action": "allocate",
                    "plan": plan.__dict__,
                },
            )
            response = await self._resource_orchestrator.process_task(resource_request)
            return response.result if response.result else {}

        # Default allocation
        return {
            "allocation_id": str(uuid.uuid4()),
            "memory_bytes": 100 * 1024 * 1024,  # 100MB
            "cpu_cores": 1,
            "timeout_seconds": plan.estimated_duration_seconds * 2,
        }

    async def _execute_workflow(
        self,
        request: TaskRequest,
        plan: WorkflowPlan,
    ) -> Any:
        """Execute the workflow plan."""
        # Create workflow context
        context = WorkflowContext(
            workflow_name=f"{request.operation.value}_workflow",
            definition={"steps": plan.steps},
            trigger_data=request.parameters,
        )

        self._active_workflows[request.request_id] = context

        # If we have a Workflow Orchestrator, delegate to it
        if self._workflow_orchestrator:
            workflow_request = TaskRequest(
                operation=OperationType.BATCH_PROCESS,
                parameters={
                    "plan": plan.__dict__,
                    "context": context.__dict__,
                },
            )
            response = await self._workflow_orchestrator.process_task(workflow_request)
            return response.result

        # Otherwise, execute steps directly
        result = None
        for step in plan.steps:
            context.start_step(step["id"])

            # Get the agent for this step
            agent = self._agents.get(step["agent"])

            if agent:
                step_request = TaskRequest(
                    operation=OperationType(step["action"]) if step["action"] in [e.value for e in OperationType] else OperationType.COMPUTE,
                    parameters={
                        **request.parameters,
                        "previous_result": result,
                    },
                )
                response = await agent.process_task(step_request)

                if response.status == TaskStatus.FAILED:
                    context.fail_step(step["id"], response.error or "Unknown error")
                    raise RuntimeError(f"Step {step['id']} failed: {response.error}")

                result = response.result
                context.complete_step(step["id"], {"output": result})
            else:
                # Simulate step execution
                self.logger.warning(f"Agent {step['agent']} not registered, simulating step")
                context.complete_step(step["id"], {"output": "simulated"})

        context.outputs["final_result"] = result
        return result

    async def _validate_results(
        self,
        result: Any,
        request: TaskRequest,
    ) -> QualityReport:
        """Validate the workflow results."""
        report = QualityReport()

        if result is None:
            report.validation_passed = False
            report.warnings.append("Result is None")
            return report

        # Check for DNA sequence result
        if isinstance(result, dict):
            sequence = result.get("sequence")
            if sequence:
                # Validate sequence format
                if not all(c in "ATCG" for c in sequence.upper()):
                    report.validation_passed = False
                    report.warnings.append("Invalid characters in sequence")
                else:
                    # Calculate GC content
                    gc_count = sum(1 for c in sequence.upper() if c in "GC")
                    report.gc_content = gc_count / len(sequence) if sequence else 0

                    # Find max homopolymer
                    max_run = 1
                    current_run = 1
                    for i in range(1, len(sequence)):
                        if sequence[i] == sequence[i - 1]:
                            current_run += 1
                            max_run = max(max_run, current_run)
                        else:
                            current_run = 1
                    report.homopolymer_max = max_run

            # Check for checksum
            checksum = result.get("checksum")
            report.checksum_valid = checksum is not None

            # Check for error correction
            errors_corrected = result.get("errors_corrected", 0)
            report.errors_corrected = errors_corrected
            report.error_correction_applied = errors_corrected > 0 or result.get("error_correction_applied", False)

        return report

    async def _handle_error(
        self,
        request: TaskRequest,
        error: Exception,
    ) -> TaskResponse:
        """Handle errors with escalation levels."""
        error_level = 1

        # Determine error level based on error type
        if isinstance(error, TimeoutError):
            error_level = 2
        elif isinstance(error, RuntimeError):
            error_level = 3

        self.logger.error(f"Error level {error_level} for task {request.request_id}: {error}")

        # Level-based handling
        if error_level <= 2:
            # Try fallback strategy
            self.logger.info(f"Attempting fallback for task {request.request_id}")

        return TaskResponse(
            request_id=request.request_id,
            status=TaskStatus.FAILED,
            error=str(error),
            metadata={
                "error_level": error_level,
                "error_type": type(error).__name__,
            },
        )

    def _get_workflow_trace(self, request_id: str) -> List[Dict[str, Any]]:
        """Get the execution trace for a workflow."""
        context = self._active_workflows.get(request_id)
        if context:
            return context.get_trace()
        return []

    def register_agent(self, agent: BaseAgent) -> None:
        """Register a specialist agent."""
        self._agents[agent.agent_id] = agent
        self.logger.info(f"Registered agent: {agent.agent_id}")

    def set_workflow_orchestrator(self, orchestrator: BaseAgent) -> None:
        """Set the Workflow Orchestrator reference."""
        self._workflow_orchestrator = orchestrator

    def set_resource_orchestrator(self, orchestrator: BaseAgent) -> None:
        """Set the Resource Orchestrator reference."""
        self._resource_orchestrator = orchestrator

    def _register_default_tools(self) -> None:
        """Register default tools for the Master Orchestrator."""
        # Workflow planner tool
        self.register_tool(FunctionTool(
            self._plan_workflow,
            name="workflow_planner",
            description="Create a workflow plan for a request",
        ))

        # Agent invoker tool
        self.register_tool(FunctionTool(
            self._invoke_agent,
            name="agent_invoker",
            description="Invoke a registered agent with a task",
        ))

        # Quality gate checker tool
        self.register_tool(FunctionTool(
            self._check_quality_gate,
            name="quality_gate_checker",
            description="Check if a quality gate has passed",
        ))

    async def _plan_workflow(self, operation: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Tool implementation for workflow planning."""
        request = TaskRequest(
            operation=OperationType(operation),
            parameters=parameters,
        )
        analysis = await self._analyze_request(request)
        plan = await self._create_workflow_plan(request, analysis)
        return {
            "plan_id": plan.plan_id,
            "steps": plan.steps,
            "quality_gates": plan.quality_gates,
        }

    async def _invoke_agent(self, agent_id: str, operation: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Tool implementation for agent invocation."""
        agent = self._agents.get(agent_id)
        if not agent:
            return {"error": f"Agent not found: {agent_id}"}

        request = TaskRequest(
            operation=OperationType(operation) if operation in [e.value for e in OperationType] else OperationType.COMPUTE,
            parameters=parameters,
        )
        response = await agent.process_task(request)
        return response.to_dict()

    async def _check_quality_gate(self, gate_name: str, result: Any) -> Dict[str, Any]:
        """Tool implementation for quality gate checking."""
        # Simplified quality gate check
        passed = result is not None
        return {
            "gate": gate_name,
            "passed": passed,
        }
