#!/bin/bash
# semantic-context.sh - Generate relevant context using qmd
# Usage: ./semantic-context.sh [query]
# If no query provided, uses current task from handoff.json

set -e

CONTEXT_DIR="${HOME}/clawd/.context"
HANDOFF_FILE="${CONTEXT_DIR}/handoff.json"
OUTPUT_FILE="${CONTEXT_DIR}/relevant-context.md"
QMD_BIN="${HOME}/.bun/bin/qmd"

# Get query from argument or handoff.json
if [[ -n "$1" ]]; then
    QUERY="$1"
else
    if [[ -f "$HANDOFF_FILE" ]]; then
        QUERY=$(jq -r '.task.description // "current work"' "$HANDOFF_FILE")
    else
        QUERY="current work"
    fi
fi

echo "🔍 Searching for context: $QUERY"

# Check if qmd is available
if [[ ! -x "$QMD_BIN" ]]; then
    echo "Warning: qmd not found at $QMD_BIN, skipping semantic search"
    echo "# Semantic Context" > "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "_qmd not available - install with: bun install -g github:tobi/qmd_" >> "$OUTPUT_FILE"
    exit 0
fi

# Run qmd search
echo "# Semantic Context" > "$OUTPUT_FILE"
echo "Query: $QUERY" >> "$OUTPUT_FILE"
echo "Generated: $(date)" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "---" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Get top 10 results
cd "${HOME}/clawd"
"$QMD_BIN" search "$QUERY" -n 10 >> "$OUTPUT_FILE" 2>/dev/null || {
    echo "_No results found or qmd error_" >> "$OUTPUT_FILE"
}

echo "✅ Generated relevant-context.md"
echo "   Query: $QUERY"
echo "   Output: $OUTPUT_FILE"
