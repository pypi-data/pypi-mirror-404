-- VibeDNA Database Initialization
-- © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- Workflow State Tables
-- =============================================================================

CREATE TABLE IF NOT EXISTS workflow_states (
    workflow_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL DEFAULT '1.0.0',
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    variables JSONB DEFAULT '{}',
    steps JSONB DEFAULT '{}',
    outputs JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_workflow_states_status ON workflow_states(status);
CREATE INDEX idx_workflow_states_created_at ON workflow_states(created_at);
CREATE INDEX idx_workflow_states_name ON workflow_states(workflow_name);

-- =============================================================================
-- Task Queue Tables
-- =============================================================================

CREATE TABLE IF NOT EXISTS task_queue (
    task_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_id VARCHAR(255) UNIQUE NOT NULL,
    task_type VARCHAR(255) NOT NULL,
    agent_id VARCHAR(255),
    priority INTEGER DEFAULT 2,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    parameters JSONB DEFAULT '{}',
    result JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    timeout_at TIMESTAMP WITH TIME ZONE,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3
);

CREATE INDEX idx_task_queue_status ON task_queue(status);
CREATE INDEX idx_task_queue_priority ON task_queue(priority DESC);
CREATE INDEX idx_task_queue_agent ON task_queue(agent_id);
CREATE INDEX idx_task_queue_created ON task_queue(created_at);

-- =============================================================================
-- Agent Registry Tables
-- =============================================================================

CREATE TABLE IF NOT EXISTS agent_registry (
    agent_id VARCHAR(255) PRIMARY KEY,
    tier VARCHAR(50) NOT NULL,
    role VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'offline',
    host VARCHAR(255),
    port INTEGER,
    capabilities JSONB DEFAULT '[]',
    last_heartbeat TIMESTAMP WITH TIME ZONE,
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_agent_registry_tier ON agent_registry(tier);
CREATE INDEX idx_agent_registry_status ON agent_registry(status);

-- =============================================================================
-- Resource Allocation Tables
-- =============================================================================

CREATE TABLE IF NOT EXISTS resource_allocations (
    allocation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES task_queue(task_id),
    agent_id VARCHAR(255) REFERENCES agent_registry(agent_id),
    memory_bytes BIGINT DEFAULT 0,
    cpu_cores INTEGER DEFAULT 1,
    priority INTEGER DEFAULT 2,
    allocated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    released_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_allocations_agent ON resource_allocations(agent_id);
CREATE INDEX idx_allocations_task ON resource_allocations(task_id);
CREATE INDEX idx_allocations_active ON resource_allocations(released_at) WHERE released_at IS NULL;

-- =============================================================================
-- DNA Storage Tables
-- =============================================================================

CREATE TABLE IF NOT EXISTS dna_sequences (
    sequence_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255),
    sequence TEXT NOT NULL,
    length INTEGER NOT NULL,
    gc_content FLOAT,
    encoding_scheme VARCHAR(50),
    checksum VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_dna_sequences_name ON dna_sequences(name);
CREATE INDEX idx_dna_sequences_scheme ON dna_sequences(encoding_scheme);
CREATE INDEX idx_dna_sequences_checksum ON dna_sequences(checksum);

-- =============================================================================
-- Audit Log Tables
-- =============================================================================

CREATE TABLE IF NOT EXISTS audit_log (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(255),
    action VARCHAR(255) NOT NULL,
    resource VARCHAR(255),
    allowed BOOLEAN DEFAULT TRUE,
    reason TEXT,
    ip_address INET,
    user_agent TEXT,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX idx_audit_log_user ON audit_log(user_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);

-- =============================================================================
-- Metrics Tables
-- =============================================================================

CREATE TABLE IF NOT EXISTS metrics (
    metric_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(255) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    value FLOAT NOT NULL,
    unit VARCHAR(50),
    tags JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    agent_id VARCHAR(255)
);

CREATE INDEX idx_metrics_name ON metrics(metric_name);
CREATE INDEX idx_metrics_timestamp ON metrics(timestamp);
CREATE INDEX idx_metrics_agent ON metrics(agent_id);

-- Partitioning for metrics (daily partitions)
-- Note: In production, implement proper partitioning strategy

-- =============================================================================
-- Checkpoint Tables
-- =============================================================================

CREATE TABLE IF NOT EXISTS workflow_checkpoints (
    checkpoint_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID REFERENCES workflow_states(workflow_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    current_step_id VARCHAR(255),
    completed_steps JSONB DEFAULT '[]',
    variables JSONB DEFAULT '{}',
    steps JSONB DEFAULT '{}',
    outputs JSONB DEFAULT '{}'
);

CREATE INDEX idx_checkpoints_workflow ON workflow_checkpoints(workflow_id);
CREATE INDEX idx_checkpoints_created ON workflow_checkpoints(created_at);

-- =============================================================================
-- Functions
-- =============================================================================

-- Function to update timestamp on row modification
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for workflow_states
CREATE TRIGGER update_workflow_states_updated_at
    BEFORE UPDATE ON workflow_states
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- Initial Data
-- =============================================================================

-- Insert default agents
INSERT INTO agent_registry (agent_id, tier, role, version, status) VALUES
    ('vibedna-master-orchestrator', 'orchestration', 'Master Orchestrator', '1.0.0', 'offline'),
    ('vibedna-workflow-orchestrator', 'orchestration', 'Workflow Orchestrator', '1.0.0', 'offline'),
    ('vibedna-resource-orchestrator', 'orchestration', 'Resource Orchestrator', '1.0.0', 'offline'),
    ('vibedna-encoder-agent', 'specialist', 'DNA Encoder', '1.0.0', 'offline'),
    ('vibedna-decoder-agent', 'specialist', 'DNA Decoder', '1.0.0', 'offline'),
    ('vibedna-error-correction-agent', 'specialist', 'Error Correction', '1.0.0', 'offline'),
    ('vibedna-compute-agent', 'specialist', 'DNA Compute', '1.0.0', 'offline'),
    ('vibedna-filesystem-agent', 'specialist', 'File System', '1.0.0', 'offline'),
    ('vibedna-validation-agent', 'specialist', 'Validation', '1.0.0', 'offline'),
    ('vibedna-visualization-agent', 'specialist', 'Visualization', '1.0.0', 'offline'),
    ('vibedna-synthesis-agent', 'specialist', 'Synthesis', '1.0.0', 'offline'),
    ('vibedna-index-agent', 'support', 'Indexing', '1.0.0', 'offline'),
    ('vibedna-metrics-agent', 'support', 'Metrics', '1.0.0', 'offline'),
    ('vibedna-logging-agent', 'support', 'Logging', '1.0.0', 'offline'),
    ('vibedna-docs-agent', 'support', 'Documentation', '1.0.0', 'offline'),
    ('vibedna-security-agent', 'support', 'Security', '1.0.0', 'offline')
ON CONFLICT (agent_id) DO NOTHING;

-- © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
