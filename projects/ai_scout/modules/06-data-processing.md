# 模块分析：data_processing（数据处理）

> 项目：ai_scout_refactor
> 路径：`data_processing/`
> 生成时间：2026-03-14

---

## 职责

数据处理管道。负责爬虫数据的清洗、转换、关联，以及批量评分任务的执行。是连接原始爬虫数据和 AI 评分系统的桥梁。

## 文件结构

```
data_processing/
├── data_lib.py                  # ⭐ 数据访问层
├── data_processor.py            # 专利数据处理管道
├── company_data_processor.py    # 企业数据处理
├── sync_client.py               # 爬虫数据同步
├── sql_queries.py               # SQL 查询定义
├── sql_util.py                  # SQL 工具
├── obj.py                       # 数据对象
├── tyc_company.py               # 天眼查企业数据
├── tyc_company_interface.py     # 天眼查企业接口
├── tyc_patenter_interface.py    # 天眼查专利人接口
├── tyc_sql.py                   # 天眼查 SQL
├── batch_company_competitiveness_scoring.py  # 批量竞争力评分
├── batch_company_operation_scoring.py        # 批量经营评分
├── batch_company_potential_scoring.py        # 批量潜力评分
├── batch_company_reputation_scoring.py       # 批量声誉评分
├── batch_company_tech_evaluation.py          # 批量技术评估
├── batch_company_tech_score.py               # 批量技术评分
└── batch_patent_score/          # 批量专利评分
    ├── batch_patent_scoring.py              # 综合专利评分
    ├── batch_patent_tagging.py              # 专利标签提取
    ├── batch_patent_application_value_scoring.py
    ├── batch_patent_impact_scoring.py
    ├── batch_patent_status_scoring.py
    └── __init__.py
```

## 核心模块

### 1. 数据访问层（data_lib.py）

封装所有数据库操作，提供高层 API：

| 方法 | 说明 |
|------|------|
| `get_company_list_for_reports()` | 获取待生成报告的企业列表 |
| `save_industry_report_result()` | 保存产业报告结果 |
| `save_company_report_result()` | 保存企业报告结果 |
| `get_*` 系列方法 | 各类数据查询 |

### 2. 专利数据处理管道（data_processor.py）

**核心类**：

| 类 | 功能 |
|----|------|
| `PatentTaskToPatentQuery` | 构建专利-Query 关联数据 |
| `QueryPatentToPatenter` | 从专利数据提取专利权人 |
| `IndustryPatenterExtractor` | 提取并处理产业专利权人 |
| `IntegratedPatenterTaskProcessor` | 整合全流程处理器 |

**处理流程**：
```
爬虫任务完成
    ↓
PatentTaskToPatentQuery（专利-Query 关联）
    ↓
相关性评分（LLM）
    ↓
QueryPatentToPatenter（提取专利权人）
    ↓
IndustryPatenterExtractor（产业专利权人处理）
    ↓
写入 company_longlist
```

### 3. 企业数据处理（company_data_processor.py）

**核心类**：

| 类 | 功能 |
|----|------|
| `CompanyDataProcessor` | 处理企业 query_ids 关联 |
| `CompanyTypeProcessor` | 处理企业类型分类 |
| `CompanyPatenterNameBackfiller` | 专利人名称回填 |

### 4. 批量评分模块

每个评分维度对应一个独立的批量处理脚本：

| 脚本 | 评分维度 | 输入 |
|------|----------|------|
| `batch_company_competitiveness_scoring.py` | 竞争力 | 标准/证书/投资/招投标 |
| `batch_company_operation_scoring.py` | 经营 | 业务/荣誉/招投标 |
| `batch_company_potential_scoring.py` | 潜力 | 股东/融资/人员 |
| `batch_company_reputation_scoring.py` | 声誉 | 新闻舆情 |
| `batch_company_tech_evaluation.py` | 技术评估 | 专利+企业信息 |
| `batch_company_tech_score.py` | 技术评分 | 技术评估结果 |
| `batch_patent_score/batch_patent_scoring.py` | 专利综合 | 专利数据 |
| `batch_patent_score/batch_patent_tagging.py` | 专利标签 | 专利全文 |

### 5. 数据同步（sync_client.py）

从爬虫数据库（`test_asc`）同步数据到主系统数据库（`test_as`）：

```python
sync_patent_data(task_id, industry_id)  # 同步专利数据
```

### 6. 天眼查数据集成

| 模块 | 功能 |
|------|------|
| `tyc_company.py` | 天眼查企业数据处理 |
| `tyc_company_interface.py` | 企业数据接口 |
| `tyc_patenter_interface.py` | 专利人数据接口 |
| `tyc_sql.py` | 天眼查相关 SQL |

## 依赖关系

- **上游**：`common/tasks.py` 的 Celery 任务调用本模块
- **下游**：`ai_scout_agent`（评分/报告）、MySQL 数据库
- **被依赖**：所有批量处理任务、数据同步任务

## SQL 管理

`sql_queries.py` 集中管理所有原生 SQL：

| 函数 | 说明 |
|------|------|
| `check_all_tasks_complete()` | 检查所有爬虫任务是否完成 |
| `get_latest_batch_id()` | 获取最新批次 ID |
| `insert_data_task_record()` | 插入数据任务记录 |
| `update_data_task_completed()` | 更新任务完成状态 |
| `get_patent_keyword_wordcloud()` | 获取专利关键词词云 |
| `get_industry_by_id()` | 获取产业信息 |

## 注意事项

- 批量评分是计算密集型任务，建议使用 Flash 模型
- 数据同步需处理两库之间的数据一致性
- SQL 查询使用原生 SQL 而非 ORM，注意 SQL 注入防护
- 处理大量企业数据时注意内存使用，建议分批处理
