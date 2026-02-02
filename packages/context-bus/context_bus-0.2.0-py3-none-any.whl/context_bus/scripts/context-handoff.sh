#!/bin/bash
# context-handoff.sh - Prepare full context bundle for model switch
# Usage: ./context-handoff.sh [from_model] [to_model] [reason]
# Example: ./context-handoff.sh opus codex budget_threshold

set -e

CONTEXT_DIR="${HOME}/clawd/.context"
HANDOFF_FILE="${CONTEXT_DIR}/handoff.json"
SUMMARY_FILE="${CONTEXT_DIR}/rolling-summary.md"
SEMANTIC_FILE="${CONTEXT_DIR}/relevant-context.md"
PROMPT_FILE="${CONTEXT_DIR}/handoff-prompt.md"
SCRIPT_DIR="$(dirname "$0")"

FROM_MODEL="${1:-opus}"
TO_MODEL="${2:-codex}"
REASON="${3:-manual_switch}"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M IST")

echo "🔄 Preparing context handoff: $FROM_MODEL → $TO_MODEL"
echo "   Reason: $REASON"
echo ""

# Step 1: Update handoff.json with switch info
echo "📝 Step 1: Updating handoff.json..."
TMP_FILE=$(mktemp)
jq --arg from "$FROM_MODEL" \
   --arg to "$TO_MODEL" \
   --arg reason "$REASON" \
   --arg timestamp "$(date -u +"%Y-%m-%dT%H:%M:%S+05:30")" \
   '.model.previous = $from | 
    .model.current = $to | 
    .model.switch_reason = $reason |
    .timestamp = $timestamp' \
   "$HANDOFF_FILE" > "$TMP_FILE"
mv "$TMP_FILE" "$HANDOFF_FILE"

# Step 2: Generate semantic context
echo "🔍 Step 2: Generating semantic context..."
"$SCRIPT_DIR/semantic-context.sh" >/dev/null 2>&1 || echo "   (semantic context skipped)"

# Step 3: Create handoff prompt
echo "📄 Step 3: Creating handoff prompt..."

TASK_DESC=$(jq -r '.task.description // "No task set"' "$HANDOFF_FILE")
TASK_STATUS=$(jq -r '.task.status // "unknown"' "$HANDOFF_FILE")
CONTEXT_REFS=$(jq -r '.context_refs | join("\n- ")' "$HANDOFF_FILE")
RECENT_ACTIONS=$(jq -r '.recent_actions[:5] | map("- " + .summary) | join("\n")' "$HANDOFF_FILE")
NEXT_STEPS=$(jq -r '.next_steps | map("1. " + .) | join("\n")' "$HANDOFF_FILE")
BLOCKERS=$(jq -r '.blockers | if length > 0 then map("- " + .) | join("\n") else "None" end' "$HANDOFF_FILE")
NOTES=$(jq -r '.notes | to_entries | map("**" + .key + ":** " + .value) | join("\n")' "$HANDOFF_FILE")

cat > "$PROMPT_FILE" << EOF
# Context Handoff

**Switching from:** $FROM_MODEL → $TO_MODEL  
**Reason:** $REASON  
**Timestamp:** $TIMESTAMP

---

## Current Task

**Description:** $TASK_DESC  
**Status:** $TASK_STATUS

---

## Files to Read First

- $CONTEXT_REFS

---

## Recent Actions (Last 5)

$RECENT_ACTIONS

---

## Next Steps

$NEXT_STEPS

---

## Current Blockers

$BLOCKERS

---

## Notes from Previous Model

$NOTES

---

## Relevant Context (Semantic Search)

$(cat "$SEMANTIC_FILE" 2>/dev/null || echo "_No semantic context available_")

---

## Rolling Summary

$(cat "$SUMMARY_FILE" 2>/dev/null || echo "_No rolling summary available_")

---

**Instructions for receiving model:**
1. Read the files listed in "Files to Read First"
2. Review the recent actions to understand what's been done
3. Continue with the next steps listed above
4. Update handoff.json after significant actions
EOF

echo ""
echo "✅ Handoff bundle ready!"
echo ""
echo "📁 Files created:"
echo "   - $HANDOFF_FILE (updated)"
echo "   - $SEMANTIC_FILE"
echo "   - $PROMPT_FILE"
echo ""
echo "📋 Feed this to $TO_MODEL:"
echo "   cat $PROMPT_FILE"
echo ""
echo "Or for Codex:"
echo "   codex exec \"\$(cat $PROMPT_FILE)\""
