#!/bin/bash
# refresh-summary.sh - Generate rolling-summary.md from current state
# Usage: ./refresh-summary.sh
#
# This creates a human-readable summary from handoff.json
# For low-freq background updates via local Kimi, see kimi-summarize.sh

set -e

CONTEXT_DIR="${HOME}/clawd/.context"
HANDOFF_FILE="${CONTEXT_DIR}/handoff.json"
SUMMARY_FILE="${CONTEXT_DIR}/rolling-summary.md"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M IST")

if [[ ! -f "$HANDOFF_FILE" ]]; then
    echo "Error: handoff.json not found"
    exit 1
fi

# Extract data from handoff.json
TASK_DESC=$(jq -r '.task.description // "No active task"' "$HANDOFF_FILE")
TASK_STATUS=$(jq -r '.task.status // "idle"' "$HANDOFF_FILE")
MODEL=$(jq -r '.model.current // "opus"' "$HANDOFF_FILE")
USAGE=$(jq -r '.model.usage_percent // "unknown"' "$HANDOFF_FILE")

# Get recent actions (last 5)
RECENT_ACTIONS=$(jq -r '.recent_actions[:5] | map("- " + .summary) | join("\n")' "$HANDOFF_FILE")
if [[ -z "$RECENT_ACTIONS" ]] || [[ "$RECENT_ACTIONS" == "null" ]]; then
    RECENT_ACTIONS="- No recent actions recorded"
fi

# Get next steps
NEXT_STEPS=$(jq -r '.next_steps | if length > 0 then map("- " + .) | join("\n") else "- None defined" end' "$HANDOFF_FILE")

# Get blockers
BLOCKERS=$(jq -r '.blockers | if length > 0 then map("- " + .) | join("\n") else "None" end' "$HANDOFF_FILE")

# Get notes
NOTES=$(jq -r '.notes | to_entries | if length > 0 then map("- **" + .key + ":** " + .value) | join("\n") else "None" end' "$HANDOFF_FILE")

# Generate summary
cat > "$SUMMARY_FILE" << EOF
# Session Summary
Last updated: $TIMESTAMP

## Current State
- **Model:** $MODEL
- **Usage:** ${USAGE}%
- **Task:** $TASK_DESC
- **Status:** $TASK_STATUS

## Recent Progress
$RECENT_ACTIONS

## Next Steps
$NEXT_STEPS

## Blockers
$BLOCKERS

## Key Decisions
$NOTES
EOF

echo "✅ Generated rolling-summary.md"
echo ""
cat "$SUMMARY_FILE"
