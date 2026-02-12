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
│
├── 📈 A股量价策略回测项目
│   ├── 数据获取
│   │   ├── stock_data_manager.py  # 数据缓存系统
│   │   └── get_multi_stocks.py    # 多股票获取
│   │
│   ├── 策略回测
│   │   ├── strategy_ranker.py      # 单股票策略回测
│   │   └── multi_stock_backtest.py # 多股票汇总回测
│   │
│   ├── stock_data/              # 股票数据 (CSV)
│   │   ├── 600519.csv  # 贵州茅台
│   │   ├── 600036.csv  # 招商银行
│   │   └── ...
│   │
│   └── README量价策略.md        # 项目说明
│
└── README.md              # 本说明文件
```

## 📈 A股量价策略回测项目

### 项目概述

用真实A股数据验证15种量价策略的有效性。

### 核心发现

| 策略类型 | 结论 |
|----------|------|
| **缩量策略** | ✅ 整体有效 (胜率56-58%) |
| **放量策略** | ❌ 整体无效 (胜率<50%) |
| **核心假设** | "放量买入"策略胜率仅47% |

### 运行方式

```bash
# 获取股票数据
python3 get_multi_stocks.py

# 单股票回测
python3 strategy_ranker.py

# 多股票汇总
python3 multi_stock_backtest.py
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
