#evals #methodology

> [!info] 基本信息
> 来源: [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
> 发布: 2026-01-09 | 难度: 🔴 前沿 | 状态: ⬜ 未开始 | 约 50 分钟

## 章节概括

### 为什么需要评测？
没有评测 → 生产环境才发现问题 → 修一个 bug 引入其他 bug。评测让行为变化在上线前可见。

### Agent 评测的术语体系
- **Task**：单个测试（输入 + 成功标准）
- **Trial**：一次尝试（多次运行取统计）
- **Grader**：评分逻辑（可多个，含多个 assertion）
- **Transcript**：完整记录（输出、工具调用、推理、中间结果）
- **Outcome**：最终环境状态（不是模型说了什么，是实际发生了什么）
- **Harness**：运行评测的基础设施
- **Agent scaffold**：让模型成为 Agent 的系统
- **Eval suite**：测量特定能力的测试集合

### Agent 评测 vs 传统评测
- Agent 多轮交互、修改状态、错误会累积
- 前沿模型可能找到评测设计者没想到的解法（Opus 4.5 利用政策漏洞"作弊"）
- 需要评测环境状态，不只是输出

### 什么时候建评测？
- **早期**：迫使产品团队定义"什么是成功"
- **后期**：在规模扩张时维持质量底线
- 无论什么阶段都有用

### 案例
- **Descript**：视频编辑 Agent，三个维度（不破坏、按要求做、做得好）→ LLM 评分 + 人工校准
- **Bolt**：已有大规模 Agent 后建评测 → 3 个月搭建：静态分析 + 浏览器测试 + LLM 评判

## 学习笔记
（待阅读后补充）

---

#evals #methodology
