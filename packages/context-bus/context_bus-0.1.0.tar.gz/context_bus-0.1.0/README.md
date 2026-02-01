# Context Bus

**Automatic model switching for AI coding agents with full context preservation.**

Never lose context when switching between Claude Opus, Codex, Gemini CLI, or local models. Context Bus automatically switches when you hit usage limits and switches back when limits reset — all while preserving your conversation context.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-blue)]()

## Features

- 🔄 **Auto-switch** at configurable usage threshold (default: 95%)
- 🔙 **Auto-return** to primary model when limits reset
- 📦 **Context preservation** via structured handoff files
- 📱 **Notifications** via Telegram, Discord, or Slack
- ⚙️ **Configurable** primary/secondary/tertiary models
- 🔒 **Safe switching** — won't interrupt active tasks
- 🤖 **OpenClaw/Clawdbot integration** — works out of the box

## What Context Bus Does

Context Bus provides **two key capabilities**:

### 1. Shared Context Layer (like Agent Sync, but for context)

All models read from the same files:
- `AGENTS.md` - Project context, constraints, current task
- `MEMORY.md` - Long-term memory, decisions, preferences
- `handoff.json` - Structured state for machine parsing

**Edit once → all models see the same context.** No re-explaining when you switch models.

### 2. Automatic Model Switching

When you hit usage limits:
- Auto-generates context summary
- Switches to fallback model
- Preserves full context
- Notifies you
- Auto-returns when limits reset

## Comparison with Agent Rules Sync

| Feature | Agent Rules Sync | Context Bus |
|---------|------------------|-------------|
| **Syncs rules** | ✅ Yes | ❌ No |
| **Syncs context** | ❌ No | ✅ Yes |
| **Model switching** | ❌ No | ✅ Yes |
| **Handoff protocol** | ❌ No | ✅ Yes |
| **Usage monitoring** | ❌ No | ✅ Yes |

**Use both together!** Agent Rules Sync for consistent rules + Context Bus for shared context and model switching.

---

## Installation

Works on **macOS**, **Linux**, and **Windows** (native + WSL).

### Via pip (Recommended)

```bash
pip install context-bus
context-bus init
```

### Via curl (One-liner)

```bash
curl -fsSL https://raw.githubusercontent.com/rajathkm/context-bus/main/install.sh | bash
```

### Via Clawdbot/OpenClaw

Just ask your agent:
```
"Install Context Bus for automatic model switching"
```

### Manual Install

```bash
git clone https://github.com/rajathkm/context-bus.git
cd context-bus
./install.sh
```

### What Happens During Installation

1. ✅ Scripts installed to `~/.context-bus/`
2. ✅ Config template created at `~/.config/context-bus/config.yaml`
3. ✅ Initial `handoff.json` and `rolling-summary.md` created
4. ✅ PATH updated (optional)

---

## Quick Start

### 1. Configure Your Models

Edit `~/.config/context-bus/config.yaml`:

```yaml
models:
  primary: opus          # Your main model (Claude Opus 4.5)
  secondary: codex       # Fallback model (OpenAI Codex)
  tertiary: gemini       # Optional third model (Gemini CLI)

thresholds:
  switch_to_secondary: 95    # Switch at 95% usage
  switch_back: 50            # Switch back when usage drops (indicates reset)
```

### 2. Set Up Notifications

```yaml
notifications:
  enabled: true
  channel: telegram
  telegram:
    chat_id: "YOUR_CHAT_ID"
```

### 3. Add to Your Agent

**For OpenClaw/Clawdbot users:**

The installer automatically adds Context Bus rules to your `HEARTBEAT.md`. Your agent will:
- Check usage during heartbeats
- Auto-switch at threshold
- Notify you on Telegram
- Switch back when limits reset

**For other agents (Claude Code, Cursor, etc.):**

Add to your agent's system instructions:
```markdown
## Context Bus Integration
Before starting work, read ~/.context-bus/handoff.json for current state.
After significant actions, update the handoff file.
```

---

## OpenClaw/Clawdbot Integration

Context Bus is designed to work seamlessly with OpenClaw (Clawdbot).

### Automatic Installation

