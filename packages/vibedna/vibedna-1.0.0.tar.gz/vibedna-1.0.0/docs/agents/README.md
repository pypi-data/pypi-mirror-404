# VibeDNA Agent Orchestration System

A hierarchical multi-agent architecture for distributed DNA encoding, decoding, computation, and file management operations.

## Table of Contents

1. [Agent System Overview](#agent-system-overview)
2. [Orchestration Tier Agents](#orchestration-tier-agents)
3. [Specialist Tier Agents](#specialist-tier-agents)
4. [Support Tier Agents](#support-tier-agents)
5. [MCP Servers](#mcp-servers)
6. [Creating Custom Agents](#creating-custom-agents)

---

## Agent System Overview

### Purpose and Design Philosophy

The VibeDNA Agent Orchestration System provides a scalable, modular architecture for DNA-based computing operations. The system is designed around the following principles:

- **Separation of Concerns**: Each agent has a specific role and responsibility
- **Hierarchical Coordination**: Strategic, tactical, and operational layers ensure efficient task management
- **Fault Tolerance**: Built-in error handling, retries, and graceful degradation
- **Extensibility**: New agents can be easily added to extend functionality
- **Quality Assurance**: Quality gates and validation at every step

### Three-Tier Architecture

The agent system is organized into three tiers:

```
                    ┌─────────────────────────────────────┐
                    │       ORCHESTRATION TIER            │
                    │  (Strategic Coordination Layer)     │
                    ├─────────────────────────────────────┤
                    │  MasterOrchestrator                 │
                    │  WorkflowOrchestrator               │
                    │  ResourceOrchestrator               │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │        SPECIALIST TIER              │
                    │   (Domain-Specific Execution)       │
                    ├─────────────────────────────────────┤
                    │  EncoderAgent    DecoderAgent       │
                    │  ComputeAgent    ValidationAgent    │
                    │  FileSystemAgent ErrorCorrectionAgent│
                    │  VisualizationAgent SynthesisAgent  │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │         SUPPORT TIER                │
                    │   (Infrastructure & Utilities)      │
                    ├─────────────────────────────────────┤
                    │  IndexAgent      MetricsAgent       │
                    │  LoggingAgent    DocsAgent          │
                    │  SecurityAgent                      │
                    └─────────────────────────────────────┘
```

### Core Abstractions

#### BaseAgent

All agents inherit from `BaseAgent`, which provides:

```python
from vibedna.agents import BaseAgent, AgentConfig, AgentCapability, AgentTier

class BaseAgent(ABC):
    """Abstract base class for all VibeDNA agents."""

    FOOTER = "© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC."

    def __init__(self, config: AgentConfig):
        self.config = config
        self._status = AgentStatus.INITIALIZING
        self._tools: Dict[str, Tool] = {}
        self._tasks_completed = 0
        self._tasks_failed = 0

    @abstractmethod
    async def handle_task(self, request: TaskRequest) -> TaskResponse:
        """Handle an incoming task request."""
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the agent's system prompt."""
        pass
```

#### AgentConfig

Configuration for an agent instance:

```python
@dataclass
class AgentConfig:
    agent_id: str
    version: str = "1.0.0"
    tier: AgentTier = AgentTier.SPECIALIST
    role: str = ""
    description: str = ""
    capabilities: List[AgentCapability] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    mcp_connections: List[str] = field(default_factory=list)
    max_concurrent_tasks: int = 10
    timeout_seconds: float = 300.0
    retry_attempts: int = 3
```

#### Message Types

```python
class TaskRequest:
    request_id: str
    operation: OperationType  # ENCODE, DECODE, COMPUTE, STORE, etc.
    priority: TaskPriority    # LOW, NORMAL, HIGH, CRITICAL
    parameters: Dict[str, Any]
    context: Dict[str, Any]

class TaskResponse:
    request_id: str
    status: TaskStatus        # COMPLETED, FAILED, PARTIAL, etc.
    result: Any
    quality_report: Dict[str, Any]
    workflow_trace: List[Dict[str, Any]]
```

---

## Orchestration Tier Agents

### MasterOrchestrator

The top-level coordinator for the VibeDNA system. Receives user requests, decomposes them into executable workflows, delegates to specialist agents, and ensures quality standards are met.

#### Capabilities

| Capability | Description |
|------------|-------------|
| `request_parsing` | Parse and classify incoming requests |
| `workflow_planning` | Decompose requests into execution plans |
| `agent_delegation` | Delegate tasks to specialist agents |
| `result_aggregation` | Aggregate results from multiple agents |
| `quality_enforcement` | Enforce quality gates and standards |

#### Configuration

```python
from vibedna.agents import MasterOrchestrator, AgentConfig

# Using default configuration
master = MasterOrchestrator()

# Custom configuration
config = AgentConfig(
    agent_id="my-master-orchestrator",
    version="1.0.0",
    tier=AgentTier.ORCHESTRATION,
    max_concurrent_tasks=20,
    timeout_seconds=600.0,
    mcp_connections=["vibedna-monitor", "vibedna-search"],
)
master = MasterOrchestrator(config)
```

#### Usage

```python
import asyncio
from vibedna.agents import MasterOrchestrator, TaskRequest, OperationType

async def main():
    # Initialize orchestrator
    master = MasterOrchestrator()
    await master.initialize()

    # Register specialist agents
    master.register_agent(encoder_agent)
    master.register_agent(decoder_agent)
    master.register_agent(validation_agent)

    # Create an encoding request
    request = TaskRequest(
        operation=OperationType.ENCODE,
        parameters={
            "data": b"Hello, DNA!",
            "scheme": "quaternary",
            "filename": "hello.txt",
        },
    )

    # Process the request
    response = await master.process_task(request)

    print(f"Status: {response.status}")
    print(f"Sequence: {response.result['sequence'][:50]}...")
    print(f"Checksum: {response.result['checksum']}")

asyncio.run(main())
```

#### Delegation Matrix

| Request Type | Primary Agent | Support Agents |
|--------------|---------------|----------------|
| encode | Encoder | Validation, ErrorCorrection |
| decode | Decoder | ErrorCorrection, Validation |
| compute | Compute | Validation |
| store | FileSystem | Encoder, Index |
| retrieve | FileSystem | Decoder, Index |
| validate | Validation | ErrorCorrection |
| visualize | Visualization | Decoder |
| batch_process | Workflow | All specialists |

---

### WorkflowOrchestrator

Tactical workflow manager responsible for executing multi-step workflows, handling parallel execution, maintaining state, and coordinating handoffs between agents.

#### Capabilities

| Capability | Description |
|------------|-------------|
| `workflow_execution` | Execute multi-step workflows |
| `parallel_scheduling` | Schedule and execute parallel tasks |
| `state_management` | Manage workflow state and checkpoints |
| `dependency_resolution` | Resolve step dependencies |

#### Built-in Workflows

```python
# Available built-in workflows:
BUILTIN_WORKFLOWS = {
    "encode_simple",      # Basic encoding workflow
    "encode_with_ec",     # Encoding with error correction
    "decode_simple",      # Basic decoding workflow
    "decode_with_repair", # Decoding with error repair
    "store_and_index",    # Store file and add to index
}
```

#### Workflow Definition Language (YAML DSL)

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

    - id: add_error_correction
      agent: error-correction-agent
      action: apply_reed_solomon
      input:
        sequence: "${steps.encode_data.output.sequence}"

  outputs:
    sequence: "${steps.add_error_correction.output.sequence}"
    checksum: "${steps.add_error_correction.output.checksum}"
```

#### Usage

```python
from vibedna.agents import WorkflowOrchestrator, TaskRequest

async def run_workflow():
    workflow = WorkflowOrchestrator()
    await workflow.initialize()

    # Execute a built-in workflow
    request = TaskRequest(
        parameters={
            "action": "execute",
            "workflow_name": "encode_with_ec",
            "input": {
                "data": b"Important data",
                "scheme": "balanced_gc",
            },
        },
    )

    response = await workflow.process_task(request)

    # Register a custom workflow
    register_request = TaskRequest(
        parameters={
            "action": "register",
            "definition": workflow_yaml_string,
        },
    )
    await workflow.process_task(register_request)
```

---

### ResourceOrchestrator

Operational resource manager responsible for resource allocation, load balancing, quota enforcement, and auto-scaling.

#### Capabilities

| Capability | Description |
|------------|-------------|
| `resource_allocation` | Allocate resources for tasks |
| `load_balancing` | Balance load across agent pools |
| `quota_management` | Enforce usage quotas |
| `auto_scaling` | Trigger auto-scaling based on load |

#### Default Pool Configurations

```python
DEFAULT_POOLS = {
    "encoder_pool": AgentPoolConfig("encoder_pool", min=2, max=10),
    "decoder_pool": AgentPoolConfig("decoder_pool", min=2, max=10),
    "compute_pool": AgentPoolConfig("compute_pool", min=1, max=5),
    "filesystem_pool": AgentPoolConfig("filesystem_pool", min=2, max=8),
    "validation_pool": AgentPoolConfig("validation_pool", min=2, max=6),
}
```

#### Quota Configuration

```python
@dataclass
class QuotaConfig:
    encode_requests_per_hour: int = 1000
    decode_requests_per_hour: int = 1000
    compute_operations_per_hour: int = 500
    storage_bytes: int = 10 * 1024 * 1024 * 1024  # 10 GB
    max_input_size: int = 100 * 1024 * 1024       # 100 MB
    max_sequence_length: int = 1_000_000_000      # 1B nucleotides
    timeout_seconds: int = 3600
```

#### Usage

```python
from vibedna.agents import ResourceOrchestrator, TaskRequest

async def allocate_resources():
    resource_mgr = ResourceOrchestrator()
    await resource_mgr.initialize()

    # Allocate resources for a task
    request = TaskRequest(
        parameters={
            "action": "allocate",
            "task_id": "encode-123",
            "task_type": "encode",
            "input_size": 1024 * 1024,  # 1 MB
            "priority": 3,  # HIGH
            "user_id": "user-456",
        },
    )

    response = await resource_mgr.process_task(request)
    allocation = response.result

    print(f"Allocation ID: {allocation['allocation_id']}")
    print(f"Memory: {allocation['memory_bytes']} bytes")
    print(f"Pool: {allocation['pool']}")

    # Release resources when done
    release_request = TaskRequest(
        parameters={
            "action": "release",
            "allocation_id": allocation['allocation_id'],
        },
    )
    await resource_mgr.process_task(release_request)
```

#### Load Balancing Strategy

The ResourceOrchestrator uses weighted round-robin selection with:
- Inverse of current load as weight
- Cache affinity bonus (2x for warm cache)
- Health check filtering

---

## Specialist Tier Agents

### EncoderAgent

Specialized agent for binary-to-DNA conversion supporting multiple encoding schemes.

#### Encoding Schemes

| Scheme | Density (bits/nt) | Error Tolerance | Use Case |
|--------|-------------------|-----------------|----------|
| `quaternary` | 2.0 | Low | Maximum storage density |
| `balanced_gc` | ~1.9 | Medium | DNA synthesis compatibility |
| `rll` | ~1.7 | Medium | Sequencing accuracy |
| `triplet` | 0.67 | High | Maximum error tolerance |

#### Usage

```python
from vibedna.agents import EncoderAgent, TaskRequest

async def encode_data():
    encoder = EncoderAgent()
    await encoder.initialize()

    request = TaskRequest(
        parameters={
            "data": b"Hello, DNA World!",
            "scheme": "quaternary",
            "filename": "hello.txt",
            "add_error_correction": True,
        },
    )

    response = await encoder.process_task(request)

    print(f"Sequence length: {response.result['nucleotide_count']}")
    print(f"GC content: {response.result['metadata']['gc_content']:.1%}")
    print(f"Checksum: {response.result['checksum']}")
```

---

### DecoderAgent

Specialized agent for DNA-to-binary conversion with automatic scheme detection.

#### Capabilities

- Automatic encoding scheme detection
- Error detection during decoding
- Checksum verification
- Support for all encoding schemes

#### Usage

```python
from vibedna.agents import DecoderAgent, TaskRequest

async def decode_sequence():
    decoder = DecoderAgent()
    await decoder.initialize()

    request = TaskRequest(
        parameters={
            "sequence": "ATCGATCG...",  # DNA sequence
            "verify_checksum": True,
            "attempt_repair": True,
        },
    )

    response = await decoder.process_task(request)

    print(f"Filename: {response.result['filename']}")
    print(f"MIME type: {response.result['mime_type']}")
    print(f"Errors corrected: {response.result['errors_corrected']}")
```

---

### ErrorCorrectionAgent

Implements Reed-Solomon error correction adapted for DNA (GF(4) arithmetic).

#### Reed-Solomon for DNA

```
DNA operates in GF(4):
- Elements: {0, 1, α, α+1} = {A, T, C, G}
- With 16 parity nucleotides per block:
  - Can detect up to 16 errors
  - Can correct up to 8 errors
```

#### Mutation Model

DNA has specific mutation patterns that the agent accounts for:
- Transitions (A↔G, T↔C): 70% probability
- Transversions (purine↔pyrimidine): 30% probability

#### Usage

```python
from vibedna.agents import ErrorCorrectionAgent, TaskRequest

async def apply_error_correction():
    ec_agent = ErrorCorrectionAgent()
    await ec_agent.initialize()

    # Apply Reed-Solomon encoding
    encode_request = TaskRequest(
        parameters={
            "action": "apply_reed_solomon",
            "sequence": "ATCGATCGATCGATCG",
        },
    )
    response = await ec_agent.process_task(encode_request)
    protected_sequence = response.result['sequence']

    # Decode with error correction
    decode_request = TaskRequest(
        parameters={
            "action": "decode_reed_solomon",
            "sequence": corrupted_sequence,
        },
    )
    response = await ec_agent.process_task(decode_request)

    print(f"Errors detected: {response.result['errors_detected']}")
    print(f"Errors corrected: {response.result['errors_corrected']}")
```

---

### ComputeAgent

Performs computations directly on DNA sequences without encode/decode cycles.

#### DNA Logic Gates

| Gate | Operation | Description |
|------|-----------|-------------|
| AND | min(a, b) | Minimum of nucleotide values |
| OR | max(a, b) | Maximum of nucleotide values |
| XOR | (a + b) mod 4 | Modular addition |
| NOT | complement | A↔G, T↔C |
| NAND | NOT(AND) | Negated AND |
| NOR | NOT(OR) | Negated OR |
| XNOR | NOT(XOR) | Negated XOR |

#### DNA Arithmetic

```
Nucleotide values: A=0, T=1, C=2, G=3

Operations:
- Addition: Base-4 addition with carry
- Subtraction: Base-4 subtraction with borrow
- Multiplication: Standard base-4 algorithm
- Division: Returns quotient and remainder
```

#### Usage

```python
from vibedna.agents import ComputeAgent, TaskRequest

async def dna_computation():
    compute = ComputeAgent()
    await compute.initialize()

    # Logic gate operation
    gate_request = TaskRequest(
        parameters={
            "operation": "xor",
            "sequence_a": "ATCGATCG",
            "sequence_b": "GCTAGCTA",
        },
    )
    response = await compute.process_task(gate_request)
    print(f"XOR result: {response.result['result']}")

    # Arithmetic operation
    add_request = TaskRequest(
        parameters={
            "operation": "add",
            "sequence_a": "ATCG",
            "sequence_b": "GCTA",
        },
    )
    response = await compute.process_task(add_request)
    print(f"Sum: {response.result['result']}")
    print(f"Overflow: {response.result['overflow']}")
```

---

### FileSystemAgent

Manages a virtual file system where all data is stored as DNA sequences.

#### File System Structure

```
/
├── .vibedna/
│   ├── config.dna          # System configuration
│   ├── catalog.dna         # File catalog/index
│   └── trash/              # Deleted files (recoverable)
├── documents/
├── images/
├── data/
└── projects/
```

#### Operations

| Action | Description |
|--------|-------------|
| `create_file` | Create new file with DNA encoding |
| `read_file` | Read and decode file |
| `update_file` | Update existing file |
| `delete_file` | Delete (move to trash or permanent) |
| `list_directory` | List directory contents |
| `search` | Search by query, tags, MIME types |

#### Usage

```python
from vibedna.agents import FileSystemAgent, TaskRequest
import base64

async def file_operations():
    fs = FileSystemAgent()
    await fs.initialize()

    # Create a file
    create_request = TaskRequest(
        parameters={
            "action": "create_file",
            "path": "/documents/report.txt",
            "data": base64.b64encode(b"Annual Report").decode(),
            "mime_type": "text/plain",
            "tags": ["report", "2026"],
        },
    )
    response = await fs.process_task(create_request)
    print(f"File ID: {response.result['file_id']}")

    # Read a file
    read_request = TaskRequest(
        parameters={
            "action": "read_file",
            "path": "/documents/report.txt",
        },
    )
    response = await fs.process_task(read_request)
    data = base64.b64decode(response.result['data'])
```

---

### ValidationAgent

Performs comprehensive validation of DNA sequences including format, structure, and biological constraint checks.

#### Validation Checks

| Check | Severity | Description |
|-------|----------|-------------|
| Character validation | Error | Only ATCG allowed |
| Header validation | Error | Magic sequence, version, scheme |
| Footer validation | Error | End marker, block count, checksum |
| Checksum validation | Error | Verify integrity |
| GC content check | Warning | Warn if outside 30-70% |
| Homopolymer check | Warning | Warn if runs > 5 |

#### Usage

```python
from vibedna.agents import ValidationAgent, TaskRequest

async def validate_sequence():
    validator = ValidationAgent()
    await validator.initialize()

    request = TaskRequest(
        parameters={
            "action": "validate_sequence",
            "sequence": dna_sequence,
        },
    )

    response = await validator.process_task(request)

    print(f"Valid: {response.result['valid']}")
    for issue in response.result['issues']:
        print(f"  [{issue['severity']}] {issue['code']}: {issue['message']}")
```

---

### VisualizationAgent

Creates visual representations of DNA sequences and statistics.

#### Visualization Types

| Type | Description |
|------|-------------|
| `sequence_view` | Formatted sequence display with annotations |
| `statistics` | Nucleotide distribution, GC content |
| `dashboard` | Complete statistics dashboard |

#### Usage

```python
from vibedna.agents import VisualizationAgent, TaskRequest

async def visualize_sequence():
    viz = VisualizationAgent()
    await viz.initialize()

    # Generate sequence view
    view_request = TaskRequest(
        parameters={
            "action": "sequence_view",
            "sequence": dna_sequence,
            "line_length": 60,
        },
    )
    response = await viz.process_task(view_request)
    print(response.result['view'])

    # Generate statistics dashboard
    dashboard_request = TaskRequest(
        parameters={
            "action": "dashboard",
            "sequence": dna_sequence,
        },
    )
    response = await viz.process_task(dashboard_request)
    print(response.result['dashboard'])
```

---

### SynthesisAgent

Optimizes sequences for physical DNA synthesis on various platforms.

#### Supported Platforms

| Platform | Max Length | GC Range | Max Homopolymer |
|----------|------------|----------|-----------------|
| Twist Bioscience | 300 bp | 25-65% | 6 |
| IDT | 200 bp | 30-70% | 4 |
| GenScript | 500 bp | 20-80% | 8 |

#### Optimization Steps

1. Check GC content and balance if needed
2. Break long homopolymer runs
3. Remove forbidden sequences (restriction sites)
4. Fragment if length exceeds platform max
5. Generate synthesis order

#### Usage

```python
from vibedna.agents import SynthesisAgent, TaskRequest

async def prepare_synthesis():
    synth = SynthesisAgent()
    await synth.initialize()

    # Optimize sequence
    optimize_request = TaskRequest(
        parameters={
            "action": "optimize",
            "sequence": long_sequence,
            "platform": "twist_bioscience",
        },
    )
    response = await synth.process_task(optimize_request)
    optimized = response.result['optimized']

    # Generate synthesis order
    order_request = TaskRequest(
        parameters={
            "action": "generate_order",
            "sequence": optimized,
            "platform": "twist_bioscience",
            "project_name": "VibeDNA_Project_001",
        },
    )
    response = await synth.process_task(order_request)
    print(response.result['order_content'])
```

---

## Support Tier Agents

### IndexAgent

Maintains a searchable index of all DNA sequences for fast lookup and retrieval.

#### Capabilities

| Capability | Description |
|------------|-------------|
| `catalog_management` | Add, update, remove entries |
| `full_text_search` | Search by name, tags, metadata |
| `similarity_search` | Find similar sequences using MinHash |

#### Usage

```python
from vibedna.agents import IndexAgent, TaskRequest

async def index_operations():
    index = IndexAgent()
    await index.initialize()

    # Add to index
    add_request = TaskRequest(
        parameters={
            "action": "add_to_catalog",
            "id": "seq-001",
            "path": "/data/sequence1.dna",
            "name": "Sample Sequence",
            "tags": ["sample", "test"],
            "metadata": {"created_by": "user1"},
        },
    )
    await index.process_task(add_request)

    # Search
    search_request = TaskRequest(
        parameters={
            "action": "search",
            "query": "sample",
            "tags": ["test"],
        },
    )
    response = await index.process_task(search_request)
    print(f"Found {response.result['count']} results")
```

---

### MetricsAgent

Collects and reports system performance metrics.

#### Metrics Categories

| Category | Metrics |
|----------|---------|
| Throughput | Requests per minute, bytes processed |
| Latency | P50, P99 response times |
| Errors | Error rates, failure counts |
| Storage | Memory, storage usage |

#### Usage

```python
from vibedna.agents import MetricsAgent, TaskRequest

async def get_metrics():
    metrics = MetricsAgent()
    await metrics.initialize()

    # Get all metrics
    request = TaskRequest(
        parameters={
            "action": "get_metrics",
            "category": "all",
        },
    )
    response = await metrics.process_task(request)

    print(f"Encode requests: {response.result['throughput']['encode_requests']}")
    print(f"Encode P50 latency: {response.result['latency']['encode_p50']}ms")
    print(f"Error rate: {response.result['errors']['error_rate']:.2%}")
```

---

### LoggingAgent

Centralized log collection and retrieval.

#### Log Levels

- `DEBUG`: Detailed debugging information
- `INFO`: General operational information
- `WARNING`: Potential issues
- `ERROR`: Error conditions
- `CRITICAL`: Critical failures

#### Usage

```python
from vibedna.agents import LoggingAgent, TaskRequest

async def logging_operations():
    logger = LoggingAgent()
    await logger.initialize()

    # Add log entry
    log_request = TaskRequest(
        parameters={
            "action": "log",
            "level": "info",
            "source": "encoder-agent",
            "message": "Encoding completed successfully",
            "metadata": {"request_id": "req-123"},
        },
    )
    await logger.process_task(log_request)

    # Search logs
    search_request = TaskRequest(
        parameters={
            "action": "search",
            "level": "error",
            "source": "encoder-agent",
            "limit": 50,
        },
    )
    response = await logger.process_task(search_request)
```

---

### DocsAgent

Generates documentation for sequences, workflows, and APIs.

#### Documentation Types

| Type | Description |
|------|-------------|
| `generate_sequence_doc` | Sequence metadata and structure |
| `generate_workflow_doc` | Workflow definitions and steps |
| `generate_api_doc` | API endpoint documentation |

#### Usage

```python
from vibedna.agents import DocsAgent, TaskRequest

async def generate_docs():
    docs = DocsAgent()
    await docs.initialize()

    # Generate sequence documentation
    request = TaskRequest(
        parameters={
            "action": "generate_sequence_doc",
            "sequence": dna_sequence,
            "metadata": {
                "filename": "data.txt",
                "encoding": "quaternary",
            },
        },
    )
    response = await docs.process_task(request)
    print(response.result['documentation'])
```

---

### SecurityAgent

Manages access control policies and security auditing.

#### Capabilities

| Capability | Description |
|------------|-------------|
| `access_control` | Manage permissions and policies |
| `request_validation` | Validate request authorization |
| `audit_logging` | Log security events |

#### Usage

```python
from vibedna.agents import SecurityAgent, TaskRequest

async def security_operations():
    security = SecurityAgent()
    await security.initialize()

    # Check access
    check_request = TaskRequest(
        parameters={
            "action": "check_access",
            "user_id": "user-123",
            "resource": "/data/sensitive.dna",
            "requested_action": "read",
        },
    )
    response = await security.process_task(check_request)

    if response.result['allowed']:
        print("Access granted")
    else:
        print(f"Access denied: {response.result['reason']}")

    # Create a custom policy
    policy_request = TaskRequest(
        parameters={
            "action": "create_policy",
            "policy_id": "restricted",
            "name": "Restricted Access",
            "permissions": [
                {"resource": "/public/*", "actions": ["read"]},
                {"resource": "/data/*", "actions": ["read", "write"]},
            ],
        },
    )
    await security.process_task(policy_request)
```

---

## MCP Servers

VibeDNA provides six MCP (Model Context Protocol) servers that expose agent capabilities to AI systems.

### vibedna-core

Core encoding and decoding operations.

**URL**: `https://mcp.vibedna.vibecaas.com/core`
**Port**: 8090

#### Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `encode_binary` | Encode binary data to DNA | `data`, `scheme`, `filename`, `add_error_correction` |
| `decode_dna` | Decode DNA to binary | `sequence`, `verify` |
| `validate_sequence` | Validate sequence format | `sequence` |
| `get_sequence_info` | Get sequence information | `sequence` |

#### Resources

| Resource | URI | Description |
|----------|-----|-------------|
| `encoding_schemes` | `vibedna://schemes` | Available encoding schemes |

---

### vibedna-fs

DNA-based file storage operations.

**URL**: `https://mcp.vibedna.vibecaas.com/filesystem`
**Port**: 8092

#### Tools

| Tool | Description |
|------|-------------|
| `create_file` | Create file in DNA storage |
| `read_file` | Read file from DNA storage |
| `update_file` | Update existing file |
| `delete_file` | Delete file from storage |
| `list_directory` | List directory contents |
| `search_files` | Search for files |
| `get_raw_sequence` | Get raw DNA sequence for a file |

---

### vibedna-compute

DNA-native computation operations.

**URL**: `https://mcp.vibedna.vibecaas.com/compute`
**Port**: 8091

#### Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `logic_gate` | Apply logic gate | `gate`, `sequence_a`, `sequence_b` |
| `arithmetic` | Perform arithmetic | `operation`, `sequence_a`, `sequence_b` |
| `compare` | Compare sequences | `sequence_a`, `sequence_b` |
| `shift` | Bit shift sequence | `sequence`, `direction`, `positions` |
| `evaluate_expression` | Evaluate compound expression | `expression`, `variables` |

---

### vibedna-monitor

System monitoring and metrics.

**URL**: `https://mcp.vibedna.vibecaas.com/monitor`
**Port**: 8094

#### Tools

| Tool | Description |
|------|-------------|
| `get_metrics` | Get current system metrics |
| `get_health` | Get system health status |
| `get_agent_status` | Get status of all agents |
| `get_workflow_status` | Get status of running workflows |
| `record_metric` | Record a metric value |

---

### vibedna-search

Sequence and file indexing.

**URL**: `https://mcp.vibedna.vibecaas.com/search`
**Port**: 8093

#### Tools

| Tool | Description |
|------|-------------|
| `search` | Full-text search across files |
| `similarity_search` | Find similar sequences (MinHash) |
| `index_file` | Add file to search index |
| `remove_from_index` | Remove file from index |
| `get_index_stats` | Get indexing statistics |

---

### vibedna-synth

DNA synthesis optimization.

**URL**: `https://mcp.vibedna.vibecaas.com/synth`
**Port**: 8095

#### Tools

| Tool | Description |
|------|-------------|
| `optimize_sequence` | Optimize for synthesis platform |
| `check_constraints` | Check against platform constraints |
| `fragment_sequence` | Split into synthesizable fragments |
| `generate_order` | Generate synthesis order (FASTA) |

---

## Creating Custom Agents

### Extending BaseAgent

To create a custom agent, extend the `BaseAgent` class and implement the required abstract methods.

```python
from vibedna.agents import (
    BaseAgent,
    AgentConfig,
    AgentCapability,
    AgentTier,
    TaskRequest,
    TaskResponse,
    TaskStatus,
)

class MyCustomAgent(BaseAgent):
    """Custom agent for specialized operations."""

    def __init__(self, config: Optional[AgentConfig] = None):
        if config is None:
            config = AgentConfig(
                agent_id="my-custom-agent",
                version="1.0.0",
                tier=AgentTier.SPECIALIST,
                role="Custom Data Processor",
                description="Performs custom data processing operations",
                capabilities=[
                    AgentCapability(
                        name="custom_processing",
                        description="Process data with custom algorithm",
                    ),
                    AgentCapability(
                        name="data_transformation",
                        description="Transform data between formats",
                    ),
                ],
                tools=["custom_processor", "data_transformer"],
                mcp_connections=["vibedna-core"],
                max_concurrent_tasks=5,
                timeout_seconds=120.0,
            )

        super().__init__(config)
        # Initialize custom components
        self._processor = MyCustomProcessor()

    def get_system_prompt(self) -> str:
        """Get the agent's system prompt."""
        return """You are a custom VibeDNA agent for specialized data processing.

## Capabilities

1. Custom Processing - Apply custom algorithms to DNA data
2. Data Transformation - Convert between different data formats

## Protocol

1. Validate input data
2. Apply requested operation
3. Verify output quality
4. Return result with metadata

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC."""

    async def handle_task(self, request: TaskRequest) -> TaskResponse:
        """Handle an incoming task request."""
        self.logger.info(f"Handling task: {request.request_id}")

        action = request.parameters.get("action", "process")

        try:
            if action == "process":
                return await self._process_data(request)
            elif action == "transform":
                return await self._transform_data(request)
            else:
                return TaskResponse.failure(
                    request.request_id,
                    f"Unknown action: {action}",
                )
        except Exception as e:
            self.logger.error(f"Task failed: {e}")
            return TaskResponse.failure(request.request_id, str(e))

    async def _process_data(self, request: TaskRequest) -> TaskResponse:
        """Process data with custom algorithm."""
        data = request.parameters.get("data")
        options = request.parameters.get("options", {})

        result = self._processor.process(data, **options)

        return TaskResponse.success(
            request.request_id,
            {
                "processed_data": result,
                "metadata": {
                    "algorithm": "custom_v1",
                    "options_used": options,
                },
            },
        )

    async def _transform_data(self, request: TaskRequest) -> TaskResponse:
        """Transform data between formats."""
        data = request.parameters.get("data")
        source_format = request.parameters.get("source_format")
        target_format = request.parameters.get("target_format")

        result = self._processor.transform(data, source_format, target_format)

        return TaskResponse.success(
            request.request_id,
            {
                "transformed_data": result,
                "format": target_format,
            },
        )

    def _register_default_tools(self) -> None:
        """Register default tools for the agent."""
        from vibedna.agents.base.tool import FunctionTool

        self.register_tool(FunctionTool(
            self._processor.process,
            name="custom_processor",
            description="Process data with custom algorithm",
        ))
```

### Implementing handle_task

The `handle_task` method is the main entry point for task processing:

```python
async def handle_task(self, request: TaskRequest) -> TaskResponse:
    """
    Handle an incoming task request.

    Args:
        request: TaskRequest containing:
            - request_id: Unique identifier
            - operation: OperationType enum
            - parameters: Dict of task parameters
            - context: Additional context
            - priority: TaskPriority enum

    Returns:
        TaskResponse containing:
            - request_id: Same as request
            - status: TaskStatus enum
            - result: Operation result
            - error: Error message (if failed)
            - quality_report: Quality metrics
            - workflow_trace: Execution trace
    """
    # Validate input
    if not request.parameters.get("required_param"):
        return TaskResponse.failure(
            request.request_id,
            "Missing required parameter: required_param",
        )

    try:
        # Perform operation
        result = await self._do_operation(request.parameters)

        # Return success
        return TaskResponse.success(
            request.request_id,
            result,
            quality_report={"operation_valid": True},
        )
    except Exception as e:
        # Return failure
        return TaskResponse.failure(
            request.request_id,
            str(e),
        )
```

### Registering with Orchestrator

Register your custom agent with the MasterOrchestrator:

```python
from vibedna.agents import MasterOrchestrator
from my_agents import MyCustomAgent

async def setup_system():
    # Initialize orchestrator
    master = MasterOrchestrator()
    await master.initialize()

    # Create and initialize custom agent
    custom_agent = MyCustomAgent()
    await custom_agent.initialize()

    # Register with orchestrator
    master.register_agent(custom_agent)

    # Optionally update delegation matrix for new operation types
    master._delegation_matrix.operation_agents["custom_operation"] = {
        "primary": ["my-custom-agent"],
        "support": ["validation-agent"],
    }

    return master
```

### Creating Custom Tools

Tools are discrete capabilities that agents can invoke:

```python
from vibedna.agents.base.tool import (
    Tool,
    ToolDefinition,
    ToolParameter,
    ToolResult,
    ParameterType,
    FunctionTool,
    tool,
)

# Method 1: Using the @tool decorator
@tool(
    name="analyze_sequence",
    description="Analyze a DNA sequence for patterns",
)
async def analyze_sequence(
    sequence: str,
    pattern: str = "ATCG",
) -> Dict[str, Any]:
    """Analyze sequence for pattern occurrences."""
    count = sequence.count(pattern)
    return {
        "pattern": pattern,
        "occurrences": count,
        "sequence_length": len(sequence),
    }

# Method 2: Using FunctionTool
def my_function(data: bytes, option: str = "default") -> Dict[str, Any]:
    return {"processed": True}

tool = FunctionTool(
    my_function,
    name="my_tool",
    description="Process data with options",
    parameters=[
        ToolParameter(
            name="data",
            param_type=ParameterType.BYTES,
            description="Data to process",
            required=True,
        ),
        ToolParameter(
            name="option",
            param_type=ParameterType.STRING,
            description="Processing option",
            required=False,
            default="default",
        ),
    ],
)

# Method 3: Extending Tool class
class MyCustomTool(Tool):
    def __init__(self):
        definition = ToolDefinition(
            name="custom_tool",
            description="Perform custom operation",
            parameters=[
                ToolParameter(
                    name="input",
                    param_type=ParameterType.STRING,
                    description="Input data",
                    required=True,
                ),
            ],
        )
        super().__init__(definition)

    async def _execute(self, input: str) -> Any:
        # Implement tool logic
        return {"result": input.upper()}
```

### Agent Lifecycle

```python
# 1. Create agent
agent = MyCustomAgent()

# 2. Initialize (registers tools, connects to MCP servers)
await agent.initialize()

# 3. Process tasks
response = await agent.process_task(request)

# 4. Check health
health = agent.get_health()
print(f"Status: {health.status}")
print(f"Tasks completed: {health.tasks_completed}")

# 5. Shutdown gracefully
await agent.shutdown()
```

### Best Practices

1. **Always validate input** in `handle_task` before processing
2. **Use appropriate error handling** and return meaningful error messages
3. **Implement quality reports** for operations that produce data
4. **Log important events** using `self.logger`
5. **Respect timeouts** set in the configuration
6. **Add the VibeDNA footer** to all responses using `self.FOOTER`
7. **Register tools** in `_register_default_tools()` method
8. **Define capabilities** that accurately describe what the agent can do

---

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
