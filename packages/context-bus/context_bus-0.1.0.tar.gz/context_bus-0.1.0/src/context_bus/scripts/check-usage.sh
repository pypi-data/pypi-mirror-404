#!/bin/bash
# check-usage.sh - Check current Claude Opus usage percentage
# Usage: ./check-usage.sh
# Returns: Current usage percentage and recommendation

set -e

CONTEXT_DIR="${HOME}/clawd/.context"
HANDOFF_FILE="${CONTEXT_DIR}/handoff.json"
USAGE_LOG="${CONTEXT_DIR}/usage.log"
THRESHOLD=98  # Switch at 98% as per master plan

# Try to get usage from OpenClaw session_status
# This is a placeholder - actual implementation depends on OpenClaw internals
get_usage() {
    # Method 1: Try reading from a usage file if OpenClaw writes one
    if [[ -f "${HOME}/.openclaw/usage.json" ]]; then
        jq -r '.weekly_percent // 0' "${HOME}/.openclaw/usage.json" 2>/dev/null && return
    fi
    
    # Method 2: Parse from recent session output
    # This would need to be implemented based on actual OpenClaw output format
    
    # Method 3: Return unknown (manual check required)
    echo "-1"
}

USAGE=$(get_usage)

# Log the check
echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") usage=$USAGE" >> "$USAGE_LOG"

# Determine recommendation
if [[ "$USAGE" == "-1" ]]; then
    echo "📊 Usage: Unknown (manual check required)"
    echo ""
    echo "Run /status in OpenClaw to check weekly limit usage"
    echo "If above ${THRESHOLD}%, run:"
    echo "  ~/clawd/scripts/context-bus/context-handoff.sh opus codex budget_threshold"
    RECOMMEND="unknown"
elif [[ "$USAGE" -ge "$THRESHOLD" ]]; then
    echo "🔴 Usage: ${USAGE}% (ABOVE THRESHOLD)"
    echo ""
    echo "Recommendation: Switch to Codex"
    echo "Run: ~/clawd/scripts/context-bus/context-handoff.sh opus codex budget_threshold"
    RECOMMEND="switch"
elif [[ "$USAGE" -ge 90 ]]; then
    echo "🟡 Usage: ${USAGE}% (approaching threshold)"
    echo ""
    echo "Status: Continue with Opus, monitor closely"
    RECOMMEND="monitor"
else
    echo "🟢 Usage: ${USAGE}%"
    echo ""
    echo "Status: Continue with Opus"
    RECOMMEND="continue"
fi

# Update handoff.json with current usage
if [[ -f "$HANDOFF_FILE" ]] && [[ "$USAGE" != "-1" ]]; then
    TMP_FILE=$(mktemp)
    jq --arg usage "$USAGE" '.model.usage_percent = ($usage | tonumber)' \
       "$HANDOFF_FILE" > "$TMP_FILE"
    mv "$TMP_FILE" "$HANDOFF_FILE"
fi

# Return status for scripting
case "$RECOMMEND" in
    switch) exit 2 ;;
    monitor) exit 1 ;;
    continue) exit 0 ;;
    *) exit 3 ;;
esac
