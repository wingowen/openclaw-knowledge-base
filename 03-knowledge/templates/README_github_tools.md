# GitHub 仓库创建工具

本工具集包含多种方式来创建 GitHub 仓库：

## 已安装的工具

### 1. GitHub CLI (gh)
- **版本**: 2.86.0
- **用途**: GitHub 官方命令行工具
- **安装路径**: `/usr/local/bin/gh`

### 2. hub
- **版本**: 2.14.2
- **用途**: GitHub 的增强命令行工具
- **安装路径**: `/usr/local/bin/hub`

### 3. curl
- **用途**: 用于直接调用 GitHub API
- **安装路径**: `/usr/bin/curl`

## 使用方法

### 方法1: 交互式脚本
```bash
./github_repo_creator.sh
```

### 方法2: 直接使用 GitHub CLI
```bash
# 登录 GitHub
gh auth login

# 创建公开仓库
gh repo create my-repo --public

# 创建私有仓库
gh repo create my-private-repo --private

# 创建带描述的仓库
gh repo create my-repo --description "我的项目描述" --public
```

### 方法3: 使用 hub
```bash
# 创建公开仓库
hub create my-repo

# 创建私有仓库
hub create --private my-private-repo

# 创建带描述的仓库
hub create -d "我的项目描述" my-repo
```

### 方法4: 使用 API
```bash
curl -X POST \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  -d '{"name":"my-repo","description":"我的项目描述","private":false}' \
  https://api.github.com/user/repos
```

## 交互式脚本功能

脚本提供以下功能：
1. **检查工具**: 检查已安装的 GitHub 工具
2. **GitHub CLI 创建**: 使用官方 CLI 创建仓库
3. **hub 创建**: 使用 hub 工具创建仓库
4. **API 创建**: 直接使用 GitHub API 创建仓库

## 配置 GitHub

### 使用 GitHub CLI 登录
```bash
gh auth login
```

### 配置 Git
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### 创建 SSH 密钥 (可选)
```bash
ssh-keygen -t ed25519 -C "your.email@example.com"
# 添加公钥到 GitHub: https://github.com/settings/keys
```

## 推荐工作流程

1. 首次使用时运行 `./github_repo_creator.sh` 选择选项1检查工具
2. 使用 GitHub CLI 登录: `gh auth login`
3. 使用交互式脚本或直接命令创建仓库
4. 本地创建项目并推送到 GitHub

## 注意事项

- 使用 GitHub CLI 和 hub 需要 GitHub 身份验证
- API 方法需要 personal access token
- 创建仓库前确保网络连接正常
- 仓库名称只能包含字母、数字、下划线和连字符