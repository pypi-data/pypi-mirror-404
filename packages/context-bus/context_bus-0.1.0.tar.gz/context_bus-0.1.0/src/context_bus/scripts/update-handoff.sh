#!/bin/bash
# update-handoff.sh - Update handoff.json with new action/state
# Usage: ./update-handoff.sh <action> <file> <summary>
# Example: ./update-handoff.sh edit src/router.ts "Added switch logic"

set -e

CONTEXT_DIR="${HOME}/clawd/.context"
HANDOFF_FILE="${CONTEXT_DIR}/handoff.json"

# Check if handoff.json exists
if [[ ! -f "$HANDOFF_FILE" ]]; then
    echo "Error: handoff.json not found at $HANDOFF_FILE"
    exit 1
fi

ACTION="${1:-update}"
FILE="${2:-unknown}"
SUMMARY="${3:-No summary provided}"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S+05:30")

# Create new action entry
NEW_ACTION=$(cat <<EOF
{
  "timestamp": "$TIMESTAMP",
  "action": "$ACTION",
  "file": "$FILE",
  "summary": "$SUMMARY"
}
EOF
)

# Update handoff.json
# - Add new action to recent_actions (keep last 10)
# - Update timestamp
TMP_FILE=$(mktemp)

jq --argjson new_action "$NEW_ACTION" \
   --arg timestamp "$TIMESTAMP" \
   '.timestamp = $timestamp | 
    .recent_actions = ([$new_action] + .recent_actions | .[0:10])' \
   "$HANDOFF_FILE" > "$TMP_FILE"

mv "$TMP_FILE" "$HANDOFF_FILE"

echo "✅ Updated handoff.json"
echo "   Action: $ACTION"
echo "   File: $FILE"
echo "   Summary: $SUMMARY"
