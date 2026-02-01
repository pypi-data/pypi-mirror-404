# Cortex MCP

**Making AI Accountable Over Time**

*Zero-Effort, Zero-Trust, Zero-Loss*

Cortex is a Model Context Protocol (MCP) server that enforces AI accountability through persistent memory, automatic verification, and evidence-based grounding. Unlike systems that make AI smarter, Cortex makes AI responsible.

**Status**: Phase 9 Complete | Test Coverage: 97% | Beta Testing Open

## Core Features

### Accountability Systems
- **Hallucination Detection** (Phase 9): Automatic claim extraction and evidence-based grounding with 0.87+ accuracy
- **Reference History**: Track what AI referenced and why (95% recommendation accuracy)
- **Smart Context**: Lazy loading with 70% token savings, auto-compression at 30min idle
- **Contradiction Detection**: Multi-language semantic contradiction detection (7 languages)

### Memory Management
- **Hybrid RAG**: Semantic + keyword search with 100% retrieval accuracy
- **Git Integration**: Auto-sync memory branches with git branches
- **Branching**: Automatic context separation with AI-detected topic changes
- **Snapshots**: Point-in-time backups with restore verification

### Privacy & Security
- **Zero-Trust**: All data stored locally by default
- **Cloud Sync**: Optional E2E encrypted backup to Google Drive
- **Plan A/B**: Automatic mode switching based on user acceptance rate

## Installation

```bash
pip install cortex-mcp
```

## Quick Start

### 1. Activate Your License

```bash
# Activate with license key
cortex-mcp --activate YOUR-LICENSE-KEY

# Or check license status
cortex-mcp --check
```

### 2. Configure Claude Desktop

Add to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "cortex": {
      "command": "cortex-mcp",
      "args": []
    }
  }
}
```

### 3. Start Using

Once configured, Claude will automatically use Cortex for memory management. You can:

- Ask Claude to remember information across sessions
- Search through past conversations and context
- Organize context by project/branch
- Sync context across devices (with cloud sync enabled)

## CLI Commands

```bash
cortex-mcp                    # Start MCP server
cortex-mcp --license KEY      # Activate license and start
cortex-mcp --activate KEY     # Activate license only
cortex-mcp --check            # Check license status
cortex-mcp --github-login     # Login with GitHub
cortex-mcp --telemetry off    # Disable anonymous telemetry
cortex-mcp --version          # Show version
cortex-mcp --help             # Show help
```

## MCP Tools

Cortex provides 15+ MCP tools across 4 categories:

### Core Memory
| Tool | Description |
|------|-------------|
| `initialize_context` | Scan project for initial context (FULL/LIGHT/NONE modes) |
| `create_branch` | Create context branch with auto-verification |
| `update_memory` | Save context with auto-indexing and hallucination detection |
| `get_active_summary` | Get current branch summary for System Prompt injection |

### Search & Retrieval
| Tool | Description |
|------|-------------|
| `search_context` | Hybrid RAG search (semantic + keyword) |
| `load_context` | Lazy load specific context (decompression) |
| `suggest_contexts` | AI-powered recommendations (95% accuracy) |
| `accept_suggestions` | Accept context recommendations (with feedback) |
| `reject_suggestions` | Reject recommendations (with reason) |

### Verification & Quality
| Tool | Description |
|------|-------------|
| `verify_response` | Hallucination detection with grounding score |
| `get_context_graph_info` | Retrieve context relationship graph |

### Backup & Sync
| Tool | Description |
|------|-------------|
| `create_snapshot` | Create verified backup snapshot |
| `restore_snapshot` | Restore with integrity verification |
| `list_snapshots` | List available snapshots |
| `sync_to_cloud` | E2E encrypted cloud backup |
| `sync_from_cloud` | Restore from cloud |

See [API_REFERENCE.md](./API_REFERENCE.md) for detailed documentation.

## Data Storage

All data is stored locally in `~/.cortex/`:

```
~/.cortex/
├── memory/          # Context files
├── chroma_db/       # Vector database
├── backups/         # Snapshots
├── licenses/        # License data
└── logs/            # Log files
```

## Privacy & Security

- **Zero-Trust**: All data stored locally by default
- **E2E Encryption**: Cloud sync uses AES-256-GCM encryption
- **No Tracking**: Telemetry is anonymous and opt-in

## Beta Testing

We're accepting 30 beta testers for 1-year free access!

**What you get:**
- Full Pro tier features (normally $15/month)
- Direct support and feature requests
- Shape the future of AI accountability

**Requirements:**
- Active AI development workflow
- Willing to provide feedback
- Test for at least 2-3 months

**Apply:** See [BETA_TEST_GUIDE.md](./BETA_TEST_GUIDE.md)

## License

Cortex MCP is available under the following license types:

- **Beta Free**: 1-year free license (30 spots available)
- **Pro**: $15/month (Reference History, Smart Context, Hallucination Detection)
- **Enterprise**: $20/month (All Pro + Cloud Sync, Multi-PC, Priority Support)

Visit [https://github.com/syab726/cortex](https://github.com/syab726/cortex) for more information.

## Support

- **Issues**: [GitHub Issues](https://github.com/syab726/cortex/issues)
- **Documentation**: [GitHub Wiki](https://github.com/syab726/cortex/wiki)

## Requirements

- Python 3.10+
- Claude Desktop (or any MCP-compatible client)

## Development

```bash
# Clone repository
git clone https://github.com/syab726/cortex.git
cd cortex

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .
isort .
```

---

**Cortex MCP** - *Never lose context again.*
