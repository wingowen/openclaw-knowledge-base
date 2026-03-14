# GitHub 仓库创建示例

## 快速开始

### 1. 首次使用 - 登录 GitHub
```bash
gh auth login
```
选择: 
- GitHub.com
- HTTPS
- 登录浏览器
- 输入验证码

### 2. 创建仓库

#### 方法1: 使用 GitHub CLI
```bash
# 创建公开仓库
gh repo create my-new-project --public

# 创建私有仓库
gh repo create my-private-project --private

# 创建带描述的仓库
gh repo create my-awesome-project --description "我的酷炫项目" --public
```

#### 方法2: 使用交互式脚本
```bash
./github_repo_creator.sh
# 然后选择选项2创建仓库
```

#### 方法3: 使用 hub
```bash
# 创建公开仓库
hub create my-new-project

# 创建私有仓库
hub create --private my-private-project
```

### 3. 推送代码到新仓库
```bash
# 初始化本地仓库
git init
git add .
git commit -m "Initial commit"

# 添加远程仓库（根据创建时的输出）
git remote add origin https://github.com/username/my-repo.git

# 推送到 GitHub
git push -u origin main
```

## 常用命令

### GitHub CLI
```bash
# 查看仓库信息
gh repo view

# 克隆仓库
gh repo clone username/repo

# 删除仓库
gh repo delete my-repo --yes
```

### hub
```bash
# 查看仓库信息
hub browse

# 克隆仓库
hub clone username/repo

# 删除仓库
hub delete my-repo
```

## API 直接调用
```bash
# 创建公开仓库
curl -X POST \
  -H "Authorization: token YOUR_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  -d '{"name":"my-repo"}' \
  https://api.github.com/user/repos
```

## 注意事项

1. 仓库名称只能包含字母、数字、下划线和连字符
2. 创建私有仓库可能需要付费账户
3. 确保网络连接正常
4. 首次使用前必须进行身份验证