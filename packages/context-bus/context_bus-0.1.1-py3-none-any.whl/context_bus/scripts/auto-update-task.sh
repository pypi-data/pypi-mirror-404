#!/bin/bash
# auto-update-task.sh - Update current task in handoff.json
# Usage: ./auto-update-task.sh <task_id> <description> <status> [complexity]
# Example: ./auto-update-task.sh "fix-bug-123" "Fix authentication bug" "in_progress" "medium"

set -e

CONTEXT_DIR="${HOME}/clawd/.context"
HANDOFF_FILE="${CONTEXT_DIR}/handoff.json"

TASK_ID="${1:-}"
DESCRIPTION="${2:-}"
STATUS="${3:-in_progress}"
COMPLEXITY="${4:-medium}"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S+05:30")

if [[ -z "$TASK_ID" ]] || [[ -z "$DESCRIPTION" ]]; then
    echo "Usage: $0 <task_id> <description> [status] [complexity]"
    echo ""
    echo "Arguments:"
    echo "  task_id      Unique identifier for the task"
    echo "  description  What the task is about"
    echo "  status       idle|in_progress|blocked|completed (default: in_progress)"
    echo "  complexity   low|medium|high (default: medium)"
    echo ""
    echo "Example:"
    echo "  $0 'auth-fix' 'Fix OAuth token refresh' 'in_progress' 'high'"
    exit 1
fi

# Validate status
case "$STATUS" in
    idle|in_progress|blocked|completed) ;;
    *)
        echo "Error: Invalid status '$STATUS'"
        echo "Valid: idle, in_progress, blocked, completed"
        exit 1
        ;;
esac

# Update handoff.json
if [[ -f "$HANDOFF_FILE" ]]; then
    TMP_FILE=$(mktemp)
    jq --arg id "$TASK_ID" \
       --arg desc "$DESCRIPTION" \
       --arg status "$STATUS" \
       --arg complexity "$COMPLEXITY" \
       --arg timestamp "$TIMESTAMP" \
       '.task.id = $id | 
        .task.description = $desc | 
        .task.status = $status | 
        .task.complexity = $complexity |
        .timestamp = $timestamp' \
       "$HANDOFF_FILE" > "$TMP_FILE"
    mv "$TMP_FILE" "$HANDOFF_FILE"
    
    echo "✅ Updated task in handoff.json"
    echo ""
    echo "Task ID:     $TASK_ID"
    echo "Description: $DESCRIPTION"
    echo "Status:      $STATUS"
    echo "Complexity:  $COMPLEXITY"
else
    echo "Error: handoff.json not found at $HANDOFF_FILE"
    exit 1
fi
