# AI CodeScan API Documentation

This directory contains auto-generated API documentation for AI CodeScan.

## Modules

### Core
- [Orchestrator](orchestrator.md) - Central workflow coordination
- [Authentication](auth.md) - User authentication và authorization
- [Logging](logging.md) - Debug logging và monitoring

### Agents
- [Data Acquisition](data_acquisition.md) - Repository cloning và preparation
- [CKG Operations](ckg_operations.md) - Code Knowledge Graph construction
- [Code Analysis](code_analysis.md) - Static analysis và linting
- [LLM Services](llm_services.md) - AI integration và services
- [Synthesis & Reporting](synthesis_reporting.md) - Result aggregation
- [Interaction & Tasking](interaction_tasking.md) - Web UI và user interaction

## Coverage Report

Run the following command to check docstring coverage:

```bash
python scripts/generate_docs.py --coverage
```
