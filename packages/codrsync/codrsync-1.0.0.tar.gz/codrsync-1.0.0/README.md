# codrsync CLI

**Turn any dev into jedi ninja codr** - AI-powered development orchestrator.

## Installation

```bash
pip install codrsync
```

Or from source:

```bash
cd cli
pip install -e .
```

## Quick Start

```bash
# Configure authentication (uses YOUR Claude Code or API key)
codrsync auth

# Create a new project
codrsync init

# Check project status
codrsync status

# View roadmap
codrsync roadmap

# Start a sprint
codrsync sprint start

# Export to Excel/Jira/Trello
codrsync export excel
```

## Commands

### Local (work offline)

| Command | Description |
|---------|-------------|
| `codrsync status` | Show project dashboard |
| `codrsync roadmap` | Show timeline and dependencies |
| `codrsync sprint` | Manage sprints |
| `codrsync export` | Export to Excel, Jira, Trello, Notion |

### AI-powered (use your Claude)

| Command | Description |
|---------|-------------|
| `codrsync init` | Interactive project kickstart |
| `codrsync build` | AI-guided development |
| `codrsync prp` | Manage PRPs |

## Authentication

codrsync uses YOUR Claude Code installation or Anthropic API key.

```bash
# Configure once
codrsync auth

# Options:
# 1. Use Claude Code (if installed) - recommended
# 2. Use Anthropic API key
# 3. Offline mode (limited features)
```

**You pay for your own AI usage.** codrsync provides the intelligence through prompts.

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                     CODRSYNC CLI                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  LOCAL (free, offline)          AI (your Claude/API)        │
│  ────────────────────           ──────────────────          │
│  • status                       • init (kickstart)          │
│  • roadmap                      • build (implement)         │
│  • sprint                       • prp generate              │
│  • export                       • research                  │
│                                                             │
│  Reads JSON files               Uses YOUR account           │
│  No API calls                   You pay for usage           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

When you run `codrsync init`, it creates:

```
your-project/
├── doc/project/
│   ├── manifest.json      # Project metadata
│   └── progress.json      # Progress tracking
├── doc/task/
│   └── context-session.md # Current context
├── PRPs/                  # Product Requirement Prompts
├── src/                   # Your code
├── tests/                 # Your tests
└── exports/               # Exported reports
```

## Diagnostics

```bash
codrsync doctor
```

Shows:
- Python version
- Claude Code installation
- API key status
- Current project
- Dependencies

## License

MIT
