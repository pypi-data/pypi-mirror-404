#!/bin/bash
# model-router.sh - Determine which model to use based on usage and task type
# Usage: ./model-router.sh [task_type]
# task_type: code|reasoning|general (default: general)
# Returns: opus|codex and exit code (0=opus, 1=codex, 2=switch_needed)

set -e

CONTEXT_DIR="${HOME}/clawd/.context"
HANDOFF_FILE="${CONTEXT_DIR}/handoff.json"
SWITCH_LOG="${CONTEXT_DIR}/model-switches.log"

# Configuration
SWITCH_THRESHOLD=95  # Switch at 95% weekly usage (auto-switch)
TASK_TYPE="${1:-general}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_switch() {
    local from="$1"
    local to="$2"
    local reason="$3"
    echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") | $from -> $to | $reason" >> "$SWITCH_LOG"
}

get_current_model() {
    if [[ -f "$HANDOFF_FILE" ]]; then
        jq -r '.model.current // "opus"' "$HANDOFF_FILE"
    else
        echo "opus"
    fi
}

get_usage_percent() {
    # Try to read from handoff.json first
    if [[ -f "$HANDOFF_FILE" ]]; then
        local usage=$(jq -r '.model.usage_percent // -1' "$HANDOFF_FILE")
        if [[ "$usage" != "-1" ]] && [[ "$usage" != "null" ]]; then
            echo "$usage"
            return
        fi
    fi
    
    # Return -1 if unknown (manual check required)
    echo "-1"
}

update_model_in_handoff() {
    local new_model="$1"
    local reason="$2"
    
    if [[ -f "$HANDOFF_FILE" ]]; then
        local current=$(get_current_model)
        TMP_FILE=$(mktemp)
        jq --arg current "$current" \
           --arg new "$new_model" \
           --arg reason "$reason" \
           '.model.previous = $current | .model.current = $new | .model.switch_reason = $reason' \
           "$HANDOFF_FILE" > "$TMP_FILE"
        mv "$TMP_FILE" "$HANDOFF_FILE"
    fi
}

# Main logic
CURRENT_MODEL=$(get_current_model)
USAGE=$(get_usage_percent)

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🤖 Model Router"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Current model: $CURRENT_MODEL"
echo "Task type:     $TASK_TYPE"

if [[ "$USAGE" == "-1" ]]; then
    echo -e "Usage:         ${YELLOW}Unknown${NC} (run /status to update)"
else
    echo "Usage:         ${USAGE}%"
fi

echo ""

# Decision logic
RECOMMENDED="opus"
REASON=""
EXIT_CODE=0

# If already on Codex, stay on Codex unless explicitly switching back
if [[ "$CURRENT_MODEL" == "codex" ]]; then
    echo -e "${YELLOW}Currently on Codex (fallback mode)${NC}"
    echo ""
    echo "To switch back to Opus when usage resets:"
    echo "  ./model-router.sh --reset"
    RECOMMENDED="codex"
    EXIT_CODE=1
else
    # Check usage threshold
    if [[ "$USAGE" != "-1" ]] && [[ "$USAGE" -ge "$SWITCH_THRESHOLD" ]]; then
        echo -e "${RED}⚠️  Usage at ${USAGE}% - above ${SWITCH_THRESHOLD}% threshold${NC}"
        RECOMMENDED="codex"
        REASON="budget_threshold"
        EXIT_CODE=2
    else
        # Task-based routing (optional optimization)
        case "$TASK_TYPE" in
            code)
                # Could route to Codex for code tasks to save Opus budget
                # But per master plan, we use Opus until 98%
                RECOMMENDED="opus"
                ;;
            reasoning|architecture)
                # Always prefer Opus for complex reasoning
                RECOMMENDED="opus"
                ;;
            *)
                RECOMMENDED="opus"
                ;;
        esac
    fi
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [[ "$RECOMMENDED" == "opus" ]]; then
    echo -e "${GREEN}✅ Recommendation: Use OPUS${NC}"
    if [[ "$USAGE" != "-1" ]] && [[ "$USAGE" -ge 90 ]]; then
        echo -e "${YELLOW}   ⚠️  Approaching threshold - monitor usage${NC}"
    fi
elif [[ "$EXIT_CODE" == "2" ]]; then
    echo -e "${RED}🔄 Recommendation: SWITCH TO CODEX${NC}"
    echo ""
    echo "Run handoff:"
    echo "  ~/clawd/scripts/context-bus/context-handoff.sh opus codex budget_threshold"
else
    echo -e "${YELLOW}📍 Currently on: CODEX${NC}"
fi

echo ""

# Handle --reset flag
if [[ "$1" == "--reset" ]]; then
    echo "Resetting to Opus..."
    update_model_in_handoff "opus" "manual_reset"
    log_switch "codex" "opus" "manual_reset"
    echo -e "${GREEN}✅ Reset to Opus${NC}"
    exit 0
fi

# Handle --switch flag
if [[ "$1" == "--switch" ]]; then
    if [[ "$CURRENT_MODEL" == "opus" ]]; then
        echo "Switching to Codex..."
        update_model_in_handoff "codex" "manual_switch"
        log_switch "opus" "codex" "manual_switch"
        echo -e "${YELLOW}✅ Switched to Codex${NC}"
    else
        echo "Switching to Opus..."
        update_model_in_handoff "opus" "manual_switch"
        log_switch "codex" "opus" "manual_switch"
        echo -e "${GREEN}✅ Switched to Opus${NC}"
    fi
    exit 0
fi

# Output just the model name for scripting
echo "$RECOMMENDED"
exit $EXIT_CODE
