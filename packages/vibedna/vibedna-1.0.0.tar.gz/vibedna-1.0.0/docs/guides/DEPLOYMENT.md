# VibeDNA Deployment Guide

This guide provides comprehensive instructions for deploying the VibeDNA Agent Orchestration System across different environments, from local development to production Kubernetes clusters.

---

## Table of Contents

1. [Deployment Overview](#1-deployment-overview)
2. [Local Development Setup](#2-local-development-setup)
3. [Docker Deployment](#3-docker-deployment)
4. [Full Stack Deployment](#4-full-stack-deployment-docker-compose)
5. [Configuration](#5-configuration)
6. [Scaling](#6-scaling)
7. [Monitoring and Health Checks](#7-monitoring-and-health-checks)
8. [Production Considerations](#8-production-considerations)
9. [Kubernetes Deployment](#9-kubernetes-deployment-overview)

---

## 1. Deployment Overview

### Deployment Options

VibeDNA supports multiple deployment strategies to accommodate various use cases:

| Deployment Type | Use Case | Complexity |
|----------------|----------|------------|
| **Local Python** | Development, testing | Low |
| **Single Container** | Simple deployments, CI/CD | Low |
| **Docker Compose** | Development, staging | Medium |
| **Kubernetes** | Production, high availability | High |

### Architecture Summary

The VibeDNA system consists of multiple tiers of services:

```
                    ┌─────────────────────┐
                    │    API Gateway      │
                    │    (Port 8000)      │
                    └──────────┬──────────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
   ┌────────▼────────┐  ┌─────▼─────┐  ┌────────▼────────┐
   │     Master      │  │ Workflow  │  │   Resource      │
   │  Orchestrator   │  │Orchestrator│  │  Orchestrator   │
   │   (Port 8200)   │  │(Port 8201)│  │  (Port 8202)    │
   └────────┬────────┘  └─────┬─────┘  └────────┬────────┘
            │                 │                  │
            └─────────────────┼──────────────────┘
                              │
    ┌─────────────────────────┼─────────────────────────┐
    │          Specialist Agents (Ports 8300-8307)      │
    │  encoder, decoder, error-correction, compute,     │
    │  filesystem, validation, visualization, synthesis │
    └─────────────────────────┼─────────────────────────┘
                              │
    ┌─────────────────────────┼─────────────────────────┐
    │          Support Agents (Ports 8400-8404)         │
    │  index, metrics, logging, docs, security          │
    └─────────────────────────┼─────────────────────────┘
                              │
    ┌─────────────────────────┼─────────────────────────┐
    │           MCP Servers (Ports 8100-8105)           │
    │    core, fs, compute, monitor, search, synth      │
    └─────────────────────────┼─────────────────────────┘
                              │
    ┌─────────────────────────┼─────────────────────────┐
    │          Infrastructure Services                   │
    │  Redis (6379), PostgreSQL (5432), ES (9200)       │
    └───────────────────────────────────────────────────┘
```

---

## 2. Local Development Setup

### Prerequisites

- **Python 3.10+** (3.11 recommended)
- **Git**
- **Docker and Docker Compose** (for containerized deployment)
- **pip** (Python package manager)

### Clone and Install

```bash
# Clone the repository
git clone https://github.com/ttracx/VibeDNA.git
cd VibeDNA

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# For development with all extras
pip install -e ".[dev]"
```

### Running Locally

#### Start the API Server

```bash
# Using the CLI
vibedna

# Or directly with uvicorn
uvicorn vibedna.api.rest_server:app --host 0.0.0.0 --port 8000 --reload
```

#### Verify Installation

```bash
# Check CLI is working
vibedna --help

# Test the API
curl http://localhost:8000/
```

---

## 3. Docker Deployment

### Single Container Deployment

Build and run the main VibeDNA API container:

```bash
# Build the image
docker build -t vibedna:latest -f Dockerfile .

# Run the container
docker run -d \
  --name vibedna-api \
  -p 8000:8000 \
  -e VIBEDNA_LOG_LEVEL=INFO \
  vibedna:latest
```

**Dockerfile Reference:**

```dockerfile
# VibeDNA Docker Image
FROM python:3.11-slim

LABEL maintainer="NeuralQuantum.ai <contact@neuralquantum.ai>"
LABEL description="VibeDNA - Binary to DNA Encoding System"
LABEL version="1.0.0"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY vibedna/ ./vibedna/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

# Run API server
CMD ["uvicorn", "vibedna.api.rest_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Using docker-compose.yml

For development with the full stack:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Environment Variables

Key environment variables for Docker deployment:

| Variable | Description | Default |
|----------|-------------|---------|
| `VIBEDNA_LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `VIBEDNA_REDIS_URL` | Redis connection URL | `redis://redis:6379/0` |
| `VIBEDNA_POSTGRES_URL` | PostgreSQL connection URL | (see .env.example) |
| `VIBEDNA_ES_URL` | Elasticsearch URL | `http://elasticsearch:9200` |

---

## 4. Full Stack Deployment (docker-compose)

### Infrastructure Services

The following infrastructure services are required:

#### Redis (Message Queue and Caching)

```yaml
redis:
  image: redis:7-alpine
  container_name: vibedna-redis
  ports:
    - "6379:6379"
  volumes:
    - redis-data:/data
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 10s
    timeout: 5s
    retries: 5
  networks:
    - vibedna-network
```

#### PostgreSQL (Workflow State and Task Queue)

```yaml
postgres:
  image: postgres:15-alpine
  container_name: vibedna-postgres
  environment:
    POSTGRES_USER: vibedna
    POSTGRES_PASSWORD: vibedna
    POSTGRES_DB: vibedna
  ports:
    - "5432:5432"
  volumes:
    - postgres-data:/var/lib/postgresql/data
    - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql:ro
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U vibedna"]
    interval: 10s
    timeout: 5s
    retries: 5
  networks:
    - vibedna-network
```

#### Elasticsearch (Search and Indexing)

```yaml
elasticsearch:
  image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
  container_name: vibedna-elasticsearch
  environment:
    - discovery.type=single-node
    - xpack.security.enabled=false
    - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
  ports:
    - "9200:9200"
  volumes:
    - elasticsearch-data:/usr/share/elasticsearch/data
  healthcheck:
    test: ["CMD-SHELL", "curl -s http://localhost:9200/_cluster/health | grep -q '\"status\":\"green\"\\|\"status\":\"yellow\"'"]
    interval: 30s
    timeout: 10s
    retries: 5
  networks:
    - vibedna-network
```

### MCP Servers

MCP (Model Context Protocol) servers provide specialized capabilities:

| Server | Port | Purpose |
|--------|------|---------|
| `mcp-core` | 8100 | Core DNA encoding/decoding tools |
| `mcp-fs` | 8101 | File system operations |
| `mcp-compute` | 8102 | DNA computation operations |
| `mcp-monitor` | 8103 | System monitoring |
| `mcp-search` | 8104 | Search and indexing |
| `mcp-synth` | 8105 | DNA synthesis planning |

**Example MCP Server Configuration:**

```yaml
mcp-core:
  build:
    context: .
    dockerfile: Dockerfile.mcp
  container_name: vibedna-mcp-core
  environment:
    VIBEDNA_LOG_LEVEL: ${LOG_LEVEL:-INFO}
    VIBEDNA_REDIS_URL: redis://redis:6379/0
    MCP_SERVER_TYPE: core
    MCP_SERVER_PORT: 8100
  ports:
    - "8100:8100"
  healthcheck:
    test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8100/health')"]
    interval: 30s
    timeout: 10s
    retries: 3
  networks:
    - vibedna-network
  depends_on:
    redis:
      condition: service_healthy
```

### Agent Containers

#### Orchestration Tier

```yaml
master-orchestrator:
  build:
    context: .
    dockerfile: Dockerfile.agent
  container_name: vibedna-master-orchestrator
  environment:
    VIBEDNA_LOG_LEVEL: ${LOG_LEVEL:-INFO}
    VIBEDNA_REDIS_URL: redis://redis:6379/0
    VIBEDNA_POSTGRES_URL: postgresql://vibedna:vibedna@postgres:5432/vibedna
    AGENT_TYPE: master-orchestrator
    AGENT_PORT: 8200
  ports:
    - "8200:8200"
  depends_on:
    redis:
      condition: service_healthy
    postgres:
      condition: service_healthy
    mcp-core:
      condition: service_healthy
  healthcheck:
    test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8200/health')"]
    interval: 30s
    timeout: 10s
    retries: 3
  networks:
    - vibedna-network
```

#### Specialist Tier (with Replicas)

```yaml
encoder-agent:
  build:
    context: .
    dockerfile: Dockerfile.agent
  container_name: vibedna-encoder-agent
  environment:
    AGENT_TYPE: encoder
    AGENT_PORT: 8300
  ports:
    - "8300:8300"
  deploy:
    replicas: 2
    resources:
      limits:
        memory: 512M
  depends_on:
    mcp-core:
      condition: service_healthy
  networks:
    - vibedna-network
```

### API Gateway

```yaml
api-gateway:
  build:
    context: .
    dockerfile: Dockerfile
  container_name: vibedna-api-gateway
  environment:
    VIBEDNA_LOG_LEVEL: ${LOG_LEVEL:-INFO}
    VIBEDNA_REDIS_URL: redis://redis:6379/0
    MASTER_ORCHESTRATOR_URL: http://master-orchestrator:8200
  ports:
    - "8000:8000"
  depends_on:
    master-orchestrator:
      condition: service_healthy
  healthcheck:
    test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/')"]
    interval: 30s
    timeout: 10s
    retries: 3
  networks:
    - vibedna-network
```

### Start Full Stack

```bash
# Start all services with build
docker-compose up -d --build

# Check status
docker-compose ps

# View combined logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f api-gateway
```

---

## 5. Configuration

### Environment Variables Reference

#### General Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Application log level | `INFO` |
| `VIBEDNA_LOG_LEVEL` | VibeDNA-specific log level | `INFO` |

#### Database Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_USER` | PostgreSQL username | `vibedna` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `vibedna` |
| `POSTGRES_DB` | PostgreSQL database name | `vibedna` |
| `VIBEDNA_POSTGRES_URL` | Full PostgreSQL connection URL | - |

#### Redis Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection URL | `redis://redis:6379/0` |
| `VIBEDNA_REDIS_URL` | VibeDNA Redis URL | `redis://redis:6379/0` |

#### Elasticsearch Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `VIBEDNA_ES_URL` | Elasticsearch URL | `http://elasticsearch:9200` |
| `ES_JAVA_OPTS` | Elasticsearch JVM options | `-Xms512m -Xmx512m` |

#### API Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `API_HOST` | API server bind host | `0.0.0.0` |
| `API_PORT` | API server port | `8000` |

#### Agent Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `AGENT_TYPE` | Agent type identifier | `encoder` |
| `AGENT_PORT` | Agent HTTP port | `8300` |
| `AGENT_TIMEOUT` | Operation timeout (seconds) | `300` |
| `AGENT_MAX_CONCURRENT_TASKS` | Max concurrent tasks | `10` |

#### MCP Server Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_SERVER_TYPE` | MCP server type | `core` |
| `MCP_SERVER_PORT` | MCP server port | `8100` |
| `MCP_TIMEOUT` | Message timeout (seconds) | `30` |

#### Resource Limits

| Variable | Description | Default |
|----------|-------------|---------|
| `MAX_MEMORY_PER_TASK` | Max memory per task (bytes) | `536870912` (512MB) |
| `DEFAULT_CPU_CORES` | Default CPU cores per task | `1` |

### .env File Setup

Create a `.env` file from the example:

```bash
cp .env.example .env
```

**Example .env file:**

```bash
# VibeDNA Environment Configuration

# =============================================================================
# General Settings
# =============================================================================

# Log level: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO

# =============================================================================
# Database Configuration
# =============================================================================

POSTGRES_USER=vibedna
POSTGRES_PASSWORD=vibedna
POSTGRES_DB=vibedna

# =============================================================================
# Redis Configuration
# =============================================================================

REDIS_URL=redis://redis:6379/0

# =============================================================================
# Elasticsearch Configuration
# =============================================================================

ES_JAVA_OPTS=-Xms512m -Xmx512m

# =============================================================================
# API Configuration
# =============================================================================

API_HOST=0.0.0.0
API_PORT=8000

# =============================================================================
# Agent Configuration
# =============================================================================

# Default timeout for agent operations (seconds)
AGENT_TIMEOUT=300

# Maximum concurrent tasks per agent
AGENT_MAX_CONCURRENT_TASKS=10

# =============================================================================
# MCP Server Configuration
# =============================================================================

# MCP message timeout (seconds)
MCP_TIMEOUT=30

# =============================================================================
# Resource Limits
# =============================================================================

# Maximum memory allocation per task (bytes)
MAX_MEMORY_PER_TASK=536870912

# Default CPU cores per task
DEFAULT_CPU_CORES=1
```

### Service Ports

| Service | Port | Protocol |
|---------|------|----------|
| API Gateway | 8000 | HTTP |
| Redis | 6379 | Redis |
| PostgreSQL | 5432 | PostgreSQL |
| Elasticsearch | 9200 | HTTP |
| MCP Core | 8100 | HTTP/JSON-RPC |
| MCP FS | 8101 | HTTP/JSON-RPC |
| MCP Compute | 8102 | HTTP/JSON-RPC |
| MCP Monitor | 8103 | HTTP/JSON-RPC |
| MCP Search | 8104 | HTTP/JSON-RPC |
| MCP Synth | 8105 | HTTP/JSON-RPC |
| Master Orchestrator | 8200 | HTTP |
| Workflow Orchestrator | 8201 | HTTP |
| Resource Orchestrator | 8202 | HTTP |
| Encoder Agent | 8300 | HTTP |
| Decoder Agent | 8301 | HTTP |
| Error Correction Agent | 8302 | HTTP |
| Compute Agent | 8303 | HTTP |
| Filesystem Agent | 8304 | HTTP |
| Validation Agent | 8305 | HTTP |
| Visualization Agent | 8306 | HTTP |
| Synthesis Agent | 8307 | HTTP |
| Index Agent | 8400 | HTTP |
| Metrics Agent | 8401 | HTTP |
| Logging Agent | 8402 | HTTP |
| Docs Agent | 8403 | HTTP |
| Security Agent | 8404 | HTTP |

---

## 6. Scaling

### Horizontal Scaling with Replicas

Use Docker Compose deploy configuration for horizontal scaling:

```yaml
encoder-agent:
  build:
    context: .
    dockerfile: Dockerfile.agent
  environment:
    AGENT_TYPE: encoder
    AGENT_PORT: 8300
  deploy:
    replicas: 4
    resources:
      limits:
        memory: 512M
        cpus: '0.5'
      reservations:
        memory: 256M
        cpus: '0.25'
```

**Scale specific services dynamically:**

```bash
# Scale encoder agents to 5 replicas
docker-compose up -d --scale encoder-agent=5

# Scale decoder agents to 3 replicas
docker-compose up -d --scale decoder-agent=3
```

### Load Balancing

For production deployments, add a load balancer:

```yaml
nginx:
  image: nginx:alpine
  container_name: vibedna-lb
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf:ro
    - ./ssl:/etc/nginx/ssl:ro
  depends_on:
    - api-gateway
  networks:
    - vibedna-network
```

**Example nginx.conf:**

```nginx
upstream vibedna_api {
    least_conn;
    server api-gateway:8000;
}

upstream encoder_pool {
    least_conn;
    server encoder-agent-1:8300;
    server encoder-agent-2:8300;
    server encoder-agent-3:8300;
}

server {
    listen 80;
    server_name vibedna.local;

    location / {
        proxy_pass http://vibedna_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Resource Limits

Configure resource limits for production stability:

```yaml
compute-agent:
  deploy:
    replicas: 2
    resources:
      limits:
        memory: 1G
        cpus: '1.0'
      reservations:
        memory: 512M
        cpus: '0.5'

error-correction-agent:
  deploy:
    resources:
      limits:
        memory: 1G
        cpus: '1.0'
```

---

## 7. Monitoring and Health Checks

### Health Endpoints

All services expose a `/health` endpoint:

```bash
# Check API Gateway health
curl http://localhost:8000/

# Check agent health
curl http://localhost:8200/health

# Check MCP server health
curl http://localhost:8100/health
```

**Health response format:**

```json
{
  "status": "healthy",
  "agent": "vibedna-master-orchestrator"
}
```

**Additional endpoints for MCP servers:**

```bash
# List available tools
curl http://localhost:8100/tools

# List available resources
curl http://localhost:8100/resources

# Get server info
curl http://localhost:8100/info
```

### Metrics Collection

The Metrics Agent (port 8401) collects system-wide metrics:

```bash
# Query metrics
curl http://localhost:8401/health
```

**PostgreSQL metrics table schema:**

```sql
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
```

**Integrate with Prometheus:**

```yaml
prometheus:
  image: prom/prometheus:latest
  container_name: vibedna-prometheus
  ports:
    - "9090:9090"
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
  networks:
    - vibedna-network
```

### Log Aggregation

The Logging Agent (port 8402) handles centralized logging:

```yaml
logging-agent:
  build:
    context: .
    dockerfile: Dockerfile.agent
  container_name: vibedna-logging-agent
  environment:
    AGENT_TYPE: logging
    AGENT_PORT: 8402
  volumes:
    - logs-data:/var/log/vibedna
  networks:
    - vibedna-network
```

**Integrate with ELK Stack:**

```yaml
kibana:
  image: docker.elastic.co/kibana/kibana:8.11.0
  container_name: vibedna-kibana
  environment:
    ELASTICSEARCH_HOSTS: http://elasticsearch:9200
  ports:
    - "5601:5601"
  depends_on:
    - elasticsearch
  networks:
    - vibedna-network
```

---

## 8. Production Considerations

### Security Hardening

#### Run as Non-Root User

The agent and MCP Dockerfiles already implement this:

```dockerfile
# Create non-root user for security
RUN useradd -m -u 1000 vibedna && \
    chown -R vibedna:vibedna /app
USER vibedna
```

#### Network Isolation

Use Docker networks to isolate services:

```yaml
networks:
  vibedna-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
```

#### Environment Variables Security

- Never commit `.env` files with production credentials
- Use Docker secrets or external secret management (Vault, AWS Secrets Manager)
- Rotate database passwords regularly

```bash
# Using Docker secrets
echo "secure_password" | docker secret create postgres_password -

# Reference in compose
services:
  postgres:
    secrets:
      - postgres_password
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
```

### SSL/TLS Setup

#### Generate Certificates

```bash
# Generate self-signed certificate for development
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/vibedna.key \
  -out ssl/vibedna.crt \
  -subj "/CN=vibedna.local"
```

#### Configure NGINX with SSL

```nginx
server {
    listen 443 ssl http2;
    server_name vibedna.local;

    ssl_certificate /etc/nginx/ssl/vibedna.crt;
    ssl_certificate_key /etc/nginx/ssl/vibedna.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;

    location / {
        proxy_pass http://vibedna_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name vibedna.local;
    return 301 https://$server_name$request_uri;
}
```

### Backup Strategies

#### PostgreSQL Backup

```bash
# Manual backup
docker exec vibedna-postgres pg_dump -U vibedna vibedna > backup.sql

# Automated backup script
#!/bin/bash
BACKUP_DIR=/backups/postgres
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
docker exec vibedna-postgres pg_dump -U vibedna vibedna | gzip > $BACKUP_DIR/vibedna_$TIMESTAMP.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
```

#### Redis Backup

```bash
# Trigger RDB snapshot
docker exec vibedna-redis redis-cli BGSAVE

# Copy RDB file
docker cp vibedna-redis:/data/dump.rdb ./backups/redis/
```

#### Volume Backup

```bash
# Backup all volumes
docker run --rm \
  -v vibedna_postgres-data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/postgres-data.tar.gz /data
```

---

## 9. Kubernetes Deployment (Overview)

### Converting to K8s Manifests

#### Deployment Example

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vibedna-api-gateway
  labels:
    app: vibedna
    component: api-gateway
spec:
  replicas: 2
  selector:
    matchLabels:
      app: vibedna
      component: api-gateway
  template:
    metadata:
      labels:
        app: vibedna
        component: api-gateway
    spec:
      containers:
      - name: api-gateway
        image: vibedna:latest
        ports:
        - containerPort: 8000
        env:
        - name: VIBEDNA_LOG_LEVEL
          value: "INFO"
        - name: VIBEDNA_REDIS_URL
          valueFrom:
            secretKeyRef:
              name: vibedna-secrets
              key: redis-url
        resources:
          limits:
            memory: "512Mi"
            cpu: "500m"
          requests:
            memory: "256Mi"
            cpu: "250m"
        livenessProbe:
          httpGet:
            path: /
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
```

#### Service Example

```yaml
apiVersion: v1
kind: Service
metadata:
  name: vibedna-api-gateway
spec:
  selector:
    app: vibedna
    component: api-gateway
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
---
apiVersion: v1
kind: Service
metadata:
  name: vibedna-api-gateway-lb
spec:
  selector:
    app: vibedna
    component: api-gateway
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

#### ConfigMap and Secrets

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: vibedna-config
data:
  LOG_LEVEL: "INFO"
  API_PORT: "8000"
  AGENT_TIMEOUT: "300"
---
apiVersion: v1
kind: Secret
metadata:
  name: vibedna-secrets
type: Opaque
stringData:
  redis-url: "redis://redis:6379/0"
  postgres-url: "postgresql://vibedna:password@postgres:5432/vibedna"
```

### Helm Chart Considerations

For production Kubernetes deployments, consider creating a Helm chart with the following structure:

```
vibedna-helm/
├── Chart.yaml
├── values.yaml
├── templates/
│   ├── _helpers.tpl
│   ├── configmap.yaml
│   ├── secrets.yaml
│   ├── deployment-api.yaml
│   ├── deployment-agents.yaml
│   ├── deployment-mcp.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── hpa.yaml
│   └── pdb.yaml
└── charts/
    ├── redis/
    ├── postgresql/
    └── elasticsearch/
```

**Key Helm values.yaml considerations:**

```yaml
# values.yaml
replicaCount:
  apiGateway: 2
  encoderAgent: 4
  decoderAgent: 4
  masterOrchestrator: 1

image:
  repository: vibedna
  tag: latest
  pullPolicy: IfNotPresent

resources:
  apiGateway:
    limits:
      cpu: 500m
      memory: 512Mi
    requests:
      cpu: 250m
      memory: 256Mi

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: api.vibedna.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: vibedna-tls
      hosts:
        - api.vibedna.example.com

postgresql:
  enabled: true
  auth:
    username: vibedna
    database: vibedna

redis:
  enabled: true
  architecture: standalone

elasticsearch:
  enabled: true
  replicas: 1
```

---

## Quick Reference Commands

```bash
# Start full stack
docker-compose up -d

# Stop full stack
docker-compose down

# View logs
docker-compose logs -f [service_name]

# Scale a service
docker-compose up -d --scale encoder-agent=5

# Rebuild and restart
docker-compose up -d --build

# Check service health
curl http://localhost:8000/
curl http://localhost:8200/health

# Database backup
docker exec vibedna-postgres pg_dump -U vibedna vibedna > backup.sql

# Enter container shell
docker exec -it vibedna-api-gateway /bin/bash
```

---

(c) 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
