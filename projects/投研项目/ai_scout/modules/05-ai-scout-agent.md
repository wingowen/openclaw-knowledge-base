# 模块分析：ai_scout_agent（AI Agent 核心）

> 项目：ai_scout_refactor
> 路径：`ai_scout_agent/`
> 生成时间：2026-03-14

---

## 职责

AI 投研系统的核心智能模块。封装所有 LLM 相关功能：查询生成、相关性计算、多维度评分、报告生成、摘要提取。

## 文件结构

```
ai_scout_agent/
├── core/
│   ├── query_gen.py           # 查询生成器
│   ├── query_parser.py        # 查询解析器
│   ├── schema.py              # 数据模式
│   ├── interfaces.py          # 接口定义
│   ├── generators.py          # 生成器工具
│   ├── relevance/             # 相关性计算
│   │   ├── base.py            # 基础接口
│   │   ├── llm.py             # LLM 相关性
│   │   ├── vector.py          # 向量相关性
│   │   └── models.py          # 数据模型
│   ├── scoring/               # ⭐ 多维度评分系统
│   │   ├── aggregator.py      # 评分聚合
│   │   ├── context.py         # 评分上下文
│   │   ├── company/           # 企业评分（5维度）
│   │   └── dimensions/        # 专利评分（9维度）
│   ├── report/                # 报告生成
│   │   ├── industry.py        # 产业报告
│   │   ├── company.py         # 企业报告
│   │   ├── context_builder.py # 上下文构建
│   │   └── patent_tag_extractor.py # 标签提取
│   └── summarization/         # 摘要服务
│       └── reputation_summarizers.py
├── utils/
│   ├── llm_client.py          # ⭐ LLM 客户端工厂
│   ├── search_provider.py     # 搜索提供者
│   ├── observability.py       # Langfuse 可观测性
│   ├── metrics.py             # 指标收集
│   ├── concurrency.py         # 并发工具
│   ├── summary/               # 摘要工具集
│   └── url_checker/           # URL 检查
├── prompts/
│   └── manager.py             # Prompt 模板管理
├── config/                    # 配置
├── examples/                  # 使用示例
└── interface.py               # 对外接口
```

## 核心子模块

### 1. 查询生成（query_gen）

**功能**：根据产业定义自动生成专利搜索查询策略。

**支持模式**：
- 标准模式：基于产业关键词组合
- 高级模式：LLM 辅助生成复杂查询
- 上下文模式：结合已有数据优化查询

**输出**：结构化搜索查询列表，传递给爬虫执行。

### 2. 相关性计算（relevance）

**两种计算方式**：

| 方式 | 类 | 说明 |
|------|----|------|
| LLM 相关性 | `LLMRelevanceCalculator` | 使用 LLM 判断专利与产业的相关性 |
| 向量相关性 | `VectorRelevanceCalculator` | 使用向量相似度计算相关性 |

**用途**：在专利数据入库后，筛选与目标产业真正相关的专利。

### 3. 多维度评分（scoring）

#### 企业评分（5 维度）

| 维度 | Scorer | 输入数据 | 评分方式 |
|------|--------|----------|----------|
| 竞争力 | `CompetitivenessScorer` | 标准/证书/投资/招投标 | LLM + 规则 |
| 经营 | `OperationScorer` | 业务/荣誉/招投标 | LLM + 规则 |
| 潜力 | `PotentialScorer` | 股东/融资/人员 | LLM + 规则 |
| 声誉 | `ReputationScorer` | 新闻舆情 | LLM 分析 |
| 技术 | `TechScorer` | 专利 + 技术评估 | 综合计算 |

**技术评分子流程**：
1. `TechEvaluationBuilder` → 构建技术评估输入
2. `TechEvaluator` → LLM 生成技术评估
3. `TechScorer` → 基于评估计算分数

#### 专利评分（9 维度）

| 维度 | 评分内容 |
|------|----------|
| 应用价值 | 商业应用潜力 |
| 发展潜力 | 技术发展趋势 |
| 产业化可行性 | 落地可行性 |
| 专利影响力 | 引用影响范围 |
| 专利状态 | 法律状态 |
| 专利类型 | 发明/实用新型/外观 |
| 技术重要性 | 技术链位置 |
| 技术创新性 | 创新程度 |
| 技术稀缺性 | 独占性 |

**基类**：`BasePatentLLMScorer` → 所有专利评分维度继承此类，统一 LLM 调用和结果解析。

### 4. 报告生成（report）

| 生成器 | 输出 | 说明 |
|--------|------|------|
| `IndustryReportGenerator` | 产业报告 | 产业趋势、核心标签、竞争格局 |
| `CompanyReportGenerator` | 企业报告 | 企业评估、技术分析、投资建议 |

**上下文构建**：`ContextBuilder` 负责从数据库抽取相关数据，组装 LLM 输入上下文。

### 5. LLM 客户端工厂（llm_client.py）

**多模型支持与自动降级**：

```python
LLMClientFactory.create_general_client()  # 通用客户端
LLMClientFactory.create_flash_client()    # 快速模型（批量任务）
```

**模型优先级**：
1. 豆包 (doubao-seed-1-8) → 主力
2. Kimi (kimi-k2-turbo) → 备选
3. Qwen (qwen-plus) → 备选
4. Ollama (qwen3:4b) → 本地兜底

### 6. Prompt 管理（prompts/manager.py）

集中管理所有 LLM Prompt 模板，支持：
- 模板版本管理
- 动态变量注入
- 多语言支持

### 7. 可观测性（observability.py）

集成 **Langfuse**，追踪所有 LLM 调用：
- Token 使用量
- 延迟统计
- 成本追踪
- 错误监控

## 依赖关系

- **上游**：`common/tasks.py` 调用本模块生成报告和评分
- **下游**：LLM API（豆包/Kimi/Qwen/Ollama）、Langfuse
- **被依赖**：所有评分任务、报告生成任务

## 数据流

```
产业数据 / 企业数据
    ↓
ContextBuilder（组装上下文）
    ↓
LLMClientFactory（创建客户端）
    ↓
Prompt Manager（加载模板）
    ↓
LLM API 调用（Langfuse 追踪）
    ↓
结果解析 → 评分 / 报告 / 标签
    ↓
写入数据库
```

## 注意事项

- LLM 调用是系统主要成本和性能瓶颈
- 批量任务建议使用 Flash 模型降低成本
- 所有 LLM 调用通过 Langfuse 追踪，可分析用量和成本
- 评分的确定性依赖 temperature 设置，评分任务建议使用较低 temperature
