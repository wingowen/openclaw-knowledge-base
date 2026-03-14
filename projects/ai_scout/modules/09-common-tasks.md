# 模块分析：common（公共模块）

> 项目：ai_scout_refactor
> 路径：`common/`
> 生成时间：2026-03-14

---

## 职责

公共工具和核心 Celery 任务定义。包含响应格式化、日志工具，以及系统最重要的异步任务编排。

## 文件结构

```
common/
├── tasks.py               # ⭐⭐ 核心 Celery 任务（所有业务流程入口）
├── response_utils.py      # 统一响应格式化
├── response_codes.py      # 响应码定义
├── logger_utils.py        # 日志工具
├── cleanup_apilogs.py     # API 日志清理
└── __init__.py            # 初始化
```

## 核心功能

### 1. Celery 任务（tasks.py）⭐ 最重要的模块

这是整个系统的 **任务编排中心**，所有业务流程都从这里触发。

#### 任务清单

| 任务 | 队列 | 说明 | 下游任务 |
|------|------|------|----------|
| `crawl_patent_task` | ai_scout_crawler | 专利爬取（调用爬虫服务） | `process_patent_data` |
| `process_patent_data` | ai_scout_crawler | 专利数据处理+相关性评分 | `extract_patent_tags` |
| `extract_patent_tags` | ai_scout_crawler | 专利标签提取 | `generate_industry_report` |
| `generate_industry_report` | ai_scout_crawler | 产业报告生成 | `check_all_downstream_tasks` |
| `generate_company_reports` | ai_scout_crawler | 批量企业报告生成 | - |
| `integrated_patenter_task` | ai_scout_crawler | 专利权人→企业全流程 | `generate_company_reports` |
| `orchestrate_company_report_flow` | ai_scout_crawler | 企业报告流程编排 | - |
| `monitor_company_data_crawl` | ai_scout_crawler | 企业数据爬取监控 | 批量评分 |
| `check_all_downstream_tasks` | ai_scout_crawler | 下游任务完成检查 | - |

#### 任务链（完整流程）

```
crawl_patent_task
    ↓ (成功后)
process_patent_data
    ├→ PatentTaskToPatentQuery
    ├→ PatentRelevanceProcessor (LLM 相关性评分)
    ├→ QueryPatentToPatenter
    └→ IndustryPatenterExtractor
    ↓ (所有爬虫完成后)
extract_patent_tags
    ↓
generate_industry_report (并行触发)
check_all_downstream_tasks (并行触发)
    ↓
integrated_patenter_task
    ├→ IntegratedPatenterTaskProcessor
    ├→ CompanyDataProcessor
    ├→ CompanyTypeProcessor
    └→ CompanyPatenterNameBackfiller
    ↓
generate_company_reports
    ↓
monitor_company_data_crawl
    ├→ 天眼查 11 维度数据爬取
    ├→ 新闻分类
    ├→ 批量评分（竞争力/经营/潜力/声誉/专利）
    ├→ 专利标签提取
    ├→ 技术评估生成
    └→ 总分计算
```

#### 关键设计

- **`bind=True`**：所有任务使用 bind 模式，可访问 `self.request.id` 和 `self.update_state()`
- **`autoretry_for`**：部分任务配置自动重试（如 `retry_task`）
- **状态更新**：通过 `self.update_state()` 实时更新任务进度
- **线程池并发**：`monitor_company_data_crawl` 使用 `ThreadPoolExecutor` 并行触发爬虫
- **异步触发**：专利总数爬取使用 daemon 线程异步触发，不阻塞主流程

### 2. 响应工具（response_utils.py）

统一 API 响应格式：

```python
response_utils.success(data, message="成功")
response_utils.error(message="失败", code=ERROR_CODE)
response_utils.bad_request(errors)
response_utils.business_error(message, code)
```

### 3. 响应码（response_codes.py）

定义统一的业务响应码。

### 4. 日志工具（logger_utils.py）

提供统一的日志配置和工具函数。

## 依赖关系

- **上游**：Django 视图、定时任务、手动触发
- **下游**：`ai_scout_agent`、`data_processing`、`patent_crawler`、`modules/tagging`
- **外部依赖**：爬虫服务（HTTP）、LLM API、MySQL、Redis

## 注意事项

- 这是系统的核心编排模块，修改需谨慎
- 任务之间的依赖关系通过 `.delay()` 链式调用实现
- 任务失败时会更新 `data_task` 表状态为失败（`is_complete=2`）
- `monitor_company_data_crawl` 是最长的任务，可能持续数小时
