# Attune AI

**AI-powered developer workflows with cost optimization and pattern learning.**

Run code review, debugging, testing, and release workflows from your terminal or Claude Code. Smart tier routing saves 34-86% on LLM costs.

[![PyPI](https://img.shields.io/pypi/v/attune-ai?color=blue)](https://pypi.org/project/attune-ai/)
[![Tests](https://img.shields.io/badge/tests-13%2C489%20collected-brightgreen)](https://github.com/Smart-AI-Memory/attune-ai/actions)
[![Python](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)
[![Performance](https://img.shields.io/badge/performance-18x%20faster-success)](https://github.com/Smart-AI-Memory/attune-ai/blob/main/CHANGELOG.md)

```bash
pip install attune-ai[developer]
```

---

## 🎯 Transitioning to Claude-Native Architecture

**Attune AI is evolving to focus exclusively on Anthropic/Claude** to unlock features impossible with multi-provider abstraction:

- **📦 Prompt Caching:** 90% cost reduction on repeated prompts
- **📖 Flexible Context:** 200K via subscription for most tasks, up to 1M via API for large codebases
- **🧠 Extended Thinking:** See Claude's internal reasoning process
- **🔧 Advanced Tool Use:** Optimized for agentic workflows

**Timeline:**

- ✅ **v4.8.0 (Jan 2026):** Deprecation warnings for OpenAI/Google/Ollama providers
- ✅ **v5.0.0 (Jan 26, 2026):** Non-Anthropic providers removed (BREAKING - COMPLETE)
- ✅ **v5.0.2 (Jan 28, 2026):** Cost optimization suite with batch processing and caching monitoring

**Migration Guide:** [docs/CLAUDE_NATIVE.md](docs/CLAUDE_NATIVE.md)

---

## What's New in v2.0.0

**🎉 Introducing Attune AI** - A fresh start with a new name and renewed focus:

**Package Rebrand**: `empathy-framework` is now `attune-ai`

- New package name, same powerful features
- All capabilities from v5.x preserved
- Starting fresh at v2.0.0 to mark the new brand

**🤖 Multi-Agent Orchestration** - Build and coordinate specialized AI agents:

- **Agent Coordination Dashboard** - Real-time monitoring with 6 coordination patterns
- **Custom Agents** - Create specialized agents for your workflow needs
- **LLM Agents** - Leverage Claude's advanced capabilities
- Dashboard at `http://localhost:8000` with `python examples/dashboard_demo.py` (requires Redis)

**💰 Intelligent Cost Optimization**:

- **Authentication Strategy** - Smart routing between Claude subscription (free) and Anthropic API
- **Batch API** - 50% cost savings for non-urgent tasks
- **Smart Tier Routing** - Automatic model selection saves 34-86% on costs
- **Precise Token Counting** - >98% accurate cost tracking

**⚡ Performance & Scale**:

- **18x Faster** - Redis caching, parallel scanning, incremental updates
- **99.9% Memory Reduction** - Generator expressions across 27 optimizations
- **Natural Language** - Use plain English for workflow commands
- **13,489 Tests** - Comprehensive test coverage (99.9% passing)

**🔐 Security & Quality**:

- **Automated Security Scanning** - 82% accuracy, blocks critical issues
- **Path Traversal Protection** - All file operations validated
- **HIPAA/GDPR Compliance** - Enterprise-ready security options

**🧭 Developer Experience**:

- **MCP Integration** - 10 tools auto-discovered by Claude Code
- **Hub-Based Commands** - Organized workflows (`/dev`, `/testing`, `/release`, etc.)
- **Socratic Workflows** - Interactive discovery through guided questions
- **$0 Workflows** - Run via Claude Code with no API costs, unless a 1 million API context is required.

**Migration from Empathy Framework**:

```bash
# Old package
pip uninstall empathy-framework

# New package
pip install attune-ai[developer]

# Update imports in your code
# from empathy_os → from attune
```

[See Full Changelog](CHANGELOG.md) | [Migration Guide](docs/MIGRATION_GUIDE.md)

---

## Quick Start

### 1. Install

```bash
pip install attune-ai[developer]
```

### 2. Configure

```bash
# Auto-detect API keys
python -m attune.models.cli provider

# Or set explicitly
python -m attune.models.cli provider --set anthropic
```

### 3. Use

**In Claude Code:**

```bash
/dev           # Developer tools (debug, commit, PR, review)
/testing       # Run tests, coverage, benchmarks
/workflows     # Automated analysis (security, bugs, perf)
/plan          # Planning, TDD, code review
/docs          # Documentation generation
/release       # Release preparation

# Natural language support:
/workflows "find security issues"
/plan "review my code"

# Direct tool access via MCP (v5.1.1+):
# Claude Code automatically discovers Attune AI tools through the MCP server
# Just describe what you need in natural language:
"Run a security audit on src/"          → Invokes security_audit tool
"Generate tests for config.py"          → Invokes test_generation tool
"Check my auth configuration"           → Invokes auth_status tool
"Analyze performance bottlenecks"       → Invokes performance_audit tool
```

**MCP Server Integration (v5.1.1+):**

Attune AI now includes a Model Context Protocol (MCP) server that exposes all workflows as native Claude Code tools:

- **10 Tools Available:** security_audit, bug_predict, code_review, test_generation, performance_audit, release_prep, auth_status, auth_recommend, telemetry_stats, dashboard_status
- **Automatic Discovery:** No manual configuration needed - Claude Code finds tools via `.claude/mcp.json`
- **Natural Language Access:** Describe your need and Claude invokes the appropriate tool
- **Verification Hooks:** Automatic validation of Python/JSON files and workflow outputs

To verify MCP integration:

```bash
# Check server is running
echo '{"method":"tools/list","params":{}}' | PYTHONPATH=./src python -m attune.mcp.server

# Restart Claude Code to load the MCP server
# Tools will appear in Claude's tool list automatically
```

See [.claude/MCP_TEST_RESULTS.md](.claude/MCP_TEST_RESULTS.md) for full integration details.

**CLI:**

```bash
attune workflow run security-audit --path ./src
attune workflow run test-coverage --target 90
attune telemetry show  # View cost savings
```

**Python:**

```python
from attune import EmpathyOS

async with EmpathyOS() as attune:
    result = await attune.level_2_guided(
        "Review this code for security issues"
    )
    print(result["response"])
```

---

## Command Hubs

Workflows are organized into hubs for easy discovery:

| Hub               | Command       | Description                                  |
| ----------------- | ------------- | -------------------------------------------- |
| **Developer**     | `/dev`        | Debug, commit, PR, code review, quality      |
| **Testing**       | `/testing`    | Run tests, coverage analysis, benchmarks     |
| **Documentation** | `/docs`       | Generate and manage documentation            |
| **Release**       | `/release`    | Release prep, security scan, publishing      |
| **Workflows**     | `/workflows`  | Automated analysis (security, bugs, perf)    |
| **Plan**          | `/plan`       | Planning, TDD, code review, refactoring      |
| **Utilities**     | `/utilities`  | Project init, dependencies, profiling        |
| **Learning**      | `/learning`   | Pattern learning and session evaluation      |
| **Context**       | `/context`    | State management and memory                  |
| **Agent**         | `/agent`      | Create and manage custom agents              |

**Natural Language Support:**

```bash
# Use plain English - intelligent routing matches your intent
/workflows "find security vulnerabilities"  # → security-audit
/workflows "check code performance"         # → perf-audit
/workflows "predict bugs"                   # → bug-predict
/plan "review my code"                      # → code-review
/plan "help me plan this feature"           # → planning

# Or use traditional workflow names
/workflows security-audit
/plan code-review
```

**Interactive menus:**

```bash
/dev                    # Show interactive menu
/dev "debug auth error" # Jump directly to debugging
/testing "run coverage" # Run coverage analysis
/release                # Start release preparation
```

---

## Socratic Method

Workflows guide you through discovery instead of requiring upfront configuration:

```text
You: /dev

Claude: What development task do you need?
  1. Debug issue
  2. Create commit
  3. PR workflow
  4. Quality check

You: 1

Claude: What error or unexpected behavior are you seeing?
```

**How it works:**

1. **Discovery** - Workflow asks targeted questions to understand your needs
2. **Context gathering** - Collects relevant code, errors, and constraints
3. **Dynamic agent creation** - Assembles the right team based on your answers
4. **Execution** - Runs with appropriate tier selection

**Create custom agents with Socratic guidance:**

```bash
/agent create    # Guided agent creation
/agent team      # Build multi-agent teams interactively
```

---

## Cost Optimization

### Skills = $0 (Claude Code)

When using Claude Code, workflows run as skills through the Task tool - **no API costs**:

```bash
/dev           # $0 - uses your Claude subscription
/testing       # $0
/release       # $0
/agent create  # $0
```

### API Mode (CI/CD, Automation)

For programmatic use, smart tier routing saves 34-86%:

| Tier    | Model               | Use Case                    | Cost        |
| ------- | ------------------- | --------------------------- | ----------- |
| CHEAP   | Haiku / GPT-4o-mini | Formatting, simple tasks    | ~$0.005     |
| CAPABLE | Sonnet / GPT-4o     | Bug fixes, code review      | ~$0.08      |
| PREMIUM | Opus / o1           | Architecture, complex design | ~$0.45      |

```bash
# Track API usage and savings
attune telemetry savings --days 30
```

---

## Key Features

### Multi-Agent Workflows

```bash
# 4 parallel agents check release readiness
attune orchestrate release-prep

# Sequential coverage improvement
attune orchestrate test-coverage --target 90
```

### Response Caching

Up to 57% cache hit rate on similar prompts. Zero config needed.

```python
from attune.workflows import SecurityAuditWorkflow

workflow = SecurityAuditWorkflow(enable_cache=True)
result = await workflow.execute(target_path="./src")
print(f"Cache hit rate: {result.cost_report.cache_hit_rate:.1f}%")
```

### Pattern Learning

Workflows learn from outcomes and improve over time:

```python
from attune.orchestration.config_store import ConfigurationStore

store = ConfigurationStore()
best = store.get_best_for_task("release_prep")
print(f"Success rate: {best.success_rate:.1%}")
```

### Multi-Provider Support

```python
from attune_llm.providers import (
    AnthropicProvider,  # Claude
    OpenAIProvider,     # GPT-4
    GeminiProvider,     # Gemini
    LocalProvider,      # Ollama, LM Studio
)
```

---

## CLI Reference

```bash
# Provider configuration
python -m attune.models.cli provider
python -m attune.models.cli provider --set hybrid

# Workflows
attune workflow list
attune workflow run <workflow-name>

# Cost tracking
attune telemetry show
attune telemetry savings --days 30
attune telemetry export --format csv

# Orchestration
attune orchestrate release-prep
attune orchestrate test-coverage --target 90

# Meta-workflows
attune meta-workflow list
attune meta-workflow run release-prep --real
```

---

## Install Options

```bash
# Individual developers (recommended)
pip install attune-ai[developer]

# All LLM providers
pip install attune-ai[llm]

# With caching (semantic similarity)
pip install attune-ai[cache]

# Enterprise (auth, rate limiting)
pip install attune-ai[enterprise]

# Healthcare (HIPAA compliance)
pip install attune-ai[healthcare]

# Development
git clone https://github.com/Smart-AI-Memory/attune-ai.git
cd attune-ai && pip install -e .[dev]
```

---

## Environment Setup

```bash
# At least one provider required
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
export GOOGLE_API_KEY="..."

# Optional (but required for Agent Dashboard): Redis for memory
export REDIS_URL="redis://localhost:6379"
```

---

## VSCode Extension

Install the Attune AI VSCode extension for:

- **Dashboard** - Health score, costs, patterns
- **One-Click Workflows** - Run from command palette
- **Memory Panel** - Manage Redis and patterns
- **Cost Tracking** - Real-time savings display

---

## Documentation

- [Quick Start Guide](docs/quickstart.md)
- [CLI Reference](docs/cli-reference.md)
- [Testing Guide](docs/testing-guide.md)
- [Keyboard Shortcuts](docs/keyboard-shortcuts.md)
- [Full Documentation](https://smartaimemory.com/framework-docs/)

---

## Security

- Path traversal protection on all file operations
- JWT authentication with rate limiting
- PII scrubbing in telemetry
- HIPAA/GDPR compliance options
- **Automated security scanning** with 82% accuracy (Phase 3 AST-based detection)

See [SECURITY.md](SECURITY.md) for vulnerability reporting.

### Security Scanning

**Automated security scanning in CI/CD** - 82% accuracy, blocks critical issues:

```bash
# Run security audit locally
attune workflow run security-audit

# Scan specific directory
attune workflow run security-audit --input '{"path":"./src"}'
```

**Documentation:**

- **[Developer Workflow Guide](docs/DEVELOPER_SECURITY_WORKFLOW.md)** - Quick reference for handling security findings (all developers)
- **[CI/CD Integration Guide](docs/CI_SECURITY_SCANNING.md)** - Complete setup and troubleshooting (DevOps, developers)
- **[Scanner Architecture](docs/SECURITY_SCANNER_ARCHITECTURE.md)** - Technical implementation details (engineers, architects)
- **[Remediation Process](docs/SECURITY_REMEDIATION_PROCESS.md)** - 3-phase methodology for improving scanners (security teams, leadership)
- **[API Reference](docs/api-reference/security-scanner.md)** - Complete API documentation (developers extending scanner)

**Key achievements:**

- 82.3% reduction in false positives (350 → 62 findings)
- 16x improvement in scanner accuracy
- <15 minute average fix time for critical issues
- Zero critical vulnerabilities in production code

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

**Apache License 2.0** - Free and open source for everyone. Use it, modify it, build commercial products with it. [Details →](LICENSE)

---

## Acknowledgements

This project stands on the shoulders of giants. We are deeply grateful to the open source community and all the amazing projects that make this framework possible.

**[View Full Acknowledgements →](ACKNOWLEDGEMENTS.md)**

Special thanks to:

- **[Anthropic](https://www.anthropic.com/)** - For Claude AI and the Model Context Protocol
- **[LangChain](https://github.com/langchain-ai/langchain)** - Agent framework powering our meta-orchestration
- **[FastAPI](https://github.com/tiangolo/fastapi)** - Modern Python web framework
- **[pytest](https://github.com/pytest-dev/pytest)** - Testing framework making quality assurance effortless

And to all 50+ open source projects we depend on. [See the complete list →](ACKNOWLEDGEMENTS.md)

Want to contribute? See [CONTRIBUTORS.md](CONTRIBUTORS.md)

---

**Built by [Smart AI Memory](https://smartaimemory.com)** · [Docs](https://smartaimemory.com/framework-docs/) · [Examples](examples/) · [Issues](https://github.com/Smart-AI-Memory/attune-ai/issues)
