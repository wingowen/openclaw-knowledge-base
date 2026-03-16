#multi-agent #parallel-computing

> [!info] 基本信息
> 来源: [Building a C compiler with a team of parallel Claudes](https://www.anthropic.com/engineering/building-c-compiler)
> 发布: 2026-02-05 | 难度: 🔴 前沿 | 状态: ⬜ 未开始 | 约 40 分钟

## 章节概括

### 项目概述
16 个 Claude 并行协作，从零写一个 Rust 实现的 C 编译器，能编译 Linux 6.9 内核（x86/ARM/RISC-V）。近 2000 次 Claude Code 会话，$20,000 API 成本，产出 100,000 行代码。

### Agent 架构
- **无限循环**：Claude 完成任务后立即接下一个（`while true; do claude ...; done`）
- **Docker 容器隔离**：每个 Agent 有独立容器
- **Git 协作**：共享 bare repo，Agent 各自 clone → 修改 → push
- **文件锁同步**：`current_tasks/` 目录下的文本文件防止重复劳动
- **无 Orchestration Agent**：每个 Claude 自己决定做什么

### 关键经验

#### 1. 写高质量测试
- 测试必须近乎完美，否则 Agent 会"解错题"
- CI 管道防止新 commit 破坏已有功能
- 持续发现新的失败模式 → 设计新测试

#### 2. 设身处地为 Agent 着想
- Agent 每次启动没有上下文 → 需要 README + 进度文件
- **上下文污染**：测试输出不能刷屏，重要信息写 log 文件
- **时间盲**：Claude 不知道时间，可能花几小时跑测试而不推进 → 需要 `--fast` 快速测试

#### 3. 测试驱动开发
- 测试套件是 Agent 的导航系统
- 能通过测试 = 做对了（Agent 自己验证）

### 局限性
- 研究原型，无进程间通信
- 无高层目标管理
- 每个 Agent 独立决策
- 合并冲突频繁（但 Claude 能处理）

## 学习笔记
（待阅读后补充）

---

#multi-agent #parallel-computing
