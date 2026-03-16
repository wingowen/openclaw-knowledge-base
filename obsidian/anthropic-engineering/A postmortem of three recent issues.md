#production #incident-review

> [!info] 基本信息
> 来源: [A postmortem of three recent issues](https://www.anthropic.com/engineering/a-postmortem-of-three-recent-issues)
> 发布: 2025-09-17 | 难度: 🔴 前沿 | 状态: ⬜ 未开始 | 约 30 分钟

## 章节概括

### 背景
2025 年 8-9 月，三个基础设施 bug 叠加导致 Claude 响应质量间歇性下降。多硬件平台（AWS Trainium、NVIDIA GPU、Google TPU）增加了复杂性。

### Bug 1: Context Window 路由错误
- **根因**：Sonnet 4 请求被错误路由到 1M token 上下文窗口的服务器
- **影响**：初始 0.8% → 负载均衡变更后峰值 16%（Aug 31）
- **特点**：路由是"粘性"的，一旦路由错误，后续请求也跟着错
- **修复**：修正路由逻辑，区分短/长上下文请求

### Bug 2: 输出损坏
- **根因**：TPU 服务器部署的运行时性能优化配置错误
- **表现**：英语提问中突然出现泰语/中文字符、代码语法错误
- **影响**：Opus 4/4.1 (Aug 25-28)、Sonnet 4 (Aug 25 - Sep 2)
- **修复**：回滚变更 + 添加异常字符输出检测

### Bug 3: Top-k XLA:TPU 编译错误
- （文章被截断，推测是 TPU 编译器近似计算导致的质量下降）

### 经验教训
- 多平台部署增加等效性验证复杂度
- 负载均衡变更可能放大隐藏 bug
- "粘性路由"让问题更难被察觉
- 需要更灵敏的自动检测机制

## 学习笔记
（待阅读后补充）

---

#production #incident-review