Your Clawdbot can install Context Bus itself:

```
You: "Install the Context Bus skill for automatic model switching"
Clawdbot: *installs and configures Context Bus*
```

### Manual Integration

Add to your `HEARTBEAT.md`:

```markdown
## Context Bus Auto-Switch

1. Check usage via `session_status`
2. If usage >= 95% AND model is "opus":
   - Run handoff script
   - Switch to Codex
   - Notify on Telegram
3. If usage < 50% AND model is "codex" AND tasks are idle:
   - Switch back to Opus
   - Notify on Telegram
```

### How It Works with Clawdbot

```
┌─────────────────────────────────────────────────────────────┐
│                     YOUR CLAWDBOT                           │
│                                                             │
│  HEARTBEAT.md ←── Context Bus Rules                        │
│       ↓                                                     │
│  session_status → Check Usage                               │
│       ↓                                                     │
│  95%+ reached? → Run context-handoff.sh                     │
│       ↓                                                     │
│  handoff.json + rolling-summary.md generated                │
│       ↓                                                     │
│  Telegram notification sent                                 │
│       ↓                                                     │
│  Model switched (Opus → Codex)                             │
│       ↓                                                     │
│  Context preserved ✓                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Configuration Reference

### Full Config Example

```yaml
# ~/.config/context-bus/config.yaml

# =============================================================================
# MODEL CONFIGURATION
# =============================================================================
models:
  primary:
    name: opus
    cli: claude
    usage_check: session_status
    
  secondary:
    name: codex
    cli: codex
    usage_check: none
    
  tertiary:
    name: gemini
    cli: gemini
    enabled: false
    
  local:
    name: llama3.1:8b
    provider: ollama
    endpoint: http://localhost:11434
    enabled: false

# =============================================================================
# SWITCHING RULES
# =============================================================================
thresholds:
  switch_to_secondary: 95
  switch_back: 50
  min_switch_interval: 300    # Seconds between switches

# =============================================================================
# NOTIFICATIONS
# =============================================================================
notifications:
  enabled: true
  channel: telegram           # telegram | discord | slack | none
  
  telegram:
    chat_id: ""
    
  discord:
    webhook_url: ""
    
  slack:
    webhook_url: ""
    
  events:
    on_switch: true
    on_return: true
    on_error: true
    on_threshold_warning: true

# =============================================================================
# SAFETY RULES
# =============================================================================
safety:
  check_tasks_before_return: true
  check_subagents: true
  wait_if_busy: true
  max_wait_heartbeats: 10

