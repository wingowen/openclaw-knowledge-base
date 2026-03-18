#!/bin/bash
# 知识库每小时自动 Git Push
set -euo pipefail

WORKSPACE="/root/.openclaw/workspace"
LOG() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

cd "$WORKSPACE"

# Check if there are changes
if git diff --quiet HEAD -- 2>/dev/null && [ -z "$(git ls-files --others --exclude-standard 2>/dev/null)" ]; then
    LOG "No changes, skip"
    exit 0
fi

# Stage, commit, push
git add -A
MSG="Auto backup $(date '+%Y-%m-%d %H:%M')"
git commit -m "$MSG" --allow-empty 2>/dev/null || true
git push origin HEAD 2>/dev/null || git push origin main 2>/dev/null || git push origin master 2>/dev/null || {
    LOG "Push failed"
    exit 1
}

LOG "Pushed successfully"
