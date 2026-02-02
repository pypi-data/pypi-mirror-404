#!/bin/bash
# Context Bus v3 — Usage Monitor
# Adaptive interval, switch-back support, offline detection

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE="${CONTEXT_BUS_WORKSPACE:-$HOME/clawd}"
CONTEXT_DIR="$WORKSPACE/.context-bus"
HANDOFF_FILE="$CONTEXT_DIR/handoff.json"
CONFIG_FILE="${HOME}/.config/context-bus/config.yaml"
LOG_FILE="$CONTEXT_DIR/monitor.log"

# Source utilities
source "$SCRIPT_DIR/handoff-utils.sh" 2>/dev/null || true

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Read config value with default
get_config() {
    local key=$1
    local default=$2
    if [[ -f "$CONFIG_FILE" ]]; then
        local value=$(grep -E "^\s*${key}:" "$CONFIG_FILE" 2>/dev/null | head -1 | sed 's/.*:\s*//' | tr -d '"' | tr -d "'" || echo "")
        echo "${value:-$default}"
    else
        echo "$default"
    fi
}

# Send notification
notify() {
    local message="$1"
    local channel=$(get_config "channel" "none")
    
    log "NOTIFY: $message"
    
    case "$channel" in
        telegram)
            local chat_id=$(get_config "chat_id" "")
            if [[ -n "$chat_id" ]]; then
                # Try OpenClaw message endpoint
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
}

# Switch model
switch_model() {
    local from_model=$1
    local to_model=$2
    local reason=$3
    local attempt=0
    local max_attempts=3
    
    while [[ $attempt -lt $max_attempts ]]; do
        attempt=$((attempt + 1))
        log "Switch attempt $attempt: $from_model → $to_model ($reason)"
        
        # Update handoff.json
        local now=$(date -Iseconds)
        local history_entry="{\"model\": \"$from_model\", \"until\": \"$now\", \"reason\": \"$reason\"}"
        
        # Read current history
        local current_history=$(jq -r '.model.history // []' "$HANDOFF_FILE" 2>/dev/null || echo '[]')
        local new_history=$(echo "$current_history" | jq ". + [$history_entry]")
        
        # Update with new model
        local update_json=$(jq -n \
            --arg model "$to_model" \
            --argjson history "$new_history" \
            --arg reason "$reason" \
            '{
                model: {
                    current: $model,
                    history: $history,
                    switch_reason: $reason
                }
            }')
        
        # Try to update
        if update_handoff "$update_json" "monitor"; then
            # Log event
            log_event "switch" "{\"from\": \"$from_model\", \"to\": \"$to_model\", \"reason\": \"$reason\"}"
            log "Switch successful: $from_model → $to_model"
            return 0
        fi
        
        log "Switch attempt $attempt failed, retrying..."
        sleep 2
    done
    
    log "ERROR: Switch failed after $max_attempts attempts"
    notify "❌ Model switch failed after $max_attempts attempts"
    return 1
}

# Main monitor logic
main() {
    # Ensure context dir exists
    mkdir -p "$CONTEXT_DIR"
    
    # Check if handoff file exists
    if [[ ! -f "$HANDOFF_FILE" ]]; then
        log "No handoff.json found, skipping"
        exit 0
    fi
    
    # Read handoff (with corruption recovery)
    local handoff
    handoff=$(jq '.' "$HANDOFF_FILE" 2>/dev/null) || {
        log "ERROR: Corrupted handoff.json"
        exit 1
    }
    
    # Extract values
    local usage=$(echo "$handoff" | jq -r '.model.usage_percent // 0')
    local model=$(echo "$handoff" | jq -r '.model.current // "opus"')
    local timestamp=$(echo "$handoff" | jq -r '.timestamp // empty')
    local task_status=$(echo "$handoff" | jq -r '.task.status // "idle"')
    local ready=$(echo "$handoff" | jq -r '.handoff_ready // false')
    
    # Read thresholds
    local switch_threshold=$(get_config "switch_to_secondary" "95")
    local switch_back_threshold=$(get_config "switch_back" "50")
    
    log "Check: model=$model, usage=${usage}%, status=$task_status, ready=$ready"
    
    # Check if agent is offline (>30 min since last update)
    if [[ -n "$timestamp" ]]; then
        local now_epoch=$(date +%s)
        local ts_epoch=$(date -d "$timestamp" +%s 2>/dev/null || date -j -f "%Y-%m-%dT%H:%M:%S" "${timestamp%%+*}" +%s 2>/dev/null || echo 0)
        local age_minutes=$(( (now_epoch - ts_epoch) / 60 ))
        
        if [[ $age_minutes -gt 30 ]]; then
            log "Agent offline for ${age_minutes}m — skipping any switches"
            exit 0
        fi
    fi
    
    # === SWITCH TO SECONDARY (at threshold) ===
    if [[ "$model" == "opus" ]] && [[ "$usage" -ge "$switch_threshold" ]]; then
        log "TRIGGER: Usage ${usage}% >= ${switch_threshold}%"
        
        # Validate handoff
        if [[ "$ready" == "true" ]] && validate_handoff >/dev/null 2>&1; then
            # Handoff is valid, proceed with switch
            if switch_model "opus" "codex" "auto_threshold"; then
                notify "🔄 [Context Bus] Opus → Codex (usage at ${usage}%). Context preserved ✓"
            fi
        else
            log "Handoff not ready, waiting 30s..."
            sleep 30
            
            # Re-read and check again
            handoff=$(jq '.' "$HANDOFF_FILE" 2>/dev/null)
            ready=$(echo "$handoff" | jq -r '.handoff_ready // false')
            
            if [[ "$ready" == "true" ]] && validate_handoff >/dev/null 2>&1; then
                if switch_model "opus" "codex" "auto_threshold"; then
                    notify "🔄 [Context Bus] Opus → Codex (usage at ${usage}%). Context preserved ✓"
                fi
            else
                # Switch anyway with warning
                if switch_model "opus" "codex" "incomplete_handoff"; then
                    notify "⚠️ [Context Bus] Opus → Codex (usage at ${usage}%). Handoff incomplete!"
                fi
            fi
        fi
    fi
    
    # === SWITCH BACK TO PRIMARY (at reset) ===
    if [[ "$model" == "codex" ]] && [[ "$usage" -lt "$switch_back_threshold" ]]; then
        # Only switch back if task is idle or completed
        if [[ "$task_status" == "idle" ]] || [[ "$task_status" == "completed" ]]; then
            log "TRIGGER: Usage ${usage}% < ${switch_back_threshold}%, task=$task_status"
            
            if switch_model "codex" "opus" "limits_reset"; then
                notify "🔄 [Context Bus] Codex → Opus (limits reset, usage ${usage}%). Welcome back!"
            fi
        else
            log "Would switch back but task is $task_status, waiting..."
        fi
    fi
    
    # Log heartbeat event
    log_event "monitor_check" "{\"usage\": $usage, \"model\": \"$model\"}"
}

main "$@"
