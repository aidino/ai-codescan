# 🤖 AI CodeScan - System Workflow Documentation

**Version**: 1.0  
**Last Updated**: May 31, 2024  
**Status**: Phase 1 Complete

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Authentication Workflow](#authentication-workflow)
3. [Repository Analysis Workflow](#repository-analysis-workflow)
4. [Session Management Workflow](#session-management-workflow)
5. [History Management Workflow](#history-management-workflow)
6. [CKG Operations Workflow](#ckg-operations-workflow)
7. [Code Analysis Workflow](#code-analysis-workflow)
8. [LLM Services Workflow](#llm-services-workflow)
9. [Synthesis & Reporting Workflow](#synthesis--reporting-workflow)
10. [Data Structures & Models](#data-structures--models)
11. [File Organization](#file-organization)

---

## Overview

AI CodeScan sử dụng **multi-agent architecture** với **LangGraph orchestration** để phân tích code repositories. System bao gồm 6 major agent teams với clear data flow và responsibility separation.

### **High-Level Architecture**
```
User Input (Web UI) 
    ↓
Authentication Layer
    ↓
Session Management
    ↓
Multi-Agent Orchestrator (LangGraph)
    ↓
[Data Acquisition] → [CKG Operations] → [Code Analysis] → [LLM Services] → [Synthesis & Reporting]
    ↓
Results Display (Web UI)
    ↓
History Storage
```

---

## Authentication Workflow

### **1. User Registration/Login Flow**

#### **Entry Point**: `src/agents/interaction_tasking/auth_web_ui.py`

**Data Flow**:
```
User Input (Username/Password)
    ↓
render_login_form() [auth_web_ui.py:150-200]
    ↓
AuthService.login() [src/core/auth/auth_service.py:50-70]
    ↓
UserManager.authenticate_user() [src/core/auth/user_manager.py:80-100]
    ↓
DatabaseManager.execute_query() [src/core/auth/database_manager.py:60-80]
    ↓
Session Token Generation [auth_service.py:120-140]
    ↓
st.session_state update [auth_web_ui.py:220-240]
    ↓
Dashboard Redirect [auth_web_ui.py:250-270]
```

#### **Classes & Functions Involved**:

1. **`AuthenticatedWebUI`** (`auth_web_ui.py:50-800`)
   - `render_login_form()`: User input validation
   - `render_registration_form()`: New user creation
   - `handle_authentication()`: Process login/register

2. **`AuthService`** (`auth_service.py:20-200`)
   - `login(username, password)`: Authentication logic
   - `validate_session(token)`: Session validation
   - `logout(token)`: Session cleanup

3. **`UserManager`** (`user_manager.py:20-300`)
   - `authenticate_user()`: Password verification
   - `create_user()`: New user creation
   - `get_user_by_username()`: User lookup

4. **`DatabaseManager`** (`database_manager.py:20-150`)
   - `execute_query()`: SQL execution
   - `execute_insert()`: Data insertion
   - `execute_update()`: Data updates

### **2. Session State Management**

**Data Structure**:
```python
st.session_state = {
    'authenticated': bool,
    'user_token': str,
    'current_user': UserInfo,
    'session_id': str,
    'view_mode': 'new_session' | 'history_view',
    'selected_session': Optional[str]
}
```

---

## Repository Analysis Workflow

### **Main Analysis Flow**

#### **Entry Point**: `src/agents/interaction_tasking/auth_web_ui.py:400-500`

**Complete Data Flow**:
```
User Repository URL Input
    ↓
UserIntentParserAgent.parse_repository_request() [user_intent_parser.py:50-80]
    ↓
TaskInitiationAgent.create_repository_analysis_task() [task_initiation.py:100-130]
    ↓
LangGraph Orchestrator [project_review_graph.py:100-200]
    ↓
┌─ Data Acquisition Team ─┐
│ GitOperationsAgent      │ [git_operations.py:50-200]
│ LanguageIdentifierAgent│ [language_identifier.py:50-300]
│ DataPreparationAgent   │ [data_preparation.py:50-400]
└────────────────────────┘
    ↓
┌─ CKG Operations Team ─┐
│ CodeParserCoordinator │ [code_parser_coordinator.py:50-250]
│ ASTtoCKGBuilder      │ [ast_to_ckg_builder.py:50-400]
│ CKGQueryInterface    │ [ckg_query_interface.py:50-500]
└──────────────────────┘
    ↓
┌─ Code Analysis Team ─┐
│ StaticAnalysisIntegrator│ [static_analysis_integrator.py:50-300]
│ ContextualQueryAgent   │ [contextual_query_agent.py:50-200]
└───────────────────────┘
    ↓
┌─ LLM Services Team ─┐
│ LLMGatewayAgent    │ [llm_gateway_agent.py:50-200]
│ OpenAIProvider     │ [llm_provider_abstraction.py:100-300]
└───────────────────┘
    ↓
┌─ Synthesis & Reporting ─┐
│ FindingAggregatorAgent │ [finding_aggregator.py:50-200]
│ ReportGeneratorAgent   │ [report_generator.py:50-400]
└──────────────────────────┘
    ↓
PresentationAgent.display_results() [presentation.py:50-300]
    ↓
HistoryManager.save_scan_result() [history_manager.py:150-180]
```

### **Detailed Step-by-Step Breakdown**

#### **Step 1: User Input Processing**

**File**: `src/agents/interaction_tasking/user_intent_parser.py`

```python
class UserIntentParserAgent:
    def parse_repository_request(self, repo_url: str, options: Dict) -> ParsedIntent:
        # Lines 50-80
        # 1. Validate repository URL format
        # 2. Extract platform (GitHub, GitLab, BitBucket)
        # 3. Parse analysis scope from options
        # 4. Return structured ParsedIntent object
```

**Input Data**:
- `repo_url`: str - Repository URL
- `options`: Dict - UI options (language detection, test inclusion, etc.)

**Output Data**:
- `ParsedIntent` object with validated URL và analysis parameters

#### **Step 2: Task Initiation**

**File**: `src/agents/interaction_tasking/task_initiation.py`

```python
class TaskInitiationAgent:
    def create_repository_analysis_task(self, parsed_intent: ParsedIntent) -> TaskDefinition:
        # Lines 100-130
        # 1. Generate unique task ID
        # 2. Calculate priority score
        # 3. Estimate duration
        # 4. Create TaskDefinition với metadata
```

**Input Data**:
- `ParsedIntent` object

**Output Data**:
- `TaskDefinition` object với task metadata

#### **Step 3: LangGraph Orchestration**

**File**: `src/core/orchestrator/project_review_graph.py`

```python
class ProjectReviewGraph(BaseGraph):
    def build_graph(self) -> StateGraph:
        # Lines 100-200
        # 1. Define state management
        # 2. Setup agent nodes
        # 3. Configure conditional edges
        # 4. Add error handling
```

**State Management**:
```python
class CodeScanState(TypedDict):
    task_id: str
    repository_url: str
    status: TaskStatus
    current_step: str
    data_acquisition_result: Optional[ProjectDataContext]
    ckg_result: Optional[Dict]
    analysis_result: Optional[List[Finding]]
    llm_result: Optional[Dict]
    final_result: Optional[Dict]
    error_info: Optional[Dict]
```

---

## Data Acquisition Workflow

### **Git Operations**

**File**: `src/agents/data_acquisition/git_operations.py`

#### **Function Flow**:
```python
GitOperationsAgent.clone_repository(repo_url, local_path)
    ↓ [Lines 80-120]
    # 1. Validate Git URL
    # 2. Generate unique local path
    # 3. Execute git clone với error handling
    # 4. Extract repository metadata
    ↓
GitOperationsAgent.calculate_repo_size()
    ↓ [Lines 140-160]
    # Calculate size, file count
    ↓
GitOperationsAgent.detect_basic_languages()
    ↓ [Lines 180-200]
    # Basic language detection từ extensions
```

**Output**: `RepositoryInfo` object

### **Language Identification**

**File**: `src/agents/data_acquisition/language_identifier.py`

#### **Function Flow**:
```python
LanguageIdentifierAgent.identify_language(project_path)
    ↓ [Lines 100-150]
    LanguageIdentifierAgent.analyze_file_extensions()
        ↓ [Lines 180-220]
        # Count files by extension
    ↓
    LanguageIdentifierAgent.analyze_config_files()
        ↓ [Lines 240-280]
        # Detect frameworks từ config files
    ↓
    LanguageIdentifierAgent.detect_frameworks()
        ↓ [Lines 300-350]
        # Pattern matching cho frameworks
    ↓
    LanguageIdentifierAgent.calculate_confidence()
        ↓ [Lines 380-400]
        # Score calculation based on evidence
```

**Output**: `ProjectLanguageProfile` object

### **Data Preparation**

**File**: `src/agents/data_acquisition/data_preparation.py`

#### **Function Flow**:
```python
DataPreparationAgent.prepare_project_context(repo_url, local_path, language_profile)
    ↓ [Lines 150-200]
    DataPreparationAgent.analyze_directory_structure()
        ↓ [Lines 220-260]
        # Build directory tree
    ↓
    DataPreparationAgent.analyze_files()
        ↓ [Lines 280-350]
        # Process individual files
        ↓
        DataPreparationAgent.extract_python_metadata()
            ↓ [Lines 400-450]
            # Parse Python config files
    ↓
    DataPreparationAgent.create_project_data_context()
        ↓ [Lines 500-550]
        # Aggregate all data
```

**Output**: `ProjectDataContext` object

---

## CKG Operations Workflow

### **Code Parsing Coordination**

**File**: `src/agents/ckg_operations/code_parser_coordinator.py`

#### **Function Flow**:
```python
CodeParserCoordinatorAgent.parse_python_project(project_path)
    ↓ [Lines 80-120]
    # 1. Discover Python files
    # 2. Generate AST for each file
    # 3. Extract code elements
    # 4. Aggregate parse results
```

### **AST to CKG Building**

**File**: `src/agents/ckg_operations/ast_to_ckg_builder.py`

#### **Function Flow**:
```python
ASTtoCKGBuilderAgent.build_ckg_from_project(parse_results)
    ↓ [Lines 100-150]
    ASTtoCKGBuilderAgent.process_ast_nodes()
        ↓ [Lines 200-250]
        # Convert AST nodes thành CKG nodes
    ↓
    ASTtoCKGBuilderAgent.extract_relationships()
        ↓ [Lines 300-350]
        # Extract calls, imports, inheritance
    ↓
    ASTtoCKGBuilderAgent.generate_cypher_queries()
        ↓ [Lines 400-450]
        # Create Neo4j insertion queries
    ↓
    ASTtoCKGBuilderAgent.save_to_neo4j()
        ↓ [Lines 500-550]
        # Execute queries với batch processing
```

**Output**: CKG stored in Neo4j database

---

## Code Analysis Workflow

### **Static Analysis Integration**

**File**: `src/agents/code_analysis/static_analysis_integrator.py`

#### **Function Flow**:
```python
StaticAnalysisIntegratorAgent.run_comprehensive_analysis(project_path)
    ↓ [Lines 80-100]
    StaticAnalysisIntegratorAgent.run_flake8()
        ↓ [Lines 150-200]
        # Execute flake8, parse output
    ↓
    StaticAnalysisIntegratorAgent.run_pylint()
        ↓ [Lines 250-300]
        # Execute pylint, parse output
    ↓
    StaticAnalysisIntegratorAgent.run_mypy()
        ↓ [Lines 350-400]
        # Execute mypy, parse output
    ↓
    StaticAnalysisIntegratorAgent.aggregate_findings()
        ↓ [Lines 450-500]
        # Combine results từ all tools
```

### **Contextual Query Analysis**

**File**: `src/agents/code_analysis/contextual_query_agent.py`

#### **Function Flow**:
```python
ContextualQueryAgent.analyze_findings_with_context(findings, ckg_interface)
    ↓ [Lines 100-150]
    # 1. Enrich findings với CKG context
    # 2. Calculate impact scores
    # 3. Generate contextual recommendations
    # 4. Detect related findings
```

**Output**: Enhanced `ContextualFinding` objects

---

## LLM Services Workflow

### **LLM Gateway Agent**

**File**: `src/agents/llm_services/llm_gateway_agent.py`

#### **Function Flow**:
```python
LLMGatewayAgent.explain_code_finding(finding, context)
    ↓ [Lines 100-120]
    LLMGatewayAgent.select_provider()
        ↓ [Lines 150-170]
        # Choose available LLM provider
    ↓
    LLMProvider.send_request(llm_request)
        ↓ [Lines 200-250] [llm_provider_abstraction.py]
        # Send request to OpenAI or Mock provider
    ↓
    LLMGatewayAgent.process_response()
        ↓ [Lines 280-300]
        # Parse và validate response
```

**Output**: `LLMResponse` với code explanations

---

## Synthesis & Reporting Workflow

### **Finding Aggregation**

**File**: `src/agents/synthesis_reporting/finding_aggregator.py`

#### **Function Flow**:
```python
FindingAggregatorAgent.aggregate_findings(findings_list, strategy)
    ↓ [Lines 100-150]
    FindingAggregatorAgent.deduplicate_findings()
        ↓ [Lines 200-250]
        # Remove similar findings
    ↓
    FindingAggregatorAgent.calculate_priority_scores()
        ↓ [Lines 300-350]
        # Score findings by importance
    ↓
    FindingAggregatorAgent.generate_statistics()
        ↓ [Lines 400-450]
        # Calculate summary metrics
```

### **Report Generation**

**File**: `src/agents/synthesis_reporting/report_generator.py`

#### **Function Flow**:
```python
ReportGeneratorAgent.generate_report(aggregated_findings, format)
    ↓ [Lines 100-120]
    ReportGeneratorAgent.select_format_generator()
        ↓ [Lines 150-180]
        # Choose format (TEXT, JSON, HTML, CSV, MARKDOWN)
    ↓
    ReportGeneratorAgent.generate_content()
        ↓ [Lines 200-400]
        # Generate formatted report
        ↓
        ReportGeneratorAgent.generate_executive_summary()
            ↓ [Lines 450-500]
            # Create executive summary
```

**Output**: Formatted reports in multiple formats

---

## Session Management Workflow

### **Session Creation & Tracking**

**File**: `src/core/session_manager/history_manager.py`

#### **Function Flow**:
```python
HistoryManager.create_session(session_type, user_id)
    ↓ [Lines 100-130]
    # 1. Generate unique session ID
    # 2. Initialize session metadata
    # 3. Save to JSON storage
    ↓
HistoryManager.save_scan_result(session_id, scan_result)
    ↓ [Lines 180-210]
    # 1. Validate session exists
    # 2. Save scan result data
    # 3. Update session status
```

### **Session State Management**

**Data Flow**:
```
Session Creation
    ↓
Real-time Status Updates
    ↓
Result Storage
    ↓
History Persistence
    ↓
Cross-session Retrieval
```

---

## History Management Workflow

### **History Storage & Retrieval**

**File**: `src/core/session_manager/history_manager.py`

#### **Storage Structure**:
```
logs/history/
├── sessions/           # Session metadata
│   └── {session_id}.json
├── scans/             # Scan results
│   └── {session_id}_scan.json
└── chats/             # Chat messages
    └── {session_id}_chat.json
```

#### **Function Flow**:
```python
HistoryManager.get_all_sessions(user_id, filters)
    ↓ [Lines 250-300]
    # 1. Load session metadata files
    # 2. Apply filters (session_type, status, date_range)
    # 3. Sort by created_at
    # 4. Return SessionHistory objects
    ↓
HistoryManager.get_session(session_id)
    ↓ [Lines 320-350]
    # 1. Load session metadata
    # 2. Load associated scan results
    # 3. Load chat history
    # 4. Return complete session data
```

---

## Data Structures & Models

### **Core Data Models**

#### **Authentication Models** (`src/core/auth/models.py`)
```python
@dataclass
class UserInfo:
    user_id: str
    username: str
    email: str
    role: UserRole
    created_at: datetime
    last_login: Optional[datetime]

@dataclass
class SessionInfo:
    token: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    last_accessed: datetime
```

#### **Task & Session Models** (`src/core/session_manager/`)
```python
@dataclass
class TaskDefinition:
    task_id: str
    task_type: TaskType
    repository_url: str
    analysis_scope: Dict[str, Any]
    priority: int
    estimated_duration: int
    created_at: datetime

class SessionType(Enum):
    REPOSITORY_ANALYSIS = "repository_analysis"
    PR_REVIEW = "pr_review"  
    CODE_QNA = "code_qna"

@dataclass
class SessionHistory:
    session_id: str
    session_type: SessionType
    status: SessionStatus
    user_id: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]
```

#### **Analysis Result Models**
```python
@dataclass
class Finding:
    file_path: str
    line_number: int
    severity: SeverityLevel
    finding_type: FindingType
    message: str
    rule: str
    source_tool: str

@dataclass
class ProjectDataContext:
    repository_info: RepositoryInfo
    language_profile: ProjectLanguageProfile
    directory_structure: DirectoryStructure
    file_analysis: List[FileInfo]
    project_metadata: ProjectMetadata
```

---

## File Organization

### **Source Code Structure**
```
src/
├── agents/                          # Multi-agent implementation
│   ├── interaction_tasking/         # Web UI & User interaction
│   │   ├── auth_web_ui.py          # Main authenticated web interface
│   │   ├── user_intent_parser.py   # User input processing
│   │   ├── task_initiation.py      # Task creation
│   │   ├── dialog_manager.py       # UI state management
│   │   └── presentation.py         # Results display
│   ├── data_acquisition/           # Repository data gathering
│   │   ├── git_operations.py       # Git clone & operations
│   │   ├── language_identifier.py  # Language detection
│   │   └── data_preparation.py     # Project context building
│   ├── ckg_operations/             # Code Knowledge Graph
│   │   ├── ckg_schema.py           # CKG schema definition
│   │   ├── code_parser_coordinator.py # AST parsing
│   │   ├── ast_to_ckg_builder.py   # AST to CKG conversion
│   │   └── ckg_query_interface.py  # Neo4j query interface
│   ├── code_analysis/              # Static analysis
│   │   ├── static_analysis_integrator.py # Linter integration
│   │   └── contextual_query_agent.py     # CKG-enhanced analysis
│   ├── llm_services/               # LLM integration
│   │   ├── llm_provider_abstraction.py # Provider interface
│   │   └── llm_gateway_agent.py         # LLM orchestration
│   └── synthesis_reporting/        # Results synthesis
│       ├── finding_aggregator.py   # Finding deduplication
│       └── report_generator.py     # Multi-format reports
├── core/                           # Core infrastructure
│   ├── orchestrator/              # LangGraph workflow
│   │   ├── base_graph.py          # Abstract base graph
│   │   └── project_review_graph.py # Concrete implementation
│   ├── auth/                      # Authentication system
│   │   ├── database_manager.py    # Database operations
│   │   ├── user_manager.py        # User management
│   │   ├── auth_service.py        # Session management
│   │   └── models.py              # Auth data models
│   ├── session_manager/           # Session & history
│   │   └── history_manager.py     # Session persistence
│   └── logging/                   # Debug logging
│       └── debug_logger.py        # Comprehensive logging
└── main.py                        # Application entry point
```

### **Data Storage Structure**
```
data/
└── ai_codescan.db                 # SQLite authentication database

logs/
├── debug/                         # Debug logs per session
│   ├── debug_{session_id}.log     # Main debug log
│   ├── trace_{session_id}.log     # Function call traces
│   └── summary_{session_id}.json  # Session summary
└── history/                       # Session persistence
    ├── sessions/                  # Session metadata
    ├── scans/                     # Scan results  
    └── chats/                     # Chat history

temp_repos/                        # Temporary repository storage
└── {unique_repo_names}/           # Cloned repositories
```

---

## Integration Points

### **Database Connections**
- **Neo4j**: CKG storage (port 7687)
- **SQLite**: Authentication (data/ai_codescan.db)
- **Redis**: Session caching (port 6379)
- **File System**: History persistence (logs/history/)

### **External Services**
- **OpenAI API**: LLM services
- **Git Repositories**: GitHub, GitLab, BitBucket
- **Static Analysis Tools**: flake8, pylint, mypy

### **Docker Services**
- **ai-codescan**: Main application (port 8501)
- **neo4j**: Graph database (ports 7474, 7687)
- **redis**: Caching service (port 6379)
- **portainer**: Container management (port 9000)

---

## Error Handling & Recovery

### **Error Propagation Flow**
```
Agent Error
    ↓
LangGraph Error Handler [project_review_graph.py:300-350]
    ↓
State Update với error info
    ↓
UI Error Display [auth_web_ui.py:600-650]
    ↓
Session Error Logging [history_manager.py:400-430]
```

### **Recovery Mechanisms**
1. **Graceful Degradation**: Continue workflow without failed component
2. **Retry Logic**: Automatic retry với exponential backoff
3. **Fallback Systems**: Alternative providers cho LLM services
4. **State Persistence**: Resume từ last checkpoint

---

*Generated: May 31, 2024*  
*AI CodeScan Phase 1 Complete*  
*Version: 1.0* 