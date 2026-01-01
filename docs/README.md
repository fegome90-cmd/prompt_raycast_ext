# 📚 Documentation - Raycast Extension

## 📁 Directory Structure

```
docs/
├── backend/              # DSPy backend documentation
│   ├── README.md        # Backend main documentation
│   ├── quickstart.md    # 5-minute setup guide
│   ├── implementation-summary.md  # Implementation details
│   ├── files-created.md # Files created checklist
│   ├── status.md        # Current status
│   └── verification.md  # Final verification
├── dashboard/            # Dashboard/TypeScript frontend docs
│   ├── test-fixes.md    # Test fixes analysis
│   └── code-analysis.md # Code quality analysis
├── integrations/         # Integration guides
│   └── mcp-server.md    # MCP server documentation
├── research/            # Research and architecture docs
│   └── wizard/          # DSPy wizard patterns
├── plans/               # Implementation plans
│   └── 2026-01-01-fix-critical-metrics-bugs.md
└── claude.md           # Guide for Claude AI
```

## 🚀 Quick Access

### Backend (DSPy + FastAPI)
- **Getting Started**: [backend/quickstart.md](backend/quickstart.md)
- **Main Documentation**: [backend/README.md](backend/README.md)
- **Implementation Details**: [backend/implementation-summary.md](backend/implementation-summary.md)

### Dashboard (TypeScript + Raycast)
- **Code Analysis**: [dashboard/code-analysis.md](dashboard/code-analysis.md)
- **Test Fixes**: [dashboard/test-fixes.md](dashboard/test-fixes.md)

### Integrations
- **MCP Server**: [integrations/mcp-server.md](integrations/mcp-server.md)

### Research & Architecture
- **Wizard Patterns**: [research/wizard/](research/wizard/)
- **Architecture**: [research/ab-testing-architecture.md](research/ab-testing-architecture.md)

## 📖 Documentation Philosophy

This project follows a **modular documentation structure** where:
- **`backend/`** focuses on Python/FastAPI/DSPy implementation
- **`dashboard/`** focuses on TypeScript/Raycast frontend
- **`integrations/`** documents external system connections
- **`research/`** contains architecture decisions and research
- **`plans/`** contains implementation plans and tracking

## 🔍 Finding Information

### For Backend Development
1. Start with [backend/quickstart.md](backend/quickstart.md) for setup
2. Read [backend/README.md](backend/README.md) for architecture
3. Check [backend/implementation-summary.md](backend/implementation-summary.md) for details

### For Frontend Development
1. Review [dashboard/code-analysis.md](dashboard/code-analysis.md) for code quality
2. Check [dashboard/test-fixes.md](dashboard/test-fixes.md) for known issues

### For Integration Work
1. Read [integrations/mcp-server.md](integrations/mcp-server.md) for MCP setup
2. Check [backend/README.md](backend/README.md) for API endpoints

## 📝 Contributing to Documentation

When adding documentation:
1. **Place it in the correct subdirectory** (backend, dashboard, integrations, etc.)
2. **Use clear, descriptive filenames**
3. **Update this README.md** with new sections
4. **Cross-reference** related documents

## 🔗 External Documentation

- **DSPy Framework**: https://dspy-docs.vercel.app/
- **FastAPI**: https://fastapi.tiangolo.com/
- **Raycast Extensions**: https://developers.raycast.com/
- **MCP Protocol**: https://modelcontextprotocol.io/
