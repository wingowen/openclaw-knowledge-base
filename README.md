# OpenClaw Knowledge Base

> 用于 OpenClaw 迁移恢复的结构化记忆仓库

## 🎯 目的

本仓库用于在**新机器上安装 OpenClaw 时恢复所有相关信息**，包括：
- 长期记忆 (MEMORY.md)
- 每日日志 (memory/)
- 知识库 (knowledge-base/)
- 配置和经验总结

## 📦 恢复步骤

在新机器上安装 OpenClaw 后：

```bash
# 1. 克隆本仓库
git clone https://github.com/wingowen/openclaw-knowledge-base.git ~/.openclaw/workspace

# 2. 进入工作目录
cd ~/.openclaw/workspace

# 3. 执行恢复脚本（如有）
chmod +x restore.sh && ./restore.sh
```

## 📁 目录结构

```
├── MEMORY.md              # 长期精选记忆
├── memory/                # 每日原始日志 (YYYY-MM-DD.md)
├── knowledge-base/        # 结构化知识库
│   ├── 01-persona/        # 身份与角色定义
│   ├── 02-projects/       # 项目文档
│   ├── 03-tasks/          # 任务追踪
│   ├── 04-learnings/      # 学习与经验
│   └── 05-archive/        # 归档资料
└── README.md              # 本说明文件
```

## 🔄 同步命令

```bash
# 推送到 GitHub
git add -A
git commit -m "update: description"
git push

# 从 GitHub 拉取
git pull
```

## 📝 维护建议

- **每日**: 自动记录到 `memory/YYYY-MM-DD.md`
- **每周**: 整理重要内容到 `MEMORY.md`
- **重要决策**: 即时更新 `knowledge-base/`

---

*Last updated: 2026-02-12*