# =============================================================================
# PATHS
# =============================================================================
paths:
  context_dir: ~/.context-bus
  workspace_files:
    - AGENTS.md
    - MEMORY.md
    - memory/*.md
```

---

## CLI Commands

```bash
# Check current status
context-bus status

# Manual model switching
context-bus switch codex        # Switch to secondary
context-bus switch opus         # Switch to primary
context-bus switch --back       # Return to primary (if safe)

# Generate handoff manually
context-bus handoff

# Refresh rolling summary
context-bus summary

# View/edit config
context-bus config --show
context-bus config --edit
```

---

## Context Preservation

### The Handoff System

When switching models, Context Bus creates a complete context bundle:

```
~/.context-bus/
├── handoff.json           # Structured state (machine-readable)
├── rolling-summary.md     # Human-readable summary (<400 tokens)
├── relevant-context.md    # Semantic search results (via qmd)
└── handoff-prompt.md      # Ready-to-use prompt for new model
```

### handoff.json Schema

```json
{
  "version": 1,
  "timestamp": "2026-02-01T14:00:00Z",
  "task": {
    "id": "feature-123",
    "description": "Implementing user authentication",
    "status": "in_progress",
    "complexity": "high"
  },
  "model": {
    "current": "codex",
    "previous": "opus",
    "switch_reason": "usage_threshold",
    "usage_percent": 96
  },
  "context_refs": [
    "AGENTS.md",
    "src/auth/oauth.ts"
  ],
  "recent_actions": [
    {"action": "edit", "file": "auth.ts", "summary": "Added OAuth flow"}
  ],
  "blockers": [],
  "next_steps": ["Add token refresh", "Write tests"],
  "notes": {
    "opus": "Using JWT with 1h expiry"
  }
}
```

### rolling-summary.md Example

```markdown
# Session Summary
Last updated: 2026-02-01 14:00 IST

## Current Focus
Implementing OAuth authentication flow for the API.

## Recent Progress
- Created OAuth client configuration
- Added token exchange endpoint
- Implemented session management

## Key Decisions
- Using JWT tokens with 1-hour expiry
- Refresh tokens stored in httpOnly cookies

## Open Questions
- None currently
```

---

## Supported Models

| Model | CLI Command | Install | Usage Check |
|-------|-------------|---------|-------------|
| Claude Opus 4.5 | `claude` | [Claude Code](https://claude.ai/code) | `session_status` |
| OpenAI Codex | `codex` | `npm install -g @openai/codex` | None |
| Gemini CLI | `gemini` | [Gemini CLI](https://github.com/google/gemini-cli) | API |
| Local (Ollama) | `ollama` | `brew install ollama` | None |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CONTEXT BUS                          │
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   Config    │    │   Monitor   │    │   Switch    │     │
│  │             │    │             │    │             │     │
│  │ config.yaml │ →  │ Check usage │ →  │  Handoff +  │     │
│  │ thresholds  │    │ via status  │    │  Notify     │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│                                              │              │
│                                              ↓              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   CONTEXT LAYER                      │   │
│  │                                                      │   │
│  │  handoff.json    rolling-summary.md    qmd search   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                              │              │
└──────────────────────────────────────────────┼──────────────┘
                                               ↓
┌─────────────────────────────────────────────────────────────┐
│                         MODELS                              │
│                                                             │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐   ┌─────────┐  │
│   │  Opus   │    │  Codex  │    │ Gemini  │   │  Local  │  │
│   │ Primary │    │Secondary│    │Tertiary │   │ Ollama  │  │
│   └─────────┘    └─────────┘    └─────────┘   └─────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Notifications

### Telegram

```bash
# Get your chat ID: message @userinfobot on Telegram
# Then configure:
context-bus config --telegram-chat-id YOUR_CHAT_ID
```

Example notifications:
```
🔄 [Context Bus] Opus → Codex
   Reason: Usage at 96%
   Context: Preserved ✓
   
🔄 [Context Bus] Codex → Opus
   Reason: Limits reset (usage now 12%)
   Status: Idle, safe to switch ✓
```

### Discord

```bash
# Create a webhook in your Discord server
context-bus config --discord-webhook YOUR_WEBHOOK_URL
```

### Slack

```bash
# Create an incoming webhook in Slack
context-bus config --slack-webhook YOUR_WEBHOOK_URL
```

---

## Safety Features

### Pre-Switch Checks

Before switching **back** to primary model:

| Check | What It Does |
|-------|--------------|
| Task status | Ensures no tasks are `in_progress` |
| Sub-agents | Checks for active spawned sessions |
| Cooldown | Prevents rapid toggling (5 min minimum) |

### If Checks Fail

- Switch is **delayed** to next heartbeat
- After 10 failed attempts, alert is sent
- Manual override available: `context-bus switch --force opus`

---

## Troubleshooting

### "Usage unknown"

Run `/status` in your agent to check usage, then:
```bash
~/.context-bus/update-usage.sh 78
```

### "Handoff not working"

Check files exist:
```bash
ls -la ~/.context-bus/
cat ~/.context-bus/handoff.json | jq .
```

### "Notifications not sending"

Verify config:
```bash
context-bus config --show
# Check telegram.chat_id is set
```

---

## Uninstall

```bash
curl -fsSL https://raw.githubusercontent.com/rajathkm/context-bus/main/uninstall.sh | bash
```

Or manually:
```bash
rm -rf ~/.context-bus
rm -rf ~/.config/context-bus
```

---

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md)

1. Fork the repo
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

---

## License

MIT License - see [LICENSE](LICENSE)

---

## Credits

Built for the [OpenClaw](https://github.com/openclaw/openclaw) community.

Inspired by [Agent Rules Sync](https://github.com/dhruv-anand-aintech/agent-rules-sync).
