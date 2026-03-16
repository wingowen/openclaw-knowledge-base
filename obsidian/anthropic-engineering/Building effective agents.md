#agent-architecture #foundation

> [!info] 基本信息
> 来源: [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
> 发布: 2024-12-19 | 难度: 🟢 入门 | 状态: ⬜ 未开始 | 约 40 分钟

## 章节概括

### 什么是 Agent？
Agent 的定义：系统中 LLM 动态自主控制工具调用和执行流程。与 **Workflow**（预定义代码路径编排）形成关键区别。统一称为 "agentic systems"。

### 什么时候用 Agent？
- **不要用**：简单任务优化单次 LLM 调用就够了（检索 + 上下文示例）
- **用 Workflow**：任务明确、需要可预测性和一致性
- **用 Agent**：需要灵活的模型驱动决策、无法预定义执行路径
- 核心原则：**从最简方案开始，只在必要时增加复杂度**

### 基础组件：Augmented LLM
Agent 系统的基础积木——带检索、工具、记忆增强的 LLM。推荐通过 MCP 集成第三方工具。

### 五种 Workflow 模式

| 模式 | 核心思路 | 适用场景 |
|------|---------|---------|
| **Prompt Chaining** | 任务拆成链式步骤，每步 LLM 调用处理上一步输出 | 可明确分解的子任务（写文案→翻译） |
| **Routing** | 输入分类后路由到专用处理流程 | 客服分流、大小模型成本优化 |
| **Parallelization** | 多个 LLM 同时处理子任务，结果聚合 | 安全审核、多维度评估 |
| **Orchestrator-Workers** | 中央 LLM 动态拆解任务分配给 Worker | 多文件代码修改、跨源信息搜集 |
| **Evaluator-Optimizer** | 一个生成一个评估，循环迭代优化 | 文学翻译、多轮搜索分析 |

### 真正的 Agent
- LLM 基于环境反馈在循环中使用工具
- 适合开放式问题、无法预判步骤数量
- 本质简单：LLM + 工具 + 反馈循环
- 风险：成本高、错误累积 → 需要沙箱测试 + 护栏

### 核心原则
1. **保持设计简洁**
2. **透明展示规划步骤**
3. **精心设计 Agent-Computer Interface (ACI)** — 工具文档和测试

## 学习笔记
（待阅读后补充）

---

#agent-architecture #foundation
