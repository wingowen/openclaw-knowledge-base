# 模块分析：config（配置）

> 项目：ai_scout_crawler_refactor
> 路径：`config.py`
> 生成时间：2026-03-14

---

## 职责

爬虫服务的全局配置。集中管理数据库、Redis、Celery、天眼查 API 等所有配置项。

## 文件信息

- **文件**：`config.py`（单文件模块）
- **配置来源**：`.env` 文件（通过 `python-dotenv` 加载）

## 配置项

### 路径配置

| 变量 | 说明 | 值 |
|------|------|-----|
| `BASE_DIR` | 项目根目录 | `Path(__file__).parent` |
| `SCRIPTS_DIR` | 爬虫脚本目录 | `BASE_DIR / "scripts"` |

### MySQL 配置

| 变量 | 环境变量 | 默认值 |
|------|----------|--------|
| `MYSQL_HOST` | `db.host` | localhost |
| `MYSQL_PORT` | `db.port` | 3306 |
| `MYSQL_USER` | `db.user` | root |
| `MYSQL_PASSWORD` | `db.password` | 空 |
| `MYSQL_CHARSET` | - | utf8mb4 |

### Redis 配置

| 变量 | 环境变量 | 默认值 |
|------|----------|--------|
| `REDIS_HOST` | `redis.host` | localhost |
| `REDIS_PORT` | `redis.port` | 6379 |
| `REDIS_PASSWORD` | `redis.password` | 空 |

### Celery 配置

| 变量 | 环境变量 | 默认值 |
|------|----------|--------|
| `BROKER_URL` | `BROKER_URL` | `redis://:{pwd}@{host}:6379/5` |
| `RESULT_BACKEND` | `RESULT_BACKEND` | `redis://:{pwd}@{host}:6379/6` |
| `CELERY_DEFAULT_QUEUE` | `celery.default.queue` | `ai_scout_crawler_test` |
| `TASK_TIMEOUT` | - | 3600 秒（1小时） |
| `MAX_RETRIES` | - | 0（不重试） |

### 日志配置

| 变量 | 环境变量 | 默认值 |
|------|----------|--------|
| `LOG_LEVEL` | `LOG_LEVEL` | INFO |
| `LOG_FORMAT` | - | `%(asctime)s - %(name)s - %(levelname)s - %(message)s` |

### 天眼查配置

| 变量 | 环境变量 | 说明 |
|------|----------|------|
| `TIANYANCHA_TOKEN` | `tianyancha_api_key` | API Token |

**API 价格配置**（内置）：
```python
TIANYANCHA_API_PRICE = {
    '招投标': 0.20, '企业荣誉': 0.50, '企业标准': 1.00,
    '企业主要人员': 0.15, '企业主要人员简介': 0.10,
    '企业融资历史': 0.10, '企业对外投资': 0.15,
    '企业股东信息': 0.15, '企业资质证书': 0.20,
    '企业业务': 0.10, '企业新闻舆情': 0.15,
}
```

## 依赖关系

- **被依赖**：所有模块都从本模块读取配置
- **配置源**：`.env` 文件

## 注意事项

- 所有敏感配置通过环境变量注入，不要硬编码
- Redis DB 5/6 专用于 Celery，避免与其他服务冲突
- `TASK_TIMEOUT` 需根据最长爬虫任务调整
- 天眼查 API 价格用于成本追踪，价格变动需手动更新
