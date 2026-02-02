#!/bin/bash
# kimi-summarize.sh - Generate rolling summary using local LLM on Ultron
# Usage: ./kimi-summarize.sh
#
# Uses local Ollama (Llama 3.1 8B or Kimi K2.5 when available) to generate
# a concise summary of current context for handoff purposes.
#
# This is designed for low-frequency background use (e.g., every 4 hours via cron)

set -e

CONTEXT_DIR="${HOME}/clawd/.context"
HANDOFF_FILE="${CONTEXT_DIR}/handoff.json"
SUMMARY_FILE="${CONTEXT_DIR}/rolling-summary.md"
MEMORY_DIR="${HOME}/clawd/memory"

# Ultron Ollama endpoint
OLLAMA_HOST="http://100.84.34.49:11434"

# Model preference (use Kimi if available, fall back to Llama)
PREFERRED_MODEL="kimi-k2"
FALLBACK_MODEL="llama3.1:8b"

# Check which model is available
get_model() {
    # Check if Ollama is reachable
    if ! curl -s "${OLLAMA_HOST}/api/version" >/dev/null 2>&1; then
        echo ""
        return
    fi
    
    # Check for preferred model
    if curl -s "${OLLAMA_HOST}/api/show" -d "{\"name\":\"${PREFERRED_MODEL}\"}" 2>/dev/null | grep -q "modelfile"; then
        echo "$PREFERRED_MODEL"
        return
    fi
    
    # Fall back to Llama
    if curl -s "${OLLAMA_HOST}/api/show" -d "{\"name\":\"${FALLBACK_MODEL}\"}" 2>/dev/null | grep -q "modelfile"; then
        echo "$FALLBACK_MODEL"
        return
    fi
    
    echo ""
}

MODEL=$(get_model)

if [[ -z "$MODEL" ]]; then
    echo "⚠️  Ollama not available or no models found on Ultron"
    echo "Falling back to simple summary generation..."
    
    # Fall back to refresh-summary.sh (no LLM needed)
    "${HOME}/clawd/scripts/context-bus/refresh-summary.sh"
    exit 0
fi

echo "🤖 Using model: $MODEL on Ultron"

# Gather context
HANDOFF_CONTENT=$(cat "$HANDOFF_FILE" 2>/dev/null || echo "{}")
TODAY=$(date +%Y-%m-%d)
DAILY_NOTES=$(cat "${MEMORY_DIR}/${TODAY}.md" 2>/dev/null || echo "No daily notes yet")

# Build prompt
PROMPT=$(cat << 'EOF'
You are a context summarizer for an AI agent system. Generate a concise summary (under 400 tokens) of the current work state.

Format:
# Session Summary
Last updated: [timestamp]

## Current Focus
[1-2 sentences on active task]

## Recent Progress
[3-5 bullet points of completed work]

## Key Decisions
[Any important decisions made]

## Open Questions
[Unresolved items, if any]

Here is the current state:

HANDOFF JSON:
EOF
)

PROMPT="${PROMPT}
${HANDOFF_CONTENT}

DAILY NOTES:
${DAILY_NOTES}

Generate the summary now:"

# Call Ollama
echo "📝 Generating summary..."
RESPONSE=$(curl -s "${OLLAMA_HOST}/api/generate" \
    -d "{
        \"model\": \"${MODEL}\",
        \"prompt\": $(echo "$PROMPT" | jq -Rs .),
        \"stream\": false,
        \"options\": {
            \"num_predict\": 500,
            \"temperature\": 0.3
        }
    }" | jq -r '.response // empty')

if [[ -z "$RESPONSE" ]]; then
    echo "⚠️  Empty response from Ollama, using fallback"
    "${HOME}/clawd/scripts/context-bus/refresh-summary.sh"
    exit 0
fi

# Write summary
echo "$RESPONSE" > "$SUMMARY_FILE"

# Add timestamp if not present
if ! grep -q "Last updated:" "$SUMMARY_FILE"; then
    TIMESTAMP=$(date +"%Y-%m-%d %H:%M IST")
    sed -i '' "1s/^/# Session Summary\nLast updated: ${TIMESTAMP}\n\n/" "$SUMMARY_FILE" 2>/dev/null || true
fi

echo "✅ Generated summary using $MODEL"
echo ""
cat "$SUMMARY_FILE"
