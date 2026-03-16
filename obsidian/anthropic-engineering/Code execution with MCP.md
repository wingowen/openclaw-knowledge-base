#mcp #agent-efficiency

> [!info] 基本信息
> 来源: [Code execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp)
> 发布: 2025-11-04 | 难度: 🟣 进阶 | 状态: ⬜ 未开始 | 约 35 分钟

## 章节概括

### 问题：工具消耗太多 Token
两大问题：
1. **工具定义超载**：5 个 MCP Server / 58 个工具 ≈ 55K token（工具描述全塞进上下文）
2. **中间结果膨胀**：大文档（如 2 小时会议记录 50K token）在工具调用间流经上下文

### 解决方案：Code Execution with MCP
MCP Server 以**代码 API**（而非直接工具调用）呈现。Agent 写代码调用工具。

### 实现方式
- 文件树结构：`servers/google-drive/getDocument.ts`
- 每个工具对应一个 TypeScript 文件
- Agent 按需探索文件系统加载工具定义

```
原始：150K token（全量工具定义）
优化后：2K token（只加载需要的）
节省：98.7%
```

### 核心优势

| 优势 | 说明 |
|------|------|
| **渐进式披露** | 按需读取文件系统发现工具 |
| **上下文高效结果** | 代码中过滤/聚合，只返回精简结果 |
| **强大控制流** | 循环/条件/错误处理用代码表达，不用链式工具调用 |
| **隐私保护** | 敏感数据在沙箱中处理，不流经模型上下文 |

### 示例对比
- 传统：10,000 行表格全进入上下文 → 模型手动过滤
- 代码：`allRows.filter(row => row.Status === 'pending')` → 只返回 5 行摘要

### 与 Cloudflare "Code Mode" 概念一致
核心洞察：LLM 擅长写代码，利用这个优势让 Agent 更高效地交互。

## 学习笔记
（待阅读后补充）

---

#mcp #agent-efficiency
