# GitHub 工具集

> WSL2 环境下 GitHub 操作的工具配置与使用指南

## 🛠️ 已安装工具

### 1. GitHub CLI (gh)
- **版本**: 2.86.0
- **路径**: `/usr/local/bin/gh`
- **用途**: GitHub 官方命令行工具

### 2. hub
- **版本**: 2.14.2
- **路径**: `/usr/local/bin/hub`
- **用途**: GitHub 增强命令行工具

### 3. curl
- **版本**: 7.88.1
- **路径**: `/usr/bin/curl`
- **用途**: 直接调用 GitHub API

## 📦 创建的文件

| 文件 | 说明 |
|------|------|
| `github_repo_creator.sh` | 交互式仓库创建脚本 |
| `README_github_tools.md` | 详细使用说明 |
| `test_github_tools.sh` | 快速测试脚本 |
| `github_examples.md` | 使用示例 |

## 🚀 快速开始

### 首次配置
```bash
gh auth login
```

### 创建仓库
```bash
# 方法1: 交互式
./github_repo_creator.sh

# 方法2: 直接命令
gh repo create my-repo --public

# 方法3: 使用 hub
hub create my-repo
```

## ⚠️ 注意事项

1. **认证**: 首次使用必须执行 `gh auth login`
2. **命名限制**: 仓库名只能包含字母、数字、下划线、连字符
3. **私有仓库**: 可能需要 GitHub 付费账户

## 📚 相关资源

- `/root/.openclaw/workspace/github_repo_creator.sh`
- `/root/.openclaw/workspace/README_github_tools.md`
