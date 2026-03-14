# 模块分析：business_api（业务 API）

> 项目：ai_scout_crawler_refactor
> 路径：`business_api.py`
> 生成时间：2026-03-14

---

## 职责

业务数据同步接口。提供爬虫服务与主系统之间的数据同步能力，包括任务镜像、产业/批次/查询数据的双向同步。

## 文件信息

- **文件**：`business_api.py`（单文件模块）
- **框架**：Flask 路由函数（在 `api.py` 中注册）

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/task_mirror/upsert` | POST | 任务镜像同步（先删后插） |
| `/api/task_mirror/<task_id>` | GET | 获取任务镜像 |
| `/api/insert_task_record` | POST | 插入任务记录 |
| `/api/insert_industry_query` | POST | 插入产业查询 |
| `/api/sync_data` | GET | 全量数据同步 |

## 核心功能

### 1. 任务镜像同步（upsert_task_mirror）

**目的**：将主系统的产业/批次/查询/任务数据同步到爬虫数据库。

**同步层级**（可选，按需提供）：
```
industry（产业）
    ↓
batch（批次）
    ↓
industry_query（产业查询）
    ↓
task（任务）
```

**实现方式**：使用 `INSERT ... ON DUPLICATE KEY UPDATE` 实现幂等 upsert。

**请求体**：
```json
{
    "task_id": 123,
    "query_id": 456,
    "keywords": "搜索关键词",
    "celery_task_id": "xxx",
    "industry": {"id": 1, "level": 1, "industry_name": "..."},
    "batch": {"id": 1, "industry_id": 1, "batch_time": "..."},
    "industry_query": {"id": 1, "industry_id": 1, "keyword": "..."}
}
```

### 2. 数据同步（sync_data）

将爬虫数据库的数据同步回主系统。

### 3. 数据插入

- `insert_task_record`：插入任务记录
- `insert_industry_query`：插入产业查询

## 数据库操作

使用原生 SQL + PyMySQL：
```python
with get_db_connection() as (db, cursor):
    cursor.execute(upsert_sql, values)
    db.commit()
```

**幂等性保证**：所有 upsert 操作使用 `ON DUPLICATE KEY UPDATE`。

## 依赖关系

- **上游**：`ai_scout` 主系统调用
- **下游**：MySQL（`test_asc` 数据库）
- **被依赖**：主系统的任务创建流程

## 注意事项

- 所有同步操作幂等，可安全重试
- 同步 batch 时必须同时提供 industry
- 数据库连接通过 `utils.sql_util.get_db_connection()` 获取
- JSON 序列化处理 datetime/date 类型（`json_serial` 函数）
