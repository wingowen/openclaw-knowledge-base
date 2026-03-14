# 模块分析：modules/tagging（专利标签）

> 项目：ai_scout_refactor
> 路径：`modules/tagging/`
> 生成时间：2026-03-14

---

## 职责

专利标签提取。从专利全文中自动提取技术标签和关键词，支持基于规则的提取和 LLM 辅助提取两种方式。

## 文件结构

```
modules/tagging/
├── base.py                    # 基础接口
├── schema.py                  # 标签数据模式
├── patent_tagging_batch.py    # ⭐ 批量标签处理
├── rule_based_extractor.py    # 规则提取器
├── rule_based/
│   └── patent_tag_extractor.py  # 专利标签规则提取
└── examples/
    ├── benchmark_1k.py        # 1K 基准测试
    └── rule_based_example.py  # 规则提取示例
```

## 核心功能

### 1. 批量标签处理（patent_tagging_batch.py）

**入口函数**：
```python
process_industry_patents(industry_id, batch_size=1000, max_workers=1)
```

**处理流程**：
1. 获取产业下所有专利
2. 分批处理（默认 1000 条/批）
3. 对每篇专利提取标签
4. 结果写入数据库

### 2. 规则提取（rule_based_extractor.py）

基于预定义规则和词典提取标签：
- 技术领域识别
- 关键技术词提取
- IPC 分类号映射

### 3. 标签模式（schema.py）

定义标签的数据结构和分类体系。

## 依赖关系

- **上游**：`common/tasks.py` → `extract_patent_tags` 任务
- **下游**：`ai_scout_agent.core.report.patent_tag_extractor`（LLM 提取）
- **被依赖**：产业报告生成（需要核心标签数据）

## 在业务流程中的位置

```
专利爬取 → 专利相关性评分 → 专利标签提取（本模块）→ 产业报告
                                        ↓
                              核心技术标签 + 关键词
```

## 注意事项

- 规则提取速度快但覆盖有限，LLM 提取覆盖广但成本高
- 建议先用规则提取处理明显标签，LLM 处理剩余复杂专利
- `batch_size` 和 `max_workers` 需根据服务器资源调整
