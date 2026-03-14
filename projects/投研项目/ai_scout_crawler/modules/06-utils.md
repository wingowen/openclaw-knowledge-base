# 模块分析：utils（工具模块）

> 项目：ai_scout_crawler_refactor
> 路径：`utils/`
> 生成时间：2026-03-14

---

## 职责

公共工具集。提供数据库连接、Celery 配置、日志、响应格式化等基础功能。

## 文件结构

```
utils/
├── celery_app.py          # Celery 应用配置
├── database.py            # 数据库连接管理
├── sql_util.py            # SQL 工具
├── sql_queries.py         # SQL 查询
├── crawl_sql.py           # 爬虫相关 SQL
├── account_redis.py       # 天眼查账号 Redis 管理
├── import_accounts.py     # 账号批量导入
├── logger.py              # 日志配置（loguru）
├── obj.py                 # 对象工具
├── response_codes.py      # 响应码
└── response_utils.py      # 响应格式化
```

## 核心模块

### 1. Celery 配置（celery_app.py）

```python
app = Celery('ai_scout_crawler')
app.conf.broker_url = f'redis://:{password}@{host}:{port}/5'
app.conf.result_backend = f'redis://:{password}@{host}:{port}/6'
app.conf.task_default_queue = 'ai_scout_crawler_test'
```

**Redis DB 分配**：
- DB 5：Broker（消息队列）
- DB 6：Result Backend（结果存储）

### 2. 数据库连接（database.py / sql_util.py）

**两种连接方式**：

```python
# sql_util.py - 上下文管理器
with get_db_connection() as (db, cursor):
    cursor.execute(sql, params)
    results = cursor.fetchall()

# database.py - 连接池
engine = create_engine(f'mysql+pymysql://...')
```

### 3. 日志（logger.py）

基于 **loguru** 的日志封装：

```python
logger = get_celery_logger()  # Celery 任务日志（带时间戳文件名）
exception(msg)                # 异常日志（含 traceback）
```

**特性**：
- 每个 Celery 任务独立日志文件（带时间戳）
- 自动轮转和压缩
- 同时输出到控制台和文件

### 4. 账号管理（account_redis.py）

通过 Redis 管理天眼查 API 账号的并发访问：

**功能**：
- 账号池管理
- 并发锁（防止同一账号同时使用）
- 频率控制

### 5. 响应工具（response_utils.py / response_codes.py）

统一 API 响应格式：

```python
response_utils.success(data, message)
response_utils.error(message, code)
```

**响应码**：
- `SUCCESS = 200`
- `BAD_REQUEST = 400`
- `INTERNAL_ERROR = 500`

### 6. SQL 查询（sql_queries.py / crawl_sql.py）

集中管理数据库查询：

| 模块 | 内容 |
|------|------|
| `sql_queries.py` | 通用查询（任务、批次、产业） |
| `crawl_sql.py` | 爬虫相关查询（爬取状态、结果存储） |

## 依赖关系

- **上游**：所有其他模块
- **下游**：MySQL、Redis
- **被依赖**：`api.py`、`tasks.py`、`business_api.py`、所有 `scripts/`

## 注意事项

- Redis 密码为空时 URL 格式为 `redis://:@host:port/db`（注意冒号后空）
- 数据库连接必须使用上下文管理器，确保连接正确关闭
- 日志文件路径 `logs/`，需确保目录存在
- 账号 Redis 管理是天眼查 API 并发控制的关键
