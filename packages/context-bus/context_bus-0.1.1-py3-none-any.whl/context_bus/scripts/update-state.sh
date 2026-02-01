#!/bin/bash
# update-state.sh - Update next_steps, blockers, notes, or context_refs in handoff.json
# Usage: ./update-state.sh <field> <action> <value>
#
# Fields: next_steps, blockers, context_refs, notes
# Actions: add, remove, clear, set (notes only)
#
# Examples:
#   ./update-state.sh next_steps add "Implement auth flow"
#   ./update-state.sh blockers add "Waiting for API key"
#   ./update-state.sh blockers remove "Waiting for API key"
#   ./update-state.sh notes set opus "Decided to use JWT tokens"
#   ./update-state.sh context_refs add "src/auth/oauth.ts"

set -e

CONTEXT_DIR="${HOME}/clawd/.context"
HANDOFF_FILE="${CONTEXT_DIR}/handoff.json"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S+05:30")

FIELD="${1:-}"
ACTION="${2:-}"
VALUE="${3:-}"
EXTRA="${4:-}"  # For notes: the actual note content

if [[ -z "$FIELD" ]] || [[ -z "$ACTION" ]]; then
    echo "Usage: $0 <field> <action> <value> [extra]"
    echo ""
    echo "Fields:"
    echo "  next_steps    - List of next actions"
    echo "  blockers      - Current blockers"
    echo "  context_refs  - Files to read for context"
    echo "  notes         - Model-specific notes"
    echo ""
    echo "Actions:"
    echo "  add <item>        - Add item to list"
    echo "  remove <item>     - Remove item from list"
    echo "  clear             - Clear entire list"
    echo "  set <key> <value> - Set note (notes field only)"
    echo ""
    echo "Examples:"
    echo "  $0 next_steps add 'Write unit tests'"
    echo "  $0 blockers add 'Need design review'"
    echo "  $0 notes set opus 'Using singleton pattern'"
    exit 1
fi

if [[ ! -f "$HANDOFF_FILE" ]]; then
    echo "Error: handoff.json not found"
    exit 1
fi

TMP_FILE=$(mktemp)

case "$FIELD" in
    next_steps|blockers|context_refs)
        case "$ACTION" in
            add)
                if [[ -z "$VALUE" ]]; then
                    echo "Error: add requires a value"
                    exit 1
                fi
                jq --arg val "$VALUE" \
                   --arg field "$FIELD" \
                   --arg timestamp "$TIMESTAMP" \
                   '.[$field] += [$val] | .timestamp = $timestamp' \
                   "$HANDOFF_FILE" > "$TMP_FILE"
                echo "✅ Added to $FIELD: $VALUE"
                ;;
            remove)
                if [[ -z "$VALUE" ]]; then
                    echo "Error: remove requires a value"
                    exit 1
                fi
                jq --arg val "$VALUE" \
                   --arg field "$FIELD" \
                   --arg timestamp "$TIMESTAMP" \
                   '.[$field] -= [$val] | .timestamp = $timestamp' \
                   "$HANDOFF_FILE" > "$TMP_FILE"
                echo "✅ Removed from $FIELD: $VALUE"
                ;;
            clear)
                jq --arg field "$FIELD" \
                   --arg timestamp "$TIMESTAMP" \
                   '.[$field] = [] | .timestamp = $timestamp' \
                   "$HANDOFF_FILE" > "$TMP_FILE"
                echo "✅ Cleared $FIELD"
                ;;
            *)
                echo "Error: Invalid action '$ACTION' for $FIELD"
                echo "Valid: add, remove, clear"
                exit 1
                ;;
        esac
        ;;
    notes)
        case "$ACTION" in
            set)
                if [[ -z "$VALUE" ]] || [[ -z "$EXTRA" ]]; then
                    echo "Error: notes set requires <key> <value>"
                    echo "Example: $0 notes set opus 'Using JWT tokens'"
                    exit 1
                fi
                jq --arg key "$VALUE" \
                   --arg val "$EXTRA" \
                   --arg timestamp "$TIMESTAMP" \
                   '.notes[$key] = $val | .timestamp = $timestamp' \
                   "$HANDOFF_FILE" > "$TMP_FILE"
                echo "✅ Set note [$VALUE]: $EXTRA"
                ;;
            clear)
                jq --arg timestamp "$TIMESTAMP" \
                   '.notes = {} | .timestamp = $timestamp' \
                   "$HANDOFF_FILE" > "$TMP_FILE"
                echo "✅ Cleared all notes"
                ;;
            *)
                echo "Error: Invalid action '$ACTION' for notes"
                echo "Valid: set, clear"
                exit 1
                ;;
        esac
        ;;
    *)
        echo "Error: Invalid field '$FIELD'"
        echo "Valid: next_steps, blockers, context_refs, notes"
        exit 1
        ;;
esac

mv "$TMP_FILE" "$HANDOFF_FILE"
