# GridCode Runtime (GCR)

> Modular Agentic Architecture (MAA) - An Open-Source Agent Runtime System

[![PyPI version](https://badge.fury.io/py/gridcode-runtime.svg)](https://pypi.org/project/gridcode-runtime/)
[![Python versions](https://img.shields.io/pypi/pyversions/gridcode-runtime.svg)](https://pypi.org/project/gridcode-runtime/)
[![License](https://img.shields.io/github/license/uukuguy/gridcode-runtime.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-1041%20passed-brightgreen.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-80%25-yellowgreen.svg)](tests/)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## 📚 **[Complete Documentation](docs/INDEX.md)** | **[完整文档（中文）](docs/INDEX_CN.md)**

**Quick Links**: [Quick Start](docs/QUICK_START.md) | [Alpha Testing](docs/ALPHA_TESTING_GUIDE.md) | [FAQ](docs/FAQ.md) | [API Reference](docs/API_REFERENCE.md)

---

## Overview

GridCode Runtime is an **open-source, modular, production-ready agent runtime system** inspired by Claude Code's prompt engineering patterns. It provides a unified framework for building intelligent agents with support for multiple AI frameworks (LangGraph, Pydantic-AI).

**Key Design Goals:**
- Framework-agnostic architecture supporting LangGraph and Pydantic-AI
- Production-ready features: state persistence, monitoring, human-in-the-loop
- Claude Code-inspired patterns: 5-phase planning, context-aware reminders, progressive prompt composition

> 📖 **中文文档**: [GridCode Runtime 中文文档](README_CN.md)

## 🎯 Use Cases

GridCode Runtime is ideal for:

- **Multi-Agent Systems** - Build complex agent workflows with specialized sub-agents (explore, plan, review)
- **Advanced Prompt Engineering** - Leverage 100+ reusable templates with dynamic variable resolution
- **Framework-Agnostic Development** - Switch between LangGraph and Pydantic-AI without code changes
- **Production AI Applications** - State persistence, monitoring, and human-in-the-loop workflows
- **Plugin Development** - Extend functionality with custom plugins and MCP server integration
- **Code Analysis & Generation** - Specialized agents for codebase exploration, planning, and review

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
# Basic installation (core features only)
pip install gridcode-runtime

# With LangGraph support (recommended for production)
pip install 'gridcode-runtime[langgraph]'

# With Pydantic-AI support
pip install 'gridcode-runtime[pydantic-ai]'

# With all optional dependencies (LangGraph + Pydantic-AI + dev tools)
pip install 'gridcode-runtime[all]'
```

### Optional Dependencies

GridCode Runtime supports multiple agent frameworks through optional dependencies:

| Extra | Includes | Use Case |
|-------|----------|----------|
| `langgraph` | LangGraph >= 0.2.0, langchain-core, langchain-anthropic | Production multi-agent workflows |
| `pydantic-ai` | Pydantic-AI >= 0.0.13 | Type-safe agent development |
| `all` | All frameworks + dev tools | Development and testing |

**Note**: The core package works without optional dependencies, but framework-specific features require the corresponding extras.

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

### 📖 Getting Started
- **[Alpha Testing Guide](docs/ALPHA_TESTING_GUIDE.md)** - Get started with alpha testing
- **[FAQ](docs/FAQ.md)** - Frequently asked questions and troubleshooting
- **[Quick Start Guide](docs/QUICK_START.md)** - Get up and running in 5 minutes
- **[Configuration Guide](docs/CONFIGURATION_GUIDE.md)** - Complete configuration reference

### 🏗️ Architecture & Design
- [Architecture Overview](docs/design/GRIDCODE_RUNTIME_ARCHITECTURE.md) - Three-layer system architecture and design patterns
- [Nexus Agent Engine](docs/design/NEXUS_AGENT_ENGINE_DESIGN.md) - Framework adapter design (Strategy + Adapter patterns)
- [Prompt System Design](docs/design/PROMPT_SYSTEM_DESIGN.md) - Template composition and variable resolution
- [Plugin System](docs/design/PLUGIN_SYSTEM_DESIGN.md) - Extensible plugin architecture with hooks

### 📖 User Guides
- [Agent Usage Guide](docs/AGENT_USAGE_GUIDE.md) - Working with multi-agent workflows
- [CLI Reference](docs/CLI_REFERENCE.md) - Complete CLI command reference
- [Plugin Development](docs/PLUGIN_DEVELOPMENT.md) - Creating custom plugins and hooks

### 🛠️ Developer Guides
- [Contributing Guide](CONTRIBUTING.md) - How to contribute to the project
- [API Reference](docs/API_REFERENCE.md) - Complete API documentation
- [Testing Guide](docs/TESTING_GUIDE.md) - Testing strategies and best practices

### 🌏 中文文档
- **[Alpha 测试指南](docs/ALPHA_TESTING_GUIDE_CN.md)** - Alpha 版本测试指南
- **[常见问题解答](docs/FAQ_CN.md)** - 常见问题和解决方案
- **[完整中文文档](README_CN.md)** - 完整的中文版 README

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

- **Alpha Testing**: [Alpha Testing Guide](docs/ALPHA_TESTING_GUIDE.md)
- **FAQ**: [Frequently Asked Questions](docs/FAQ.md)
- **Issues**: [GitHub Issues](https://github.com/uukuguy/gridcode-runtime/issues)
- **Discussions**: [GitHub Discussions](https://github.com/uukuguy/gridcode-runtime/discussions)
- **中文支持**: [中文文档](README_CN.md) | [中文 FAQ](docs/FAQ_CN.md)
