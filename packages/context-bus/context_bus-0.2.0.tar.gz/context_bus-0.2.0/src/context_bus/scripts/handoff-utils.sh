#!/bin/bash
# Context Bus v3 — Handoff Utilities
# Atomic writes, merge support, validation

set -e

WORKSPACE="${CONTEXT_BUS_WORKSPACE:-$(pwd)}"
CONTEXT_DIR="$WORKSPACE/.context-bus"
HANDOFF_FILE="$CONTEXT_DIR/handoff.json"
HISTORY_FILE="$CONTEXT_DIR/history.jsonl"
LOCK_FILE="$CONTEXT_DIR/.lock"

# Ensure directory exists
init_context_dir() {
    mkdir -p "$CONTEXT_DIR"
}

# Acquire file lock (with timeout)
acquire_lock() {
    local timeout=${1:-5}
    exec 200>"$LOCK_FILE"
    flock -w "$timeout" 200 || {
        echo "ERROR: Could not acquire lock after ${timeout}s" >&2
        return 1
    }
}

# Release file lock
release_lock() {
    flock -u 200 2>/dev/null || true
}

# Initialize handoff.json with v3 schema
init_handoff() {
    local now=$(date -Iseconds)
    local expires=$(date -d "+5 minutes" -Iseconds 2>/dev/null || date -v+5M -Iseconds)
    
    cat > "$HANDOFF_FILE" << EOF
{
  "schema_version": 3,
  "sequence": 1,
  "timestamp": "$now",
  "handoff_ready": true,
  "handoff_expires": "$expires",
  "checksum": null,
  "author": "init",
  "model": {
    "current": "opus",
    "usage_percent": 0,
    "history": []
  },
  "task": {
    "description": null,
    "status": "idle",
    "project": null
  },
  "context": {
    "recent_actions": [],
    "decisions": [],
    "next_steps": [],
    "blockers": []
  },
  "files_touched": []
}
EOF
    
    # Add checksum
    update_checksum
}

# Read handoff.json safely
read_handoff() {
    if [[ ! -f "$HANDOFF_FILE" ]]; then
        init_context_dir
        init_handoff
    fi
    
    # Validate JSON
    if ! jq '.' "$HANDOFF_FILE" >/dev/null 2>&1; then
        echo "WARNING: Corrupted handoff.json, reinitializing" >&2
        init_handoff
    fi
    
    cat "$HANDOFF_FILE"
}

# Compute and update checksum
update_checksum() {
    local content=$(jq 'del(.checksum)' "$HANDOFF_FILE")
    local checksum=$(echo "$content" | sha256sum | cut -d' ' -f1)
    
    local tmp=$(mktemp)
    jq ".checksum = \"sha256:$checksum\"" "$HANDOFF_FILE" > "$tmp"
    mv "$tmp" "$HANDOFF_FILE"
}

# Validate handoff (returns 0 if valid, 1 if invalid)
validate_handoff() {
    local handoff=$(read_handoff)
    local now_epoch=$(date +%s)
    
    # Get timestamp
    local timestamp=$(echo "$handoff" | jq -r '.timestamp // empty')
    if [[ -z "$timestamp" ]]; then
        echo "INVALID: No timestamp" >&2
        return 1
    fi
    
    # Check age (must be < 5 minutes / 300 seconds)
    local ts_epoch=$(date -d "$timestamp" +%s 2>/dev/null || date -j -f "%Y-%m-%dT%H:%M:%S" "$timestamp" +%s 2>/dev/null || echo 0)
    local age=$((now_epoch - ts_epoch))
    
    if [[ $age -gt 300 ]]; then
        echo "INVALID: Handoff is ${age}s old (max 300s)" >&2
        return 1
    fi
    
    # Check handoff_ready
    local ready=$(echo "$handoff" | jq -r '.handoff_ready // false')
    if [[ "$ready" != "true" ]]; then
        echo "INVALID: handoff_ready is not true" >&2
        return 1
    fi
    
    # Verify checksum
    local stored_checksum=$(echo "$handoff" | jq -r '.checksum // empty')
    if [[ -n "$stored_checksum" ]]; then
        local content=$(echo "$handoff" | jq 'del(.checksum)')
        local computed=$(echo "$content" | sha256sum | cut -d' ' -f1)
        if [[ "sha256:$computed" != "$stored_checksum" ]]; then
            echo "INVALID: Checksum mismatch" >&2
            return 1
        fi
    fi
    
    echo "VALID: Handoff is ${age}s old, ready=$ready"
    return 0
}

