#tool-design #core-skill

> [!info] 基本信息
> 来源: [Writing effective tools for agents — with agents](https://www.anthropic.com/engineering/writing-tools-for-agents)
> 发布: 2025-09-11 | 难度: 🔵 基础 | 状态: ⬜ 未开始 | 约 40 分钟

## 章节概括

### 工具的本质转变
传统软件：确定性系统之间的契约。Agent 工具：确定性系统与**非确定性 Agent** 之间的契约。需要完全不同的设计思路。

### 开发流程
1. **构建原型**：快速搭起 MCP Server，本地测试
2. **运行评测**：生成真实任务 prompt，测量工具使用准确率
3. **与 Agent 协作优化**：把评测 transcript 喂给 Claude Code 分析改进

### 评测方法论
- 任务要**复杂真实**（多步骤、多工具），不要简单沙盒
- 每个 prompt 配可验证的结果
- 收集额外指标：运行时间、工具调用数、token 消耗、工具错误率
- 读 transcript 要**读言外之意**：LLM 不总是说它真正的意思

### 核心原则

| 原则 | 要点 |
|------|------|
| **选对工具** | 不要简单包装 API endpoint；合并相关操作为一个高层工具 |
| **命名空间** | 多 MCP Server 时用 `server.tool_name` 前缀避免冲突 |
| **返回有意义的上下文** | 返回足够但精简的上下文给 Agent |
| **Token 效率** | 控制响应大小，避免无用信息填满上下文 |
| **Prompt-engineer 工具描述** | 工具描述和 schema 本身需要 prompt engineering |

### 工具合并示例
- ❌ `list_users` + `list_events` + `create_event`
- ✅ `schedule_event`（查可用时间 + 创建 + 通知一条龙）

### 常见反模式
- 工具太多或功能重叠 → Agent 选择困难
- 返回原始数据量过大 → 上下文爆炸
- 描述模糊 → Agent 误用工具

## 学习笔记
（待阅读后补充）

---

#tool-design #core-skill
