#context-engineering #core-skill

> [!info] 基本信息
> 来源: [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
> 发布: 2025-09-29 | 难度: 🔵 基础 | 状态: ⬜ 未开始 | 约 50 分钟

## 章节概括

### 从 Prompt Engineering 到 Context Engineering
Prompt Engineering → 写好指令；Context Engineering → **管理整个上下文状态**（指令、工具、MCP、外部数据、消息历史）。Agent 循环产生越来越多数据，每次推理都需要精心筛选。

### 为什么 Context 很重要？
- **Context Rot**：上下文窗口越大，信息召回精度越低
- LLM 有"注意力预算"（attention budget），每增加 token 都在消耗
- Transformer 架构：n 个 token 产生 n² 成对关系，注意力被拉薄
- 核心原则：**最小高信号 token 集合，最大化期望结果概率**

### System Prompt 设计
- 避免两个极端：硬编码 if-else vs 模糊笼统指导
- 用 XML/Markdown 分区组织（`<background_information>`, `<instructions>`, `<tool_guidance>`）
- 从最小 prompt 开始测试 → 基于失败模式添加指令

### 工具设计
- 工具定义了 Agent 与环境的契约
- 常见问题：工具集臃肿、功能重叠、选择模糊
- 如果人类工程师都无法判断用哪个工具，Agent 更不可能

### Few-shot 示例
- 选**多样化、典型**示例，不要罗列所有边界情况
- 示例是"一幅图抵千言"

### Context 检索与 Agentic Search
- **预处理检索**：传统 embedding-based RAG
- **Just-in-Time 检索**：Agent 持有轻量引用（文件路径、链接），运行时按需加载
- Claude Code 用混合策略：CLAUDE.md 预加载 + glob/grep 按需探索
- Agent 自主导航实现**渐进式披露**（progressive disclosure）

### 长时间任务
- 上下文会无限增长 → 需要压缩、总结、裁剪策略
- Agent 要学会"放下"不相关的历史

## 学习笔记
（待阅读后补充）

---

#context-engineering #core-skill
