#!/bin/bash
# Update usage percentage in handoff.json
# Usage: update-usage.sh <percentage>

CONTEXT_DIR="${HOME}/.context-bus"
HANDOFF_FILE="${CONTEXT_DIR}/handoff.json"

usage=$1

if [[ -z "$usage" ]]; then
    echo "Usage: update-usage.sh <percentage>"
    echo "Example: update-usage.sh 78"
    exit 1
fi

# Ensure directory exists
mkdir -p "$CONTEXT_DIR"

# Create handoff.json if it doesn't exist
if [[ ! -f "$HANDOFF_FILE" ]]; then
    cat > "$HANDOFF_FILE" << 'EOF'
{
  "version": 1,
  "timestamp": null,
  "task": {"id": null, "description": null, "status": "idle"},
  "model": {"current": "opus", "previous": null, "switch_reason": null, "usage_percent": null},
  "context_refs": ["AGENTS.md", "MEMORY.md"],
  "recent_actions": [],
  "next_steps": []
}
EOF
fi

# Update usage
tmp=$(mktemp)
jq ".model.usage_percent = $usage | .timestamp = \"$(date -Iseconds)\"" "$HANDOFF_FILE" > "$tmp" && mv "$tmp" "$HANDOFF_FILE"

echo "Updated usage to ${usage}%"
