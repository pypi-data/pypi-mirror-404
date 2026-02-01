#!/bin/bash
# setup.sh - Initialize Context Bus infrastructure
# Usage: ./setup.sh
# This is a one-time setup script

set -e

CLAWD_DIR="${HOME}/clawd"
CONTEXT_DIR="${CLAWD_DIR}/.context"
SCRIPT_DIR="${CLAWD_DIR}/scripts/context-bus"

echo "🚀 Context Bus Setup"
echo "===================="
echo ""

# Step 1: Create directories
echo "📁 Creating directories..."
mkdir -p "$CONTEXT_DIR/sessions"
mkdir -p "$SCRIPT_DIR"
echo "   ✅ $CONTEXT_DIR"
echo "   ✅ $CONTEXT_DIR/sessions"
echo "   ✅ $SCRIPT_DIR"
echo ""

# Step 2: Initialize handoff.json if not exists
echo "📝 Initializing handoff.json..."
if [[ ! -f "$CONTEXT_DIR/handoff.json" ]]; then
    cat > "$CONTEXT_DIR/handoff.json" << 'EOF'
{
  "version": 1,
  "timestamp": null,
  "task": {
    "id": null,
    "description": null,
    "status": "idle",
    "complexity": null
  },
  "model": {
    "current": "opus",
    "previous": null,
    "switch_reason": null,
    "usage_percent": null
  },
  "context_refs": ["AGENTS.md", "MEMORY.md"],
  "recent_actions": [],
  "blockers": [],
  "next_steps": [],
  "notes": {}
}
EOF
    echo "   ✅ Created handoff.json"
else
    echo "   ⏭️  handoff.json already exists"
fi
echo ""

# Step 3: Initialize rolling-summary.md if not exists
echo "📝 Initializing rolling-summary.md..."
if [[ ! -f "$CONTEXT_DIR/rolling-summary.md" ]]; then
    cat > "$CONTEXT_DIR/rolling-summary.md" << EOF
# Session Summary
Last updated: $(date +"%Y-%m-%d %H:%M IST")

## Current Focus
No active task.

## Recent Progress
- Context Bus initialized

## Key Decisions
- None yet

## Open Questions
- None
EOF
    echo "   ✅ Created rolling-summary.md"
else
    echo "   ⏭️  rolling-summary.md already exists"
fi
echo ""

# Step 4: Create placeholder for relevant-context.md
echo "📝 Initializing relevant-context.md..."
if [[ ! -f "$CONTEXT_DIR/relevant-context.md" ]]; then
    echo "# Semantic Context" > "$CONTEXT_DIR/relevant-context.md"
    echo "" >> "$CONTEXT_DIR/relevant-context.md"
    echo "_Run semantic-context.sh to populate_" >> "$CONTEXT_DIR/relevant-context.md"
    echo "   ✅ Created relevant-context.md"
else
    echo "   ⏭️  relevant-context.md already exists"
fi
echo ""

# Step 5: Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x "$SCRIPT_DIR"/*.sh 2>/dev/null || true
echo "   ✅ All scripts are now executable"
echo ""

# Step 6: Verify jq is available
echo "🔍 Checking dependencies..."
if command -v jq &> /dev/null; then
    echo "   ✅ jq is installed"
else
    echo "   ❌ jq not found - install with: brew install jq"
fi

if [[ -x "${HOME}/.bun/bin/qmd" ]]; then
    echo "   ✅ qmd is installed"
else
    echo "   ⚠️  qmd not found (optional) - install with: bun install -g github:tobi/qmd"
fi
echo ""

# Summary
echo "===================="
echo "✅ Context Bus Setup Complete!"
echo ""
echo "Files created:"
echo "  - $CONTEXT_DIR/handoff.json"
echo "  - $CONTEXT_DIR/rolling-summary.md"
echo "  - $CONTEXT_DIR/relevant-context.md"
echo ""
echo "Available scripts:"
echo "  - update-handoff.sh   Update handoff.json with action"
echo "  - semantic-context.sh Generate qmd-based context"
echo "  - context-handoff.sh  Full handoff preparation"
echo "  - check-usage.sh      Check usage and recommend action"
echo ""
echo "Documentation:"
echo "  - docs/CONTEXT-BUS-MASTER-PLAN.md"
echo "  - docs/CONTEXT-BUS-TASKS.md"
echo ""
echo "Next: Monitor usage with check-usage.sh"
echo "      When at 98%, run context-handoff.sh"
