# Mirai IT Knowledge Systems - Architecture Design

## System Overview

AI-assisted internal IT knowledge system centered on Claude Code Workflow for ITSM knowledge management.

## Architecture Principles

1. **Claude Code Workflow as Core**: Central orchestration of all knowledge processing
2. **SubAgent Specialization**: Each SubAgent has a single, clear responsibility
3. **Hooks for Quality**: Non-intrusive validation and monitoring
4. **MCP for Integration**: Separation of concerns for memory, context, and plugins

## Directory Structure

```
Mirai-IT-Knowledge-Systems/
├── src/
│   ├── core/                    # Core workflow engine
│   │   ├── workflow.py         # Main workflow orchestrator
│   │   ├── knowledge_generator.py
│   │   └── itsm_classifier.py
│   ├── subagents/              # Claude Skills (SubAgents)
│   │   ├── architect.py
│   │   ├── knowledge_curator.py
│   │   ├── itsm_expert.py
│   │   ├── devops.py
│   │   ├── qa.py
│   │   └── documenter.py
│   ├── hooks/                  # Hooks for parallel control & quality
│   │   ├── pre_task.py
│   │   ├── on_change.py
│   │   ├── post_task.py
│   │   ├── duplicate_check.py
│   │   ├── deviation_check.py
│   │   └── auto_summary.py
│   ├── mcp/                    # MCP integrations
│   │   ├── context7_client.py
│   │   ├── claude_mem_client.py
│   │   ├── sqlite_client.py
│   │   └── github_client.py
│   ├── webui/                  # Web interface
│   │   ├── app.py
│   │   ├── routes/
│   │   ├── templates/
│   │   └── static/
│   └── utils/                  # Utilities
│       ├── text_processor.py
│       └── validators.py
├── data/
│   ├── knowledge/              # Markdown knowledge files
│   ├── logs/                   # System logs
│   └── uploads/                # Input files
├── db/
│   └── knowledge.db            # SQLite database
├── config/
│   ├── claude_config.yaml      # Claude Code configuration
│   ├── skills/                 # SubAgent skill definitions
│   └── hooks/                  # Hook configurations
├── docs/
│   └── requirements.md         # Requirements document
└── tests/
    ├── unit/
    └── integration/
```

## Component Details

### 1. Core Workflow Engine

**workflow.py**: Central orchestrator
- Input normalization
- SubAgent assignment
- Parallel execution control
- Result aggregation

**knowledge_generator.py**: Knowledge creation
- Summary generation (technical & non-technical)
- Insight extraction
- Relationship management

**itsm_classifier.py**: ITSM categorization
- Incident / Problem / Change / Release / Request classification
- Tag management
- Relationship linking

### 2. SubAgents (Claude Skills)

Each SubAgent implements a specific role:

**Architect**
- Overall design coherence
- Decision control
- Conflict resolution

**KnowledgeCurator**
- Knowledge organization
- Classification
- Metadata management

**ITSM-Expert**
- ITSM compliance validation
- Deviation detection
- Best practice enforcement

**DevOps**
- Technical analysis
- Automation perspective
- Infrastructure insights

**QA**
- Quality assurance
- Duplicate detection
- Validation

**Documenter**
- Output formatting
- Summary generation
- Multi-format export

### 3. Hooks Mechanism

**Parallel Control Hooks:**
- `pre-task`: SubAgent assignment logic
- `on-change`: Impact & deviation analysis
- `post-task`: Integrated review

**Quality Assurance Hooks:**
- `duplicate-check`: Knowledge duplication detection
- `deviation-check`: ITSM principle deviation warnings
- `auto-summary`: 3-line summary generation

**Principles:**
- Hooks do not auto-correct
- Humans make final decisions
- Focus on warning & visualization

### 4. MCP Integration Layer

**Context7**: Technical context understanding
**Claude-Mem**: Design philosophy & decision memory
**mem-search**: Similar knowledge search
**sqlite**: Metadata database
**filesystem**: Original files & logs storage
**GitHub**: History & audit trail

### 5. WebUI

**Features:**
- Natural language knowledge search
- Knowledge registration
- ITSM tag filtering
- Related knowledge display
- Incident → Knowledge promotion

**Tech Stack:**
- Backend: Python (Flask/FastAPI)
- Frontend: HTML/CSS/JavaScript (Alpine.js)
- Database: SQLite

## Data Flow

