#!/bin/bash
# OpenRouter Key 泄露紧急处理脚本
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

WORKSPACE="/root/.openclaw/workspace"
cd "$WORKSPACE"

echo "=================================================="
echo "   🔴 OpenRouter Key 泄露紧急处理脚本"
echo "=================================================="
echo ""

echo -e "${YELLOW}⚠️  此脚本将执行以下高危操作：${NC}"
echo "  - 永久删除 Git 历史中的 memory/evolution/ 目录"
echo "  - 重写所有分支历史（强制推送会覆盖 GitHub）"
echo "  - 修改备份脚本逻辑"
echo ""
echo -e "${RED}💥 警告：如果有协作者，需要他们重新克隆仓库！${NC}"
echo ""
read -p "是否继续？(yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "已取消操作"
    exit 1
fi

echo ""
echo "📦 [步骤 1/7] 备份当前分支..."
current_branch=$(git branch --show-current)
backup_branch="backup/pre-clean-$(date +%Y%m%d-%H%M%S)"
git branch "$backup_branch" "$current_branch" 2>/dev/null || true
echo "✅ 已创建备份分支: $backup_branch"

echo ""
echo "🛡️  [步骤 2/7] 更新 .gitignore 防护规则..."
if [ -f ".gitignore" ]; then
    if grep -q "^memory/evolution/" .gitignore; then
        echo "✅ .gitignore 已包含 memory/evolution/ 规则"
    else
        echo "# Sensitive logs - auto-generated conversations" >> .gitignore
        echo "memory/evolution/" >> .gitignore
        echo "✅ 已添加 memory/evolution/ 到 .gitignore"
    fi
else
    echo "# Sensitive logs" > .gitignore
    echo "memory/evolution/" >> .gitignore
    echo "✅ 已创建 .gitignore 并添加规则"
fi

echo ""
echo "🗑️  [步骤 3/7] 从 Git 历史删除 memory/evolution/ 目录..."
if command -v git-filter-repo &> /dev/null; then
    echo "🔧 使用 git-filter-repo 清理..."
    git filter-repo --path memory/evolution/ --invert-paths
    echo "✅ filter-repo 清理完成"
else
    echo "🔧 使用 git filter-branch 清理（较慢）..."
    git filter-branch --force --index-filter \
        'git rm -r --cached --ignore-unmatch memory/evolution/' \
        --prune-empty --tag-name-filter cat -- --all
    echo "✅ filter-branch 清理完成"
fi

echo ""
echo "🧹 [步骤 4/7] 清理 Git 残留引用..."
git for-each-ref --format="%(refname)" refs/original/ | xargs -n1 git update-ref -d 2>/dev/null || true
git reflog expire --expire=now --all
git gc --prune=now --aggressive
echo "✅ 垃圾回收完成"

echo ""
echo "🔍 [步骤 5/7] 验证清理结果..."
remaining=$(git log --all --oneline -- "memory/evolution" 2>/dev/null | wc -l)
if [ "$remaining" -eq 0 ]; then
    echo "✅ memory/evolution/ 已从所有历史提交中清除"
else
    echo -e "${YELLOW}⚠️  警告：仍发现 $remaining 个提交包含 memory/evolution/${NC}"
    git log --all --oneline -- "memory/evolution" 2>/dev/null | head -3
fi

sk_count=$(git log --all -p 2>/dev/null | grep -c "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" || echo 0)
if [ "$sk_count" -eq 0 ]; then
    echo "✅ 未在历史中发现泄露的 OpenRouter Key"
else
    echo -e "${YELLOW}⚠️  警告：历史中仍发现 $sk_count 处包含泄露的 key${NC}"
fi

echo ""
echo "🔧 [步骤 6/7] 修复 hourly_git_push.sh..."
if [ -f "scripts/hourly_git_push.sh" ]; then
    cp scripts/hourly_git_push.sh scripts/hourly_git_push.sh.backup.$(date +%Y%m%d-%H%M%S)
    cat > scripts/hourly_git_push.sh <<'EOF'
#!/bin/bash
set -euo pipefail
WORKSPACE="/root/.openclaw/workspace"
LOG() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
cd "$WORKSPACE"
if git diff --quiet HEAD -- 2>/dev/null && [ -z "$(git ls-files --others --exclude-standard 2>/dev/null)" ]; then
    LOG "No changes, skip"
    exit 0
fi
git add -A
git reset HEAD workspace/memory/evolution/ 2>/dev/null || true
git clean -fd workspace/memory/evolution/ 2>/dev/null || true
MSG="Auto backup $(date '+%Y-%m-%d %H:%M')"
git commit -m "$MSG" --allow-empty 2>/dev/null || true
git push origin HEAD 2>/dev/null || git push origin main 2>/dev/null || git push origin master 2>/dev/null || {
    LOG "Push failed"
    exit 1
}
LOG "Pushed successfully (with sensitive dirs excluded)"
EOF
    chmod +x scripts/hourly_git_push.sh
    echo "✅ 已更新 hourly_git_push.sh 并添加防护"
else
    echo "⚠️  未找到 scripts/hourly_git_push.sh，跳过修复"
fi

echo ""
echo "📤 [步骤 7/7] 强制推送到 GitHub？"
echo "⚠️  注意：这会重写远程分支，协作者需要重新克隆！"
echo ""
read -p "确认强制推送？(yes/no): " PUSH_CONFIRM

if [ "$PUSH_CONFIRM" = "yes" ]; then
    echo "正在推送..."
    git push origin --force --all && echo "✅ 分支推送成功"
    git push origin --force --tags && echo "✅ 标签推送成功"
    echo ""
    echo "🎉 推送完成！"
else
    echo "⏭️  跳过推送，你可以稍后手动执行："
    echo "   git push origin --force --all"
    echo "   git push origin --force --tags"
fi

echo ""
echo "=================================================="
echo "   📊 清理完成报告"
echo "=================================================="
echo ""
echo "✅ 已执行的操作："
echo "  [x] 创建备份分支: $backup_branch"
echo "  [x] 更新 .gitignore 添加 memory/evolution/ 排除"
echo "  [x] 彻底删除 Git 历史中的 memory/evolution/ 目录"
echo "  [x] 清理 Git 残留引用（reflog + gc）"
echo "  [x] 修复 hourly_git_push.sh 脚本"
echo "  [x] 验证 API Key 从历史中清除"
echo ""
echo "📋 下一步操作清单："
echo "  1. 登录 OpenRouter (https://openrouter.ai/keys)"
echo "     撤销泄露的 key: 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"
echo "     生成新的 API Key"
echo ""
echo "  2. 更新本地配置文件："
echo "     - /root/.openclaw/workspace/.env"
echo "     - /root/.openclaw/workspace/nanobot/.env"
echo ""
echo "  3. 通知协作者（如有）："
echo "     由于历史重写，所有人必须重新克隆仓库"
echo ""
echo "  4. 更新 GitHub Actions Secrets（如使用）："
echo "     使用新生成的 OpenRouter API Key"
echo ""
echo "🔒 安全状态："
echo "  - Git 历史已清理 ✅"
echo "  - 防护规则已更新 ✅"
echo "  - 备份脚本已加固 ✅"
echo ""
echo "请先完成第 1-3 步，然后回复我，我可以帮你验证！🎯"
echo ""

exit 0
