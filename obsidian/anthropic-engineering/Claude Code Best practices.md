#coding-agent #foundation

> [!info] 基本信息
> 来源: [Claude Code Best Practices](https://code.claude.com/docs)
> 发布: 2025-04-18 | 难度: 🟢 入门 | 状态: ⬜ 未开始 | 约 30 分钟

## 章节概括

### 核心能力
- 读取整个代码库，跨文件编辑
- 执行命令、创建 commit/PR
- MCP 协议连接外部工具（Google Drive、Jira、Slack 等）

### 多平台支持
- Terminal CLI / VS Code / JetBrains / Desktop App / Web
- 所有平台共享同一个引擎，CLAUDE.md 和 MCP 配置通用

### 定制化系统
- **CLAUDE.md**：项目根目录的指令文件，每次会话自动读取
- **Skills**：自定义可复用工作流（如 `/review-pr`）
- **Hooks**：文件编辑/commit 前后自动执行 shell 命令

### 高级模式
- **Sub-agents**：多个 Claude 并行处理不同子任务
- **Agent SDK**：构建自定义 Agent 的 SDK
- **CLI 管道组合**：`tail -f log | claude -p "异常报警"`

### 跨环境工作流
- Remote Control：手机/浏览器继续本地会话
- Web/iOS 启动任务 → 终端拉取
- Slack 报 bug → 自动生成 PR

## 学习笔记
（待阅读后补充）

---

#coding-agent #foundation
