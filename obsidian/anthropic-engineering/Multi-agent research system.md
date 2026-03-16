#multi-agent #system-design

> [!info] 基本信息
> 来源: [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)
> 发布: 2025-06-13 | 难度: 🟣 进阶 | 状态: ⬜ 未开始 | 约 60 分钟

## 章节概括

### 为什么研究任务需要多 Agent？
研究是开放式问题，无法预定义步骤。多 Agent 本质是**扩展 token 预算**——每个子 Agent 有独立上下文窗口，并行探索后压缩发现给主 Agent。

### 性能数据
- 多 Agent（Opus 4 领导 + Sonnet 4 子 Agent）比单 Agent Opus 4 强 **90.2%**
- token 使用：多 Agent ≈ 单 Agent 的 **15 倍**，聊天的 15 倍
- 三个因素解释 BrowseComp 95% 方差：token 用量（80%）、工具调用数、模型选择

### 架构：Orchestrator-Worker
- **Lead Agent**：分析查询 → 制定策略 → 派发子 Agent → 综合结果
- **Subagents**：独立搜索，各自有上下文窗口和工具
- **CitationAgent**：最终处理引用归属
- **Memory**：用文件持久化计划（上下文窗口超 200K 会被截断）

### Prompt Engineering 经验
1. **像你的 Agent 一样思考**：用 Console 构建模拟，逐步观察失败模式
2. **教 Orchestrator 委派**：每个子 Agent 需要明确的目标、输出格式、工具指导、任务边界
3. **按查询复杂度调力度**：简单查事实 1 个 Agent / 3-10 次工具调用；复杂研究 >10 个子 Agent
4. **工具设计至关重要**：工具描述差会把 Agent 带偏；给明确启发式规则
5. **让 Agent 自我改进**：Claude 4 能诊断失败原因并改进 prompt

### 失败模式
- 简单查询生成 50 个子 Agent
- 搜索不存在的信息源无限循环
- 子 Agent 之间互相干扰
- 进度未持久化导致重复工作

## 学习笔记
（待阅读后补充）

---

#multi-agent #system-design