```
Input (Logs/Docs/Reports)
    ↓
Input Normalization (workflow.py)
    ↓
ITSM Classification (itsm_classifier.py)
    ↓
[pre-task Hook] → SubAgent Assignment
    ↓
Parallel SubAgent Processing
  ├── Architect: Design coherence
  ├── KnowledgeCurator: Organization
  ├── ITSM-Expert: Compliance check
  ├── DevOps: Technical analysis
  ├── QA: Quality validation
  └── Documenter: Format output
    ↓
[on-change Hook] → Impact analysis
    ↓
Result Aggregation
    ↓
[post-task Hook] → Integrated review
[duplicate-check Hook] → Duplication check
[deviation-check Hook] → Deviation warning
[auto-summary Hook] → Summary generation
    ↓
Persistence
  ├── SQLite (metadata)
  └── Markdown files (knowledge)
    ↓
WebUI Display / API Access
```

## Database Schema

### knowledge_entries table
- id: Primary key
- title: Knowledge title
- itsm_type: Incident/Problem/Change/Release/Request
- summary_technical: Technical summary
- summary_non_technical: Non-technical summary
- insights: Extracted insights (JSON)
- tags: Tags (JSON)
- related_ids: Related knowledge IDs (JSON)
- created_at: Timestamp
- updated_at: Timestamp
- markdown_path: Path to markdown file

### relationships table
- id: Primary key
- source_id: Source knowledge ID
- target_id: Target knowledge ID
- relationship_type: Incident→Problem, Problem→Change, etc.
- created_at: Timestamp

### itsm_tags table
- id: Primary key
- tag_name: Tag name
- itsm_category: ITSM category
- description: Tag description

## Non-Functional Requirements

### Reproducibility
- Same input conditions produce equivalent knowledge
- Deterministic workflow execution

### Traceability
- All decisions are logged with rationale
- Audit trail in GitHub

### Availability
- Stable operation during business hours
- Graceful degradation

### Maintainability
- Modular architecture
- Easy configuration changes
- Clear separation of concerns

## Implementation Phases

### Phase 1: Foundation
1. Directory structure
2. Database schema
3. Core workflow engine
4. Basic ITSM classification

### Phase 2: SubAgents
1. Implement 6 SubAgents
2. Parallel execution framework
3. Result aggregation

### Phase 3: Hooks & Quality
1. Pre/on/post task hooks
2. Quality assurance hooks
3. Deviation detection

### Phase 4: MCP Integration
1. Context7 integration
2. Claude-Mem integration
3. SQLite operations
4. GitHub integration

### Phase 5: WebUI
1. Backend API
2. Search functionality
3. Knowledge management UI
4. ITSM filtering

### Phase 6: Testing & Documentation
1. Unit tests
2. Integration tests
3. User documentation
4. Operational procedures

## Configuration Management

### claude_config.yaml
```yaml
workflow:
  parallel_execution: true
  max_subagents: 6
  timeout: 300

subagents:
  - name: architect
    priority: high
    role: design_coherence
  - name: knowledge_curator
    priority: high
    role: organization
  - name: itsm_expert
    priority: high
    role: compliance
  - name: devops
    priority: medium
    role: technical_analysis
  - name: qa
    priority: high
    role: quality_validation
  - name: documenter
    priority: medium
    role: formatting

hooks:
  pre_task:
    enabled: true
    script: config/hooks/pre_task.py
  on_change:
    enabled: true
    script: config/hooks/on_change.py
  post_task:
    enabled: true
    script: config/hooks/post_task.py
  duplicate_check:
    enabled: true
    threshold: 0.85
  deviation_check:
    enabled: true
    itsm_rules: config/itsm_rules.yaml
  auto_summary:
    enabled: true
    max_lines: 3

mcp:
  context7:
    enabled: true
  claude_mem:
    enabled: true
  sqlite:
    db_path: db/knowledge.db
  github:
    enabled: false  # Optional for audit
```

## Security Considerations

- Internal network only (no domain authentication required)
- Input validation
- SQL injection prevention
- Path traversal protection
- Rate limiting on WebUI

## Monitoring & Logging

- All workflow executions logged
- SubAgent activities tracked
- Hook execution results
- Performance metrics
- Error tracking

## Future Enhancements

- Multi-language support
- Advanced analytics dashboard
- Integration with ticketing systems
- ML-based knowledge recommendation
- Automated knowledge lifecycle management
