# 投研项目双库分离重构 — Todo 文档索引

> 生成时间：2026-03-14
> 基于：[重构状态分析](../重构状态分析.md)
> 重构完成率：**11%（1/9）**

## 概述

投研系统主库 `test_as` 和爬虫库 `test_asc` 双库分离重构。目前只有 `crawl_patent_task` 完成了重构，其余 8 个任务都通过 `sql_util.get_db_connection()` 直连 `test_as`，跳过了爬虫库和同步流程。

## 重构优先级与文档

### ✅ 已完成（基准参考）

| 任务 | 说明 |
|------|------|
| `crawl_patent_task` | 调用爬虫服务后执行 `sync_patent_data()` 同步 6 张表 |

### ❌ 待重构

| 优先级 | 任务 | 文档 | 风险 | 工作量 |
|--------|------|------|------|--------|
| **P0** | `process_patent_data` | [P0-process_patent_data.md](./P0-process_patent_data.md) | 🔴 高 | 中 |
| **P0** | `integrated_patenter_task` | [P0-integrated_patenter_task.md](./P0-integrated_patenter_task.md) | 🔴 高 | 大 |
| **P1** | `monitor_company_data_crawl` | [P1-monitor_company_data_crawl.md](./P1-monitor_company_data_crawl.md) | 🟠 中 | 中 |
| **P1** | `extract_patent_tags` | [P1-extract_patent_tags.md](./P1-extract_patent_tags.md) | 🟠 中 | 小 |
| **P2** | `generate_industry_report` | [P2-generate_industry_report.md](./P2-generate_industry_report.md) | 🟡 低 | 小 |
| **P2** | `generate_company_reports` | [P2-generate_company_reports.md](./P2-generate_company_reports.md) | 🟡 低 | 小 |
| **P3** | `check_all_downstream_tasks` | [P3-check_all_downstream_tasks.md](./P3-check_all_downstream_tasks.md) | 🟢 极低 | 小 |
| **P3** | `orchestrate_company_report_flow` | [P3-orchestrate_company_report_flow.md](./P3-orchestrate_company_report_flow.md) | 🟢 极低 | 无 |

## 推荐重构顺序

```
Phase 1（核心数据流）:
  P0 process_patent_data → P0 integrated_patenter_task

Phase 2（采集与标签）:
  P1 monitor_company_data_crawl → P1 extract_patent_tags

Phase 3（报告生成）:
  P2 generate_industry_report → P2 generate_company_reports

Phase 4（流程收尾）:
  P3 check_all_downstream_tasks → P3 orchestrate_company_report_flow
```

## 核心改造模式

所有 P0-P2 任务遵循同一改造模式：

```python
# Before: 直连主库读取爬虫数据
from data_processing.sql_util import get_db_connection
conn = get_db_connection()  # 只连 test_as
cursor.execute("SELECT * FROM patent_task WHERE ...")

# After: 先同步再读取
from data_processing.sync_client import sync_patent_data
sync_result = sync_patent_data(task_id=task_id, industry_id=industry_id)
# 同步后再读取，数据已在主库
```

## 依赖关系图

```
crawl_patent_task ✅
    ↓ sync_patent_data()
process_patent_data ❌ ← P0
    ↓
extract_patent_tags ❌ ← P1
    ↓
integrated_patenter_task ❌ ← P0
    ↓
monitor_company_data_crawl ❌ ← P1
    ↓
├─→ generate_industry_report ❌ ← P2
├─→ generate_company_reports ❌ ← P2
└─→ check_all_downstream_tasks ❌ ← P3
        ↓
orchestrate_company_report_flow ❌ ← P3
```

## 关键文件定位

| 文件 | 用途 | 重构涉及度 |
|------|------|-----------|
| `common/tasks.py` | Celery 任务定义 | ⭐⭐⭐ 所有任务 |
| `data_processing/data_processor.py` | 专利数据处理管道 | ⭐⭐⭐ P0 tasks |
| `data_processing/sync_client.py` | 数据同步客户端 | ⭐⭐ 需扩展 |
| `data_processing/sql_util.py` | SQL 工具（单库连接） | ⭐⭐ 需改造 |
| `data_processing/sql_queries.py` | SQL 查询定义 | ⭐⭐ P0/P1 tasks |
| `data_processing/company_data_processor.py` | 企业数据处理 | ⭐⭐ P0 integrated |
| `modules/tagging/` | 专利标签模块 | ⭐ P1 extract_tags |

## 参考资料

- [项目总览（主系统）](../ai_scout/PROJECT_OVERVIEW.md)
- [项目总览（爬虫服务）](../ai_scout_crawler/PROJECT_OVERVIEW.md)
- [交互分析](../交互分析.md)
- [重构状态分析](../重构状态分析.md)
