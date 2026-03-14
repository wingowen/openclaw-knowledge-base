# 模块分析：patent_crawler（专利爬虫）

> 项目：ai_scout_refactor
> 路径：`patent_crawler/`
> 生成时间：2026-03-14

---

## 职责

专利爬虫任务管理。负责与爬虫服务（`ai_scout_crawler`）交互，发起专利爬取任务，并通过天眼查 API 获取企业专利数据。

## 文件结构

```
patent_crawler/
├── task_crawl_patent.py         # 专利爬取任务（HTTP 调用）
├── get_data_from_tyc_api.py     # 天眼查 API 数据获取
├── tyc.py                       # 天眼查封装
├── crawl_sql.py                 # 爬虫相关 SQL
└── __init__.py
```

## 核心功能

### 1. 专利爬取任务（task_crawl_patent.py）

**核心流程**：
```python
def crawl_patent_task(keywords, query_id, industry_id):
    # 1. 构建请求
    payload = {
        "script_name": "step_one_v2.py",
        "params": {"keywords": keywords, "query_id": query_id}
    }
    
    # 2. 调用爬虫服务
    response = requests.post(f'{CLAWER_API_URL}/api/local/tasks', json=payload)
    
    # 3. 返回结果
    return response.json()
```

**调用链**：
```
common/tasks.py::crawl_patent_task (Celery)
    ↓
patent_crawler/task_crawl_patent.py
    ↓
HTTP POST → ai_scout_crawler::api.py::submit_local_task
    ↓
执行 scripts/step_one_v2.py
```

### 2. 天眼查 API 集成（get_data_from_tyc_api.py）

直接调用天眼查开放 API 获取企业专利数据：
- 企业专利列表
- 专利详情
- 专利权人信息

### 3. 爬虫 SQL（crawl_sql.py）

管理爬虫任务相关的数据库操作：
- 任务状态更新
- 爬取结果存储
- 错误记录

## 依赖关系

- **上游**：`common/tasks.py` → `crawl_patent_task`
- **下游**：`ai_scout_crawler` 爬虫服务（HTTP）
- **外部 API**：天眼查开放平台

## 注意事项

- 爬虫服务地址通过 `CLAWER_API_URL` 环境变量配置
- 任务超时时间较长（1小时+），需合理设置 HTTP 超时
- 天眼查 API 调用受频率限制和费用约束
