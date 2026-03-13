#!/bin/bash
# Ralph Wiggum - Long-running AI agent loop
# Usage: ./ralph.sh [--tool amp|claude] [--name agent-name] [max_iterations]
# Multi-project workspace edition with multi-agent coordination

set -e

# Parse arguments
TOOL="claude"
MAX_ITERATIONS=10
AGENT_NAME=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --tool)
      TOOL="$2"
      shift 2
      ;;
    --tool=*)
      TOOL="${1#*=}"
      shift
      ;;
    --name)
      AGENT_NAME="$2"
      shift 2
      ;;
    --name=*)
      AGENT_NAME="${1#*=}"
      shift
      ;;
    *)
      if [[ "$1" =~ ^[0-9]+$ ]]; then
        MAX_ITERATIONS="$1"
      fi
      shift
      ;;
  esac
done

if [[ "$TOOL" != "amp" && "$TOOL" != "claude" ]]; then
  echo "Error: Invalid tool '$TOOL'. Must be 'amp' or 'claude'."
  exit 1
fi

WORKSPACE="/Users/keith_ai/Documents/Agentic Projects"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRD_FILE="$SCRIPT_DIR/prd.json"
PROGRESS_FILE="$SCRIPT_DIR/progress.txt"
ARCHIVE_DIR="$SCRIPT_DIR/archive"
LAST_BRANCH_FILE="$SCRIPT_DIR/.last-branch"
QUERY="python3 $WORKSPACE/business-agents/query.py"

if [ ! -f "$PRD_FILE" ]; then
  echo "Error: prd.json not found at $PRD_FILE"
  exit 1
fi

# ---------------------------------------------------------------
# Generate a unique session ID for this ralph instance
# ---------------------------------------------------------------
SESSION_ID=$(python3 -c "import uuid; print(str(uuid.uuid4()))")
if [ -n "$AGENT_NAME" ]; then
  SESSION_ID="${AGENT_NAME}-${SESSION_ID:0:8}"
fi

# ---------------------------------------------------------------
# Archive previous run if branch changed
# ---------------------------------------------------------------
if [ -f "$PRD_FILE" ] && [ -f "$LAST_BRANCH_FILE" ]; then
  CURRENT_BRANCH=$(jq -r '.branchName // empty' "$PRD_FILE" 2>/dev/null || echo "")
  LAST_BRANCH=$(cat "$LAST_BRANCH_FILE" 2>/dev/null || echo "")

  if [ -n "$CURRENT_BRANCH" ] && [ -n "$LAST_BRANCH" ] && [ "$CURRENT_BRANCH" != "$LAST_BRANCH" ]; then
    DATE=$(date +%Y-%m-%d)
    FOLDER_NAME=$(echo "$LAST_BRANCH" | sed 's|^ralph/||')
    ARCHIVE_FOLDER="$ARCHIVE_DIR/$DATE-$FOLDER_NAME"

    echo "Archiving previous run: $LAST_BRANCH"
    mkdir -p "$ARCHIVE_FOLDER"
    [ -f "$PRD_FILE" ] && cp "$PRD_FILE" "$ARCHIVE_FOLDER/"
    [ -f "$PROGRESS_FILE" ] && cp "$PROGRESS_FILE" "$ARCHIVE_FOLDER/"
    echo "   Archived to: $ARCHIVE_FOLDER"

    echo "# Ralph Progress Log" > "$PROGRESS_FILE"
    echo "Started: $(date)" >> "$PROGRESS_FILE"
    echo "---" >> "$PROGRESS_FILE"
  fi
fi

if [ -f "$PRD_FILE" ]; then
  CURRENT_BRANCH=$(jq -r '.branchName // empty' "$PRD_FILE" 2>/dev/null || echo "")
  if [ -n "$CURRENT_BRANCH" ]; then
    echo "$CURRENT_BRANCH" > "$LAST_BRANCH_FILE"
  fi
fi

if [ ! -f "$PROGRESS_FILE" ]; then
  echo "# Ralph Progress Log" > "$PROGRESS_FILE"
  echo "Started: $(date)" >> "$PROGRESS_FILE"
  echo "---" >> "$PROGRESS_FILE"
fi

# ---------------------------------------------------------------
# Register this session in the coordination DB
# ---------------------------------------------------------------
$QUERY register "{\"id\": \"$SESSION_ID\", \"pid\": $$, \"tool\": \"$TOOL\"}" 2>/dev/null || true

cleanup() {
  echo ""
  echo "Deregistering session $SESSION_ID..."
  $QUERY deregister "$SESSION_ID" 2>/dev/null || true
}
trap cleanup EXIT

echo ""
echo "==============================================================="
echo "  Ralph starting — Session: $SESSION_ID"
echo "  Tool: $TOOL | Max iterations: $MAX_ITERATIONS"
echo "  Workspace: $WORKSPACE"
echo "==============================================================="
echo ""
echo "Other active agents:"
$QUERY status 2>/dev/null || echo "  (coordination DB unavailable)"
echo ""

for i in $(seq 1 $MAX_ITERATIONS); do
  echo ""
  echo "---------------------------------------------------------------"
  echo "  Iteration $i of $MAX_ITERATIONS | Session: ${SESSION_ID:0:16}..."
  echo "---------------------------------------------------------------"

  # Heartbeat — let other agents know we're alive
  $QUERY heartbeat "$SESSION_ID" 2>/dev/null || true

  # Pass session ID to agent so it can use claim/release
  AGENT_PROMPT=$(cat "$SCRIPT_DIR/CLAUDE.md")
  AGENT_PROMPT="$AGENT_PROMPT

## This Session
SESSION_ID=$SESSION_ID
ITERATION=$i
"

  if [[ "$TOOL" == "amp" ]]; then
    OUTPUT=$(echo "$AGENT_PROMPT" | amp --dangerously-allow-all 2>&1 | tee /dev/stderr) || true
  else
    OUTPUT=$(echo "$AGENT_PROMPT" | claude --dangerously-skip-permissions --print 2>&1 | tee /dev/stderr) || true
  fi

  if echo "$OUTPUT" | grep -q "<promise>COMPLETE</promise>"; then
    echo ""
    echo "Ralph completed all tasks! (Session: $SESSION_ID)"
    echo "Completed at iteration $i of $MAX_ITERATIONS"
    exit 0
  fi

  echo "Iteration $i complete. Continuing..."
  sleep 2
done

echo ""
echo "Ralph reached max iterations ($MAX_ITERATIONS)."
echo "Session: $SESSION_ID"
echo "Check $PROGRESS_FILE for status."
exit 1
