#mcp #desktop

> [!info] 基本信息
> 来源: [Desktop Extensions](https://www.anthropic.com/engineering/desktop-extensions)
> 发布: 2025-06-26 | 难度: 🔴 前沿 | 状态: ⬜ 未开始 | 约 25 分钟

## 章节概括

### 问题
MCP Server 安装太复杂：需要 Node.js/Python、手动编辑 JSON、处理依赖冲突、无发现机制。

### 解决方案：Desktop Extensions (.mcpb)
打包成单个可安装文件（ZIP），包含所有依赖。安装流程：
1. 下载 .mcpb 文件
2. 双击用 Claude Desktop 打开
3. 点"安装"

### 架构
```
extension.mcpb (ZIP)
├── manifest.json    # 元数据 + 配置
├── server/          # MCP Server 实现
├── dependencies/    # 所有依赖
└── icon.png         # 图标
```

- Claude Desktop 内置 Node.js 运行时
- 自动更新
- 敏感配置（API key）存 OS keychain
- 支持 Node.js / Python / 二进制三种类型

### manifest.json 核心字段
- `name`, `version`, `description`, `author`
- `server.type`：node / python / binary
- `server.entry_point`：主文件路径
- `server.mcp_config`：命令和参数

### 后续更新
- 2025.09：文件扩展名从 .dxt 改为 .mcpb（MCP Bundle）

## 学习笔记
（待阅读后补充）

---

#mcp #desktop
