#evals #infrastructure

> [!info] 基本信息
> 来源: [Quantifying infrastructure noise in agentic coding evals](https://www.anthropic.com/engineering/infrastructure-noise)
> 发布: 2026-03 | 难度: 🔴 前沿 | 状态: ⬜ 未开始 | 约 30 分钟

## 章节概括

### 核心发现
基础设施配置可以产生 **6 个百分点**的评测差异（p < 0.01），比排行榜 top 模型之间的差距还大。

### 为什么基础设施会影响评测？
- Agent 评测不是静态的：模型写代码、跑测试、装依赖、多次迭代
- 运行环境是解题过程的**组成部分**
- 资源配置不同的两个 Agent 不是在做同一套题

### 实验设计
Terminal-Bench 2.0，同一模型，6 种资源配置：
- 1x（严格限制）→ 3x → 5x → uncapped
- 结果：uncapped 比 1x 高 **6 个百分点**

### 效果来源
1. **3x 以下**：修复基础设施稳定性（瞬时资源 spike 导致容器被杀）
2. **3x 以上**：资源开始真正帮助 Agent 解决问题（大依赖、内存密集测试）

### 对评测设计的启示
- 资源配置不是中性的——它在**改变评测在测什么**
- 紧限制奖励高效策略，宽松限制奖励能利用资源的 Agent
- 需要显式指定资源配置，否则分数不可比较

### 其他噪声源
- 时间限制
- 集群健康状态
- 硬件规格
- 并发级别
- 带宽

## 学习笔记
（待阅读后补充）

---

#evals #infrastructure
