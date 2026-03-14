#!/bin/bash

# GitHub 仓库创建工具脚本
# 支持使用 GitHub CLI (gh) 和 hub 工具

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}[$(date '+%Y-%m-%d %H:%M:%S')] ${message}${NC}"
}

# 检查工具是否安装
check_tools() {
    print_message $GREEN "检查已安装的 GitHub 工具..."
    
    if command -v gh &> /dev/null; then
        GH_VERSION=$(gh --version)
        print_message $GREEN "✓ GitHub CLI (gh) 已安装: ${GH_VERSION}"
    else
        print_message $RED "✗ GitHub CLI (gh) 未安装"
    fi
    
    if command -v hub &> /dev/null; then
        HUB_VERSION=$(hub --version)
        print_message $GREEN "✓ hub 已安装: ${HUB_VERSION}"
    else
        print_message $RED "✗ hub 未安装"
    fi
    
    if command -v git &> /dev/null; then
        GIT_VERSION=$(git --version)
        print_message $GREEN "✓ git 已安装: ${GIT_VERSION}"
    else
        print_message $RED "✗ git 未安装"
    fi
}

# 使用 GitHub CLI 创建仓库
create_repo_with_gh() {
    local repo_name=$1
    local description=$2
    local private=$3
    
    print_message $YELLOW "使用 GitHub CLI 创建仓库: ${repo_name}"
    
    # 检查是否已登录
    if ! gh auth status &> /dev/null; then
        print_message $RED "请先登录 GitHub: gh auth login"
        return 1
    fi
    
    # 创建仓库
    local cmd="gh repo create ${repo_name}"
    if [ -n "$description" ]; then
        cmd="${cmd} --description \"${description}\""
    fi
    if [ "$private" = "true" ]; then
        cmd="${cmd} --private"
    else
        cmd="${cmd} --public"
    fi
    
    eval $cmd
}

# 使用 hub 创建仓库
create_repo_with_hub() {
    local repo_name=$1
    local description=$2
    local private=$3
    
    print_message $YELLOW "使用 hub 创建仓库: ${repo_name}"
    
    # 检查是否已登录
    if ! git remote -v | grep -q "github.com"; then
        print_message $RED "请先配置 git 和 GitHub: git remote add origin ..."
        return 1
    fi
    
    # 创建仓库
    local cmd="hub create"
    if [ "$private" = "true" ]; then
        cmd="${cmd} --private"
    fi
    if [ -n "$description" ]; then
        cmd="${cmd} -d \"${description}\""
    fi
    
    eval $cmd
}

# 使用 API 创建仓库
create_repo_with_api() {
    local repo_name=$1
    local description=$2
    local private=$3
    local token=$4
    
    print_message $YELLOW "使用 GitHub API 创建仓库: ${repo_name}"
    
    if [ -z "$token" ]; then
        print_message $RED "GitHub token is required for API creation"
        return 1
    fi
    
    local payload="{\"name\":\"${repo_name}\""
    if [ -n "$description" ]; then
        payload="${payload},\"description\":\"${description}\""
    fi
    if [ "$private" = "true" ]; then
        payload="${payload},\"private\":true"
    fi
    payload="${payload}}"
    
    curl -X POST \
        -H "Authorization: token ${token}" \
        -H "Accept: application/vnd.github.v3+json" \
        -d "${payload}" \
        https://api.github.com/user/repos
}

# 主菜单
show_menu() {
    echo ""
    echo "=== GitHub 仓库创建工具 ==="
    echo "1. 检查已安装的工具"
    echo "2. 使用 GitHub CLI 创建仓库"
    echo "3. 使用 hub 创建仓库"
    echo "4. 使用 API 创建仓库"
    echo "5. 退出"
    echo ""
    read -p "请选择操作 (1-5): " choice
}

# 主程序
main() {
    while true; do
        show_menu
        
        case $choice in
            1)
                check_tools
                ;;
            2)
                read -p "仓库名称: " repo_name
                read -p "仓库描述 (可选): " description
                read -p "私有仓库? (y/n): " private_choice
                private=$( [ "$private_choice" = "y" ] && echo "true" || echo "false" )
                create_repo_with_gh "$repo_name" "$description" "$private"
                ;;
            3)
                read -p "仓库名称: " repo_name
                read -p "仓库描述 (可选): " description
                read -p "私有仓库? (y/n): " private_choice
                private=$( [ "$private_choice" = "y" ] && echo "true" || echo "false" )
                create_repo_with_hub "$repo_name" "$description" "$private"
                ;;
            4)
                read -p "仓库名称: " repo_name
                read -p "仓库描述 (可选): " description
                read -p "私有仓库? (y/n): " private_choice
                private=$( [ "$private_choice" = "y" ] && echo "true" || echo "false" )
                read -p "GitHub token: " token
                create_repo_with_api "$repo_name" "$description" "$private" "$token"
                ;;
            5)
                print_message $GREEN "退出程序"
                exit 0
                ;;
            *)
                print_message $RED "无效选择，请重新输入"
                ;;
        esac
        
        echo ""
        read -p "按 Enter 继续..."
    done
}

# 如果脚本被直接执行，则运行主程序
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi