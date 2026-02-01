#!/bin/bash
# update-usage.sh - Update usage percentage in handoff.json
# Usage: ./update-usage.sh <percentage>
# Example: ./update-usage.sh 78
#
# This should be called after checking /status in OpenClaw
# or can be integrated with OpenClaw's session tracking

set -e

CONTEXT_DIR="${HOME}/clawd/.context"
HANDOFF_FILE="${CONTEXT_DIR}/handoff.json"
USAGE_LOG="${CONTEXT_DIR}/usage.log"

if [[ -z "$1" ]]; then
    echo "Usage: $0 <percentage>"
    echo "Example: $0 78"
    echo ""
    echo "Get current usage from OpenClaw with /status"
    echo "Look for 'weekly limit' percentage"
    exit 1
fi

USAGE="$1"

# Validate it's a number
if ! [[ "$USAGE" =~ ^[0-9]+$ ]]; then
    echo "Error: Usage must be a number (0-100)"
    exit 1
fi

if [[ "$USAGE" -gt 100 ]]; then
    echo "Warning: Usage > 100%, capping at 100"
    USAGE=100
fi

# Update handoff.json
if [[ -f "$HANDOFF_FILE" ]]; then
    TMP_FILE=$(mktemp)
    jq --arg usage "$USAGE" '.model.usage_percent = ($usage | tonumber)' \
       "$HANDOFF_FILE" > "$TMP_FILE"
    mv "$TMP_FILE" "$HANDOFF_FILE"
    
    # Log the update
    echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") usage=$USAGE" >> "$USAGE_LOG"
    
    echo "✅ Updated usage to ${USAGE}%"
    
    # Check threshold
    if [[ "$USAGE" -ge 95 ]]; then
        echo ""
        echo "🔴 ABOVE THRESHOLD (95%)"
        echo "Recommendation: Auto-switch to Codex"
        echo ""
        echo "Run:"
        echo "  ~/clawd/scripts/context-bus/context-handoff.sh opus codex auto_threshold"
    elif [[ "$USAGE" -ge 85 ]]; then
        echo ""
        echo "🟡 Approaching threshold (90%+)"
        echo "Monitor closely"
    else
        echo ""
        echo "🟢 Within budget"
    fi
else
    echo "Error: handoff.json not found"
    exit 1
fi
