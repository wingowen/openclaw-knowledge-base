# AI Scout Crawler 爬虫服务 - 模块分析索引

> 项目路径：`/mnt/d/Pycharm/ai_scout_crawler_refactor/`
> 文档路径：`~/.openclaw/workspace/projects/ai_scout_crawler/modules/`

---

## 模块列表

| # | 模块 | 文件/路径 | 职责 | 文档 |
|---|------|-----------|------|------|
| 1 | api | `api.py` | Flask API 入口（任务提交/查询/流式传输） | [01-api.md](./01-api.md) |
| 2 | tasks | `tasks.py` | Celery 任务（爬虫脚本执行器） | [02-tasks.md](./02-tasks.md) |
| 3 | business_api | `business_api.py` | 业务数据同步接口 | [03-business-api.md](./03-business-api.md) |
| 4 | scripts | `scripts/` | 爬虫脚本集（专利/天眼查/新闻） | [04-scripts.md](./04-scripts.md) |
| 5 | news_classification | `news_classification/` | 新闻自动分类 | [05-news-classification.md](./05-news-classification.md) |
| 6 | utils | `utils/` | 工具集（DB/Redis/Celery/日志） | [06-utils.md](./06-utils.md) |
| 7 | config | `config.py` | 全局配置 | [07-config.md](./07-config.md) |

## 模块依赖图

```
                    ┌────────────┐
                    │   config   │ (全局配置)
                    └─────┬──────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
  ┌──────────┐     ┌──────────┐     ┌──────────┐
  │  utils   │     │   api    │     │  tasks   │
  │ (工具集) │◄────┤ (Flask)  ├────►│ (Celery) │
  └──────────┘     └────┬─────┘     └────┬─────┘
                        │                │
                        ▼                ▼
                 ┌────────────┐   ┌────────────┐
                 │ business_  │   │  scripts/  │
                 │ api        │   │ (爬虫脚本) │
                 │ (业务同步) │   └─────┬──────┘
                 └────────────┘         │
                                        ▼
                                 ┌────────────┐
                                 │   news_    │
                                 │ classifi-  │
                                 │ cation     │
                                 │ (新闻分类) │
                                 └────────────┘
```

## 数据流

```
ai_scout 主系统
    │
    │ HTTP POST /api/local/tasks
    │ HTTP POST /api/tasks
    │ HTTP POST /api/task_mirror/upsert
    ▼
┌───────────────────────────────────┐
│  api.py (Flask)                   │
│                                   │
│  ├─ /api/local/tasks              │
│  │   └─ subprocess.Popen ────────►scripts/*.py
│  │                                 (同步执行)
│  │
│  └─ /api/tasks
│      └─ Celery.delay ────────────►tasks.py::run_crawler_task
│                                    └─ subprocess.Popen
│                                        (异步执行)
└───────────────────────────────────┘
    │
    │ /api/task_mirror/upsert
    ▼
┌───────────────────────────────────┐
│  business_api.py                  │
│  ├─ upsert task/batch/industry   │
│  └─ sync_data → 主系统            │
└───────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────┐
│  MySQL (test_asc)                 │
│  Redis (:6379/5,6)                │
└───────────────────────────────────┘
```

## 关键模块说明

### ⭐ api.py - API 入口
所有外部调用的统一入口，支持异步（Celery）和同步（本地）两种执行模式。

### ⭐ scripts/ - 爬虫脚本集
11 个天眼查维度 + 专利爬取 + 新闻分类，是实际的数据采集执行者。

### ⭐ tasks.py - 安全执行框架
提供路径安全校验、子进程管理、实时日志等基础设施。
