#!/bin/bash

# 快速测试 GitHub 工具
echo "=== GitHub 工具快速测试 ==="

# 检查 gh
echo "1. 检查 GitHub CLI..."
if command -v gh &> /dev/null; then
    echo "✓ GitHub CLI 已安装: $(gh --version)"
else
    echo "✗ GitHub CLI 未安装"
fi

# 检查 hub
echo "2. 检查 hub..."
if command -v hub &> /dev/null; then
    echo "✓ hub 已安装: $(hub --version)"
else
    echo "✗ hub 未安装"
fi

# 检查 git
echo "3. 检查 git..."
if command -v git &> /dev/null; then
    echo "✓ git 已安装: $(git --version)"
else
    echo "✗ git 未安装"
fi

# 检查 curl
echo "4. 检查 curl..."
if command -v curl &> /dev/null; then
    echo "✓ curl 已安装: $(curl --version | head -n 1)"
else
    echo "✗ curl 未安装"
fi

echo ""
echo "=== 使用说明 ==="
echo "使用交互式脚本: ./github_repo_creator.sh"
echo "或直接使用命令:"
echo "  gh repo create <repo-name> --public"
echo "  hub create <repo-name> --private"
echo ""
echo "首次使用前请运行: gh auth login"