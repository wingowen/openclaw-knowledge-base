#tool-design #reasoning

> [!info] 基本信息
> 来源: [The "think" tool](https://www.anthropic.com/engineering/claude-think-tool)
> 发布: 2025-03-20 | 难度: 🟢 入门 | 状态: ⬜ 未开始 | 约 20 分钟

## 章节概括

### Think Tool 是什么？
一个让 Claude 在工具调用链中"停下来想一想"的专用工具。与 **Extended Thinking** 不同：
- Extended Thinking：生成响应前的深度规划
- Think Tool：生成响应过程中、处理外部信息后的暂停思考

### 适用场景
- 长链工具调用需要分析中间结果
- 策略密集型环境（详细规则/政策）
- 序列决策（每步依赖上一步结果）

### 性能基准（τ-Bench）
- **航空领域**：Think + 优化 prompt → pass^1 = 0.570（baseline 0.370，+54%）
- **零售领域**：Think 单独使用 → pass^1 = 0.812（baseline 0.783）

### 最佳实践
在系统 prompt 中给 Think 工具加示例，教模型什么场景下使用、思考什么内容：
- 列出适用规则
- 检查信息完整性
- 验证操作合规性
- 迭代分析工具结果

### 注意事项
> 2025.12 更新：Extended Thinking 已增强，多数场景推荐直接用 Extended Thinking

## 学习笔记
（待阅读后补充）

---

#tool-design #reasoning
