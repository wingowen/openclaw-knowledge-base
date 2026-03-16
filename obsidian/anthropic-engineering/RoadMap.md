> [!abstract] 学习路径总览
> 系统掌握 LLM 工程化知识，从基础概念到高级 Agent 架构设计。
> 来源：https://www.anthropic.com/engineering

```
入门篇 ──▶ 基础篇 ──▶ 进阶篇 ──▶ 前沿篇
  │          │          │          │
  ▼          ▼          ▼          ▼
概念认知     核心技能    系统设计    工程前沿
(1-2周)     (2-3周)    (3-4周)    (持续关注)
```

## 🟢 入门篇（概念认知）— 1-2 周

| # | 笔记文件 | 核心收获 |
|---|---------|---------|
| 1 | [[Building effective agents]] | Agent 架构框架：Workflow vs Agent、5 种工作流模式 |
| 2 | [[Claude Code Best practices]] | 编码 Agent 的实战技巧、跨平台使用 |
| 3 | [[Claude think tool]] | "暂停思考"机制与 τ-Bench 评测结果 |

## 🔵 基础篇（核心技能）— 2-3 周

| # | 笔记文件 | 核心收获 |
|---|---------|---------|
| 4 | [[Effective context engineering]] | Context 工程：注意力预算、上下文管理、JIT 检索 |
| 5 | [[Writing tools for agents]] | 工具设计：评测驱动、命名空间、Token 效率 |
| 6 | [[Contextual Retrieval]] | RAG 增强：Contextual Embedding + BM25，失败率降 49% |
| 7 | [[Advanced tool use]] | Tool Search、Programmatic Calling、Use Examples |

## 🟣 进阶篇（系统设计）— 3-4 周

| # | 笔记文件 | 核心收获 |
|---|---------|---------|
| 8 | [[Multi-agent research system]] | 多 Agent 协作：Orchestrator-Worker、Token 扩展策略 |
| 9 | [[Effective harnesses for long-running agents]] | 长运行 Agent：Initializer + Coding Agent 模式 |
| 10 | [[Code execution with MCP]] | MCP + 代码执行：Token 消耗降低 98.7% |
| 11 | [[Claude Code sandboxing]] | 安全沙箱：文件系统 + 网络隔离，权限弹窗降 84% |

## 🔴 前沿篇（持续关注）— 按兴趣选读

| # | 笔记文件 | 核心收获 |
|---|---------|---------|
| 12 | [[Demystifying evals for AI agents]] | Agent 评测方法论与术语体系 |
| 13 | [[Infrastructure noise in agentic coding evals]] | 基础设施配置可造成 6% 评测差异 |
| 14 | [[AI-resistant technical evaluations]] | 评测设计的动态博弈 |
| 15 | [[Building C compiler with parallel Claudes]] | 16 Agent 并行写 10 万行编译器 |
| 16 | [[Desktop Extensions]] | MCP 一键安装与 .mcpb 格式 |
| 17 | [[A postmortem of three recent issues]] | 生产事故复盘：路由/输出/编译三重 Bug |

## 📊 进度追踪

- **总计**: 17 篇
- **已完成**: 0 篇
- **进行中**: 0 篇
- **未开始**: 17 篇

## 🏷️ 标签索引

- #agent-architecture — Agent 架构设计
- #context-engineering — 上下文工程
- #tool-design — 工具设计
- #evals — 评测方法论
- #multi-agent — 多 Agent 系统
- #mcp — MCP 协议
- #security — 安全设计
- #production — 生产实践