# Atomic merge update
# Usage: update_handoff '{"model": {"usage_percent": 87}}'
update_handoff() {
    local updates="$1"
    local author="${2:-agent}"
    
    init_context_dir
    acquire_lock 5 || return 1
    
    # Read existing or init
    local existing
    if [[ -f "$HANDOFF_FILE" ]]; then
        existing=$(jq '.' "$HANDOFF_FILE" 2>/dev/null || echo '{}')
    else
        init_handoff
        existing=$(cat "$HANDOFF_FILE")
    fi
    
    # Get current sequence
    local seq=$(echo "$existing" | jq -r '.sequence // 0')
    seq=$((seq + 1))
    
    # Compute timestamps
    local now=$(date -Iseconds)
    local expires=$(date -d "+5 minutes" -Iseconds 2>/dev/null || date -v+5M -Iseconds)
    
    # Merge: existing + updates + metadata
    local tmp=$(mktemp)
    echo "$existing" | jq \
        --argjson updates "$updates" \
        --arg now "$now" \
        --arg expires "$expires" \
        --arg author "$author" \
        --argjson seq "$seq" \
        '. * $updates * {
            sequence: $seq,
            timestamp: $now,
            handoff_expires: $expires,
            handoff_ready: true,
            author: $author
        }' > "$tmp"
    
    # Compute checksum of content (without checksum field)
    local content=$(jq 'del(.checksum)' "$tmp")
    local checksum=$(echo "$content" | sha256sum | cut -d' ' -f1)
    
    # Add checksum
    jq ".checksum = \"sha256:$checksum\"" "$tmp" > "${tmp}.final"
    
    # Atomic rename
    mv "${tmp}.final" "$HANDOFF_FILE"
    rm -f "$tmp"
    
    release_lock
    
    echo "Updated handoff.json (seq=$seq)"
}

# Log event to history.jsonl
log_event() {
    local event="$1"
    local data="${2:-{}}"
    
    init_context_dir
    
    local now=$(date -Iseconds)
    local entry=$(jq -n \
        --arg ts "$now" \
        --arg event "$event" \
        --argjson data "$data" \
        '{ts: $ts, event: $event} + $data')
    
    echo "$entry" >> "$HISTORY_FILE"
    
    # Rotate if > 10MB
    rotate_history
}

# Rotate history.jsonl if too large
rotate_history() {
    if [[ ! -f "$HISTORY_FILE" ]]; then
        return
    fi
    
    local size
    if [[ "$(uname)" == "Darwin" ]]; then
        size=$(stat -f%z "$HISTORY_FILE" 2>/dev/null || echo 0)
    else
        size=$(stat -c%s "$HISTORY_FILE" 2>/dev/null || echo 0)
    fi
    
    if [[ $size -gt 10485760 ]]; then  # 10MB
        local archive="${HISTORY_FILE}.$(date +%Y%m%d%H%M%S)"
        mv "$HISTORY_FILE" "$archive"
        gzip "$archive" 2>/dev/null || true
        echo "Rotated history.jsonl to ${archive}.gz"
    fi
}

# Get current model info
get_model_info() {
    local handoff=$(read_handoff)
    echo "$handoff" | jq '{
        current: .model.current,
        usage: .model.usage_percent,
        task: .task.description,
        status: .task.status,
        age_seconds: (now - (.timestamp | fromdateiso8601))
    }'
}

# CLI interface
case "${1:-}" in
    init)
        init_context_dir
        init_handoff
        echo "Initialized $HANDOFF_FILE"
        ;;
    read)
        read_handoff
        ;;
    validate)
        validate_handoff
        ;;
    update)
        update_handoff "$2" "${3:-agent}"
        ;;
    log)
        log_event "$2" "$3"
        ;;
    info)
        get_model_info
        ;;
    *)
        echo "Usage: $0 {init|read|validate|update|log|info}"
        echo ""
        echo "Commands:"
        echo "  init              Initialize handoff.json"
        echo "  read              Read handoff.json (with validation)"
        echo "  validate          Check if handoff is valid"
        echo "  update <json>     Merge update into handoff.json"
        echo "  log <event> <json> Append to history.jsonl"
        echo "  info              Get current model info"
        ;;
esac
