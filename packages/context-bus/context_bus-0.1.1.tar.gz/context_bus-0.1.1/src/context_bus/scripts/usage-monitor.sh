#!/bin/bash
# Context Bus Usage Monitor
# Runs via cron/launchd to check usage and auto-switch models

set -e

CONTEXT_DIR="${HOME}/.context-bus"
HANDOFF_FILE="${CONTEXT_DIR}/handoff.json"
CONFIG_FILE="${HOME}/.config/context-bus/config.yaml"
LOG_FILE="${CONTEXT_DIR}/monitor.log"

# Ensure directory exists
mkdir -p "$CONTEXT_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Get config value with default
get_config() {
    local key=$1
    local default=$2
    if [[ -f "$CONFIG_FILE" ]]; then
        local value=$(grep -E "^\s*${key}:" "$CONFIG_FILE" | head -1 | sed 's/.*:\s*//' | tr -d '"' | tr -d "'" 2>/dev/null)
        echo "${value:-$default}"
    else
        echo "$default"
    fi
}

# Get current model from handoff.json
get_current_model() {
    jq -r '.model.current // "opus"' "$HANDOFF_FILE" 2>/dev/null || echo "opus"
}

# Get last known usage
get_usage() {
    jq -r '.model.usage_percent // 0' "$HANDOFF_FILE" 2>/dev/null || echo "0"
}

# Update usage in handoff.json
update_handoff() {
    local field=$1
    local value=$2
    local tmp=$(mktemp)
    jq "$field = $value | .timestamp = \"$(date -Iseconds)\"" "$HANDOFF_FILE" > "$tmp" && mv "$tmp" "$HANDOFF_FILE"
}

# Send notification (works with OpenClaw or standalone)
notify() {
    local message=$1
    local channel=$(get_config "channel" "none")
    
    case "$channel" in
        telegram)
            local chat_id=$(get_config "chat_id" "")
            if [[ -n "$chat_id" ]]; then
                # Try OpenClaw message endpoint first
                curl -s -X POST "http://localhost:3033/api/message" \
                    -H "Content-Type: application/json" \
                    -d "{\"message\": \"$message\", \"to\": \"$chat_id\"}" 2>/dev/null || true
            fi
            ;;
        discord)
            local webhook=$(get_config "webhook_url" "")
            if [[ -n "$webhook" ]]; then
                curl -s -X POST "$webhook" \
                    -H "Content-Type: application/json" \
                    -d "{\"content\": \"$message\"}" 2>/dev/null || true
            fi
            ;;
        slack)
            local webhook=$(get_config "webhook_url" "")
            if [[ -n "$webhook" ]]; then
                curl -s -X POST "$webhook" \
                    -H "Content-Type: application/json" \
                    -d "{\"text\": \"$message\"}" 2>/dev/null || true
            fi
            ;;
    esac
    
    log "Notification: $message"
}

# Main logic
main() {
    if [[ ! -f "$HANDOFF_FILE" ]]; then
        log "No handoff.json found, skipping"
        exit 0
    fi
    
    local usage=$(get_usage)
    local current_model=$(get_current_model)
    local threshold=$(get_config "switch_to_secondary" "95")
    local switch_back=$(get_config "switch_back" "50")
    
    log "Check: usage=${usage}%, model=${current_model}, threshold=${threshold}%"
    
    # Check if we need to switch TO secondary
    if [[ "$current_model" == "opus" ]] && [[ "$usage" -ge "$threshold" ]]; then
        log "TRIGGER: Usage $usage% >= $threshold%, switching to codex"
        
        # Update model in handoff
        update_handoff '.model.current' '"codex"'
        update_handoff '.model.previous' '"opus"'
        update_handoff '.model.switch_reason' '"auto_monitor"'
        
        # Run handoff script if available
        if [[ -x "${CONTEXT_DIR}/context-handoff.sh" ]]; then
            "${CONTEXT_DIR}/context-handoff.sh" opus codex auto_monitor 2>/dev/null || true
        fi
        
        notify "🔄 [Context Bus] Opus → Codex (usage at ${usage}%)"
    fi
    
    # Check if we should switch BACK to primary
    if [[ "$current_model" == "codex" ]] && [[ "$usage" -lt "$switch_back" ]]; then
        local task_status=$(jq -r '.task.status // "idle"' "$HANDOFF_FILE" 2>/dev/null)
        
        if [[ "$task_status" == "idle" ]] || [[ "$task_status" == "completed" ]]; then
            log "TRIGGER: Usage $usage% < $switch_back%, switching back to opus"
            
            update_handoff '.model.current' '"opus"'
            update_handoff '.model.previous' '"codex"'
            update_handoff '.model.switch_reason' '"auto_reset"'
            
            notify "🔄 [Context Bus] Codex → Opus (limits reset, usage ${usage}%)"
        else
            log "Would switch back but task is $task_status, waiting..."
        fi
    fi
}

main "$@"
