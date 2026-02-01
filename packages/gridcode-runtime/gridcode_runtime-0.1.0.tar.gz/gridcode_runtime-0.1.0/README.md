# GridCode Runtime (GCR)

> Modular Agentic Architecture (MAA) - An Open-Source Agent Runtime System

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-822%20passed-brightgreen.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-81%25-yellowgreen.svg)](tests/)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Documentation](https://img.shields.io/badge/docs-https://github.com/uukuguy/docs-blue.svg)](https://github.com/uukuguy/docs)

## Overview

GridCode Runtime is an **open-source, modular, production-ready agent runtime system** inspired by Claude Code's prompt engineering patterns. It provides a unified framework for building intelligent agents with support for multiple AI frameworks (LangGraph, Pydantic-AI).

**Key Design Goals:**
- Framework-agnostic architecture supporting LangGraph and Pydantic-AI
- Production-ready features: state persistence, monitoring, human-in-the-loop
- Claude Code-inspired patterns: 5-phase planning, context-aware reminders, progressive prompt composition

> 📖 **中文文档**: [GridCode Runtime 中文文档](https://github.com/uukuguy/docs/blob/main/gridcode-runtime/README_zh.md)

## ✨ Key Features

### 🎯 Core Capabilities
- **Advanced Prompt System**: 100+ reusable prompt templates with 4-type variable injection (`${VAR}`, `${context.prop}`, `${COND ? "A" : "B"}`, `${FUNC()}`)
- **Framework Agnostic**: Nexus Agent Engine with Strategy+Adapter patterns supporting LangGraph and Pydantic-AI
- **Multi-Agent Architecture**: 10 specialized agents (Main, Explore, Plan, Review, TestRunner, Architect, CodeReviewer, Debugger, DocsArchitect, APIDocumenter, TutorialEngineer)
- **5-Phase Planning Workflow**: Understanding → Exploration → Planning → Review → Ready
- **Context-Aware System Reminders**: 18+ dynamic system hints with 5 Learning Mode reminders
- **Learning Mode**: Continuous improvement with FeedbackRecord, pattern analysis, and knowledge accumulation
- **Plugin System**: 5 plugin types with 10+ hook events and auto-discovery

### 🚀 Production Features
- **State Persistence**: SQLite-based checkpoints with ExecutionContext management
- **Human-in-the-Loop**: ConsoleInteractionHandler with approval workflows
- **Tool Result Enhancement**: Automatic guidance injection via ToolResultEnhancer
- **Layered Permissions**: Agent-specific tool whitelists/blacklists (main/explore/plan/review)
- **MCP Integration**: Multi-server support with stdio/HTTP transports and connection pooling
- **Configuration System**: YAML/environment/CLI with validation and templates

## Architecture

GridCode Runtime adopts a three-layer architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Orchestration                                     │
│  - GridCodeRuntime: Main runtime coordinator                │
│  - PlanModeManager: 5-phase planning workflow               │
│  - LearningModeManager: Learning mode & feedback system     │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Execution                                         │
│  ┌─────────────────────┐  ┌───────────────────────────────┐ │
│  │  Nexus Agent Engine │  │  Prompt Composer              │ │
│  │  (LangGraph/PAI)    │  │  (Template + Variable System) │ │
│  └─────────────────────┘  └───────────────────────────────┘ │
│  ┌─────────────────────┐  ┌───────────────────────────────┐ │
│  │  Agent Pool         │  │  Tool Registry                │ │
│  │  (10 Specialized)   │  │  (Read/Write/Edit/Glob/Grep)  │ │
│  └─────────────────────┘  └───────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Foundation                                        │
│  - ExecutionContext: State management (session/agent/tool)  │
│  - SQLiteStorage: Context persistence                       │
│  - PluginManager: Plugin system & hook registry             │
│  - MCPClient: MCP server integration                        │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Installation

```bash
# Install core package
pip install gridcode-runtime

# Install with LangGraph support
pip install gridcode-runtime[langgraph]

# Install with Pydantic-AI support
pip install gridcode-runtime[pydantic-ai]

# Install all dependencies (including dev tools)
pip install gridcode-runtime[all]
```

### Basic Usage

```python
import asyncio
from gridcode.core import GridCodeRuntime, ExecutionContext

async def main():
    # Create runtime with LangGraph adapter
    runtime = GridCodeRuntime(
        api_key="your-anthropic-api-key",
        framework="langgraph"  # or "pydantic-ai"
    )

    # Setup execution context
    context = ExecutionContext(
        session_id="demo-session",
        working_dir="/path/to/project"
    )

    # Run agent with simple prompt
    result = await runtime.run(
        prompt="Analyze this project's code structure",
        context=context
    )
    print(result.content)

asyncio.run(main())
```

### CLI Usage

```bash
# Run agent with CLI
gridcode run "Analyze code structure" --framework langgraph

# Configure settings
gridcode config set anthropic.api_key "your-api-key"
gridcode config set runtime.framework "langgraph"

# List available plugins
gridcode plugins list

# Get plugin information
gridcode plugins info example-plugin
```

## 📖 Advanced Usage

### Using Sub-Agents

```python
from gridcode.agents import AgentPool

# Initialize agent pool
pool = AgentPool(
    framework="langgraph",
    api_key="your-api-key"
)

# Spawn explore agent for read-only codebase exploration
result = await pool.spawn_agent(
    agent_type="explore",
    task="Find all API endpoint definitions",
    context=context
)

# Spawn plan agent for planning without execution
plan = await pool.spawn_agent(
    agent_type="plan",
    task="Design a new authentication system",
    context=context
)
```

### Enabling Learning Mode

```python
from gridcode.workflows import LearningModeManager

# Enable learning mode for continuous improvement
learning_mgr = LearningModeManager(context)
learning_mgr.enable()

# Provide feedback after task completion
learning_mgr.record_feedback(
    task_id="task-123",
    rating=5,
    feedback="Great performance on API analysis"
)

# Get learned patterns
patterns = learning_mgr.get_patterns()
```

### Plugin Development

```python
from gridcode.plugins import Plugin, Hook

class MyPlugin(Plugin):
    name = "my-plugin"
    version = "1.0.0"

    @Hook.on("PreToolUse")
    async def before_tool_use(self, tool_name: str, args: dict):
        # Custom logic before tool execution
        print(f"About to use tool: {tool_name}")
        return True  # Allow execution

    @Hook.on("PostToolUse")
    async def after_tool_use(self, tool_name: str, result: any):
        # Custom logic after tool execution
        print(f"Tool {tool_name} completed")
```

## ⚙️ Configuration

GridCode can be configured via YAML file, environment variables, or CLI arguments.

### Configuration File

Create `gridcode.yaml` in your project directory:

```yaml
runtime:
  api_provider: anthropic
  api_key: ${ANTHROPIC_API_KEY}
  model: claude-sonnet-4-5
  framework: langgraph

agent_pool:
  cache_enabled: true
  max_agents: 5

mcp:
  enabled: true
  servers:
    - name: context7
      type: stdio
      command: npx
      args: ["-y", "@context7/mcp-server"]
      env:
        CONTEXT7_API_KEY: ${CONTEXT7_API_KEY}

plugins:
  enabled: true
  dirs:
    - ~/.gridcode/plugins
    - ./plugins
```

For full configuration options, see [gridcode.yaml.template](gridcode.yaml.template) or the [Configuration Guide](https://github.com/uukuguy/docs/blob/main/gridcode-runtime/CONFIGURATION_GUIDE.md).

### Environment Variables

```bash
# API Keys
export ANTHROPIC_API_KEY="sk-ant-xxx"
export OPENAI_API_KEY="sk-proj-xxx"

# Optional: Model selection
export OPENAI_MODEL_NAME="gpt-4"

# Optional: MCP servers
export CONTEXT7_API_KEY="c7-xxx"
```

### CLI Options

```bash
# Use custom config file
gridcode run --config custom.yaml "Your query"

# Override config with CLI args
gridcode run --model gpt-4 --api-key sk-xxx "Your query"

# Configuration priority: CLI args > Environment variables > Config file > Defaults
```

## 🧪 Testing

GridCode has comprehensive test coverage with unit tests, integration tests, and performance benchmarks.

### Run Tests

```bash
# All tests
pytest

# Unit tests only (fast)
pytest tests/unit/ -v

# Integration tests (with mocked APIs)
pytest tests/integration/ --run-integration

# With coverage
pytest --cov=src --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### Test Status

- **Total Tests**: 822 tests
- **Passing**: 822 (100%)
- **Coverage**: 81%
- **Test Categories**:
  - Unit tests: ~697 tests (core logic)
  - Integration tests: ~125 tests (E2E scenarios)

For more details, see the [Testing Guide](https://github.com/uukuguy/docs/blob/main/gridcode-runtime/TESTING_GUIDE.md).

## 📚 Documentation

### 🏗️ Architecture & Design
- [Architecture Overview](https://github.com/uukuguy/docs/blob/main/gridcode-runtime/ARCHITECTURE.md) - Three-layer system architecture and design patterns
- [Nexus Agent Engine](https://github.com/uukuguy/docs/blob/main/gridcode-runtime/NEXUS_AGENT_ENGINE.md) - Framework adapter design (Strategy + Adapter patterns)
- [Prompt System Design](https://github.com/uukuguy/docs/blob/main/gridcode-runtime/PROMPT_SYSTEM.md) - Template composition and variable resolution
- [Plugin System](https://github.com/uukuguy/docs/blob/main/gridcode-runtime/PLUGIN_SYSTEM.md) - Extensible plugin architecture with hooks

### 📖 User Guides
- [Quick Start Guide](https://github.com/uukuguy/docs/blob/main/gridcode-runtime/QUICK_START.md) - Get up and running in 5 minutes
- [Configuration Guide](https://github.com/uukuguy/docs/blob/main/gridcode-runtime/CONFIGURATION_GUIDE.md) - Complete configuration reference
- [Agent Usage Guide](https://github.com/uukuguy/docs/blob/main/gridcode-runtime/AGENT_USAGE.md) - Working with multi-agent workflows
- [CLI Reference](https://github.com/uukuguy/docs/blob/main/gridcode-runtime/CLI_REFERENCE.md) - Complete CLI command reference

### 🛠️ Developer Guides
- [Contributing Guide](https://github.com/uukuguy/docs/blob/main/gridcode-runtime/CONTRIBUTING.md) - How to contribute to the project
- [Plugin Development](https://github.com/uukuguy/docs/blob/main/gridcode-runtime/PLUGIN_DEVELOPMENT.md) - Creating custom plugins and hooks
- [API Reference](https://github.com/uukuguy/docs/blob/main/gridcode-runtime/API_REFERENCE.md) - Complete API documentation
- [Testing Guide](https://github.com/uukuguy/docs/blob/main/gridcode-runtime/TESTING_GUIDE.md) - Testing strategies and best practices

### 🎓 Tutorials & Examples
- [Basic Usage Tutorial](https://github.com/uukuguy/docs/blob/main/gridcode-runtime/tutorials/BASIC_USAGE.md) - Step-by-step basic usage
- [Advanced Workflows](https://github.com/uukuguy/docs/blob/main/gridcode-runtime/tutorials/ADVANCED_WORKFLOWS.md) - Complex multi-agent scenarios
- [Plugin Examples](https://github.com/uukuguy/docs/blob/main/gridcode-runtime/tutorials/PLUGIN_EXAMPLES.md) - Real-world plugin implementations
- [Best Practices](https://github.com/uukuguy/docs/blob/main/gridcode-runtime/tutorials/BEST_PRACTICES.md) - Production deployment patterns

## Core Design Patterns (from Claude Code)

| Pattern | Description |
|---------|-------------|
| Progressive Prompt Composition | Layer prompts based on task complexity |
| 5-Phase Planning Workflow | Explore → Design → Review → Finalize → Approve |
| Context-Aware Reminders | Dynamic system hints based on state |
| Layered Tool Permissions | Different capabilities per agent type |
| Tool Result Enhancement | Inject guidance in tool responses |

## 🛠️ Tech Stack

| Category | Technologies |
|----------|-------------|
| **Runtime** | Python 3.11+, asyncio |
| **AI Frameworks** | LangGraph 0.2+, Pydantic-AI 0.0.13+ |
| **LLM Client** | Anthropic Claude API (Sonnet 4.5, Opus 4.5) |
| **Storage** | SQLite (checkpoints), Redis (optional) |
| **CLI** | Typer, Rich |
| **Logging** | loguru |
| **Testing** | pytest, pytest-asyncio, pytest-cov |
| **Code Quality** | Black, isort, Ruff, mypy |

## 🗺️ Roadmap

### Phase 1-3: Foundation ✅ (Complete)
- [x] Prompt Composer with variable resolution
- [x] Nexus Agent Engine (LangGraph + Pydantic-AI adapters)
- [x] Agent Pool (Explore, Plan, Review agents)
- [x] 5-Phase Planning Workflow
- [x] System Reminders (18+ reminder types)
- [x] Context Persistence (SQLite)

### Phase 4: Ecosystem ✅ (Complete)
- [x] Learning Mode with feedback system
- [x] Plugin System with hook registry
- [x] MCP Integration
- [x] Plugin Discovery & Auto-loading

### Phase 5: Production ✅ (Complete)
- [x] CLI Interface (typer-based)
- [x] Performance Optimization (lazy loading, caching)
- [x] Memory Profiling & Leak Detection
- [x] Configuration System (gridcode.yaml)
- [x] Integration Tests (131 E2E tests, 99.3% pass rate)
- [x] Documentation (Configuration Guide, Testing Guide)

### Phase 6: Future 🔮 (Planned)
- [ ] Web UI for agent monitoring
- [ ] More framework adapters (AutoGen, CrewAI)
- [ ] Distributed agent orchestration
- [ ] Cloud deployment support

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development environment setup
- Code style guidelines
- Testing requirements
- Pull request process

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

This project is inspired by [Claude Code](https://github.com/anthropics/claude-code)'s prompt engineering patterns. Special thanks to the Anthropic team for their innovative work in agentic AI systems.

## 📧 Contact & Support

- **Documentation**: [GridCode Runtime Docs](https://github.com/uukuguy/docs/tree/main/gridcode-runtime)
- **Issues**: [GitHub Issues](https://github.com/uukuguy/gridcode-runtime/issues)
- **Discussions**: [GitHub Discussions](https://github.com/uukuguy/gridcode-runtime/discussions)
- **API Reference**: [Complete API Documentation](https://github.com/uukuguy/docs/blob/main/gridcode-runtime/API_REFERENCE.md)
