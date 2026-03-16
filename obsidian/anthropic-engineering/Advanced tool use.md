#tool-design #advanced

> [!info] 基本信息
> 来源: [Advanced tool use](https://www.anthropic.com/engineering/advanced-tool-use)
> 发布: 2025-11-24 | 难度: 🔵 基础 | 状态: ⬜ 未开始 | 约 30 分钟

## 章节概括

### 三大新功能

#### 1. Tool Search Tool
- **问题**：5 个 MCP Server（58 个工具）= ~55K token 开销；工具多了选择困难
- **方案**：标记 `defer_loading: true`，Agent 按需搜索工具定义
- **效果**：token 消耗降低 85%（77K → 8.7K），准确率提升（Opus 4: 49% → 74%）
- 适用：>10个工具、多 MCP Server、工具选择准确性有问题时

#### 2. Programmatic Tool Calling
- **问题**：自然语言工具调用每次需要完整推理；中间结果堆积在上下文中
- **方案**：Claude 写 Python 代码编排工具调用，代码在沙箱中执行
- **优势**：
  - 并行调用（`asyncio.gather`）
  - 中间结果不污染上下文
  - 循环/条件/变换逻辑在代码中明确表达
- **案例**：预算合规检查 — 传统方式 2000+ 行费用明细进入上下文；代码方式只返回超标人员

#### 3. Tool Use Examples
- JSON Schema 只能定义结构合法性，不能表达使用模式
- 用示例展示：何时用可选参数、哪些组合有意义、API 约定

### 设计理念
Agent 应该**按需发现和加载工具**，而不是把所有定义都塞进上下文。

## 学习笔记
（待阅读后补充）

---

#tool-design #advanced
