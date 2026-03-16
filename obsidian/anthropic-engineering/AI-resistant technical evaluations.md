#evals #methodology

> [!info] 基本信息
> 来源: [Designing AI-resistant technical evaluations](https://www.anthropic.com/engineering/AI-resistant-technical-evaluations)
> 发布: 2026-01-21 | 难度: 🔴 前沿 | 状态: ⬜ 未开始 | 约 35 分钟

## 章节概括

### 背景
Anthropic 性能优化团队的面试 take-home 测试，1000+ 候选人完成。每次新 Claude 模型发布就需要重新设计——Opus 4 超过大多数候选人，Opus 4.5 连最强候选人都追上了。

### 原始测试设计
- 模拟加速器（类似 TPU）的 Python 模拟器
- 候选人优化代码（手动管理内存、VLIW、SIMD、多核）
- 热重载 Perfetto trace 查看每条指令
- 4 小时时限（后缩短到 2 小时）

### 设计原则
1. **代表真实工作**：让候选人体验实际工作内容
2. **高信号**：多次展示能力的机会，不依赖单一洞察
3. **不需要特定领域知识**：通用基础能力即可
4. **有趣**：快速迭代、有深度、有创造空间

### 对评测的启示
- AI 能力边界不断扩展 → 评测设计是动态博弈
- 更长周期的问题更难被 AI 完全解决
- 允许使用 AI 工具（像真实工作一样），但仍需展示个人技能
- 无限时间下人类最强表现仍超过模型 → 关键是时间约束下的区分度

### 开放挑战
Anthropic 发布了原始测试（无限时），如果你能打败 Opus 4.5，他们想聊聊。

## 学习笔记
（待阅读后补充）

---

#evals #methodology
