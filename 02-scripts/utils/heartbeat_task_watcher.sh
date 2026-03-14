#!/bin/bash
# Heartbeat task watcher - checks for incomplete tasks and resumes them
# Runs every 5 minutes via cron

LOG_FILE="/root/.openclaw/workspace/memory/heartbeat/task_watcher.log"
HEARTBEAT_DIR="/root/.openclaw/workspace/memory/heartbeat"
STATE_FILE="${HEARTBEAT_DIR}/task_state.json"

# Create directories if not exist
mkdir -p "$HEARTBEAT_DIR"

# Timestamp
NOW=$(date -Iseconds)
echo "[$NOW] Starting heartbeat task check..." >> "$LOG_FILE"

# Check for incomplete subagent tasks
# Use sessions_list to find active sessions that might be stuck
/usr/bin/openclaw sessions --json 2>/dev/null > "${HEARTBEAT_DIR}/sessions_${NOW}.json" || echo '[]' > "${HEARTBEAT_DIR}/sessions_${NOW}.json"

# Count active sessions (default to 0 if jq fails)
ACTIVE_SESSIONS=$(jq '[.[] | select(.active==true)] | length' "${HEARTBEAT_DIR}/sessions_${NOW}.json" 2>/dev/null || echo 0)
ACTIVE_SESSIONS=${ACTIVE_SESSIONS:-0}

# Check if any tasks need resuming
if [ "$ACTIVE_SESSIONS" -gt 0 ]; then
    echo "[$NOW] Found $ACTIVE_SESSIONS active sessions, checking for stuck tasks..." >> "$LOG_FILE"
  
    # Send heartbeat to main session to trigger task check
    /usr/bin/openclaw sessions send --sessionKey "agent:main:main" --message "HEARTBEAT_CHECK: Check for incomplete tasks and resume if needed" 2>/dev/null >> "$LOG_FILE"
  
    echo "[$NOW] Heartbeat signal sent to main session." >> "$LOG_FILE"
else
    echo "[$NOW] No active sessions detected." >> "$LOG_FILE"
fi

# Update state file
cat > "$STATE_FILE" << EOF
{
  "last_check": "$NOW",
  "active_sessions": $ACTIVE_SESSIONS,
  "status": "checked"
}
EOF

echo "[$NOW] Heartbeat check complete." >> "$LOG_FILE"
echo "" >> "$LOG_FILE"