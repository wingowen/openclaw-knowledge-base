#rag #context-engineering

> [!info] 基本信息
> 来源: [Introducing Contextual Retrieval](https://www.anthropic.com/engineering/contextual-retrieval)
> 发布: 2024-09-19 | 难度: 🔵 基础 | 状态: ⬜ 未开始 | 约 35 分钟

## 章节概括

### RAG 的核心问题
传统 RAG 将文档切块 → 编码 → 检索。问题是**切块丢失上下文**：一块说"公司营收增长3%"，但不知道是哪家公司、哪个季度。

### 解决方案：Contextual Retrieval
在每个 chunk 前**加上文档级别的简短上下文说明**再编码。

```
原始: "The company's revenue grew by 3% over the previous quarter."
+ 上下文: "This chunk is from an SEC filing on ACME corp's Q2 2023; 
           the previous quarter's revenue was $314 million."
= "This chunk is from an SEC filing on ACME corp's Q2 2023; the previous quarter's revenue was $314 million. The company's revenue grew by 3% over the previous quarter."
```

### 双管齐下
- **Contextual Embedding**：加上上下文后做 embedding
- **Contextual BM25**：加上上下文后做关键词匹配
- 两者结合：检索失败率降低 **49%**

### + Reranking
再加 Cohere reranking 排序：失败率降低 **67%**（5.7% → 1.9%）

### 成本优化
利用 Claude 的 **Prompt Caching**：文档只加载一次到 cache，后续每个 chunk 引用缓存。百万 token 文档处理成本约 $1.02。

### 实施考量
- Chunk 边界选择（大小、重叠）影响检索效果
- Embedding 模型选择（Gemini、Voyage 表现较好）
- 可用自定义 contextualizer prompt 针对特定领域优化

## 学习笔记
（待阅读后补充）

---

#rag #context-engineering
