# AI Scout Crawler - 爬虫服务文档

> 生成时间：2026-03-14
> 项目路径：`/mnt/d/Pycharm/ai_scout_crawler_refactor`

---

## 一、项目概述

**AI Scout Crawler** 是 AI Scout 投研系统的爬虫服务模块，提供 RESTful API 接口管理各类数据爬取任务。服务通过 Celery 异步执行爬虫脚本，支持专利爬取、天眼查企业数据采集、新闻分类等功能。

### 核心定位

- 作为 **独立微服务** 运行，与主系统 (`ai_scout`) 通过 HTTP API 通信
- 提供 **统一的爬虫任务管理**（提交、查询、执行）
- 支持 **两种执行模式**：Celery 异步执行 / 本地直接执行
- 负责 **多数据源采集**：专利、天眼查（11个维度）、新闻

---

## 二、技术栈

| 层级 | 技术 | 版本/说明 |
|------|------|-----------|
| **Web 框架** | Flask | 2.3.0 ~ 3.0.0 |
| **任务队列** | Celery + Redis | Celery 5.5.0 |
| **数据库** | MySQL | PyMySQL |
| **ORM** | SQLAlchemy | 2.0.46 |
| **爬虫引擎** | Selenium | 3.141.0 |
| **HTML 解析** | lxml | - |
| **中文分词** | jieba | - |
| **日志** | loguru | - |
| **Python** | 3.8 | 注：pyproject.toml 要求 <3.9 |

---

## 三、项目结构

```
ai_scout_crawler_refactor/
├── api.py                   # ⭐ Flask API 主入口
├── business_api.py          # 业务 API（数据同步、任务镜像）
├── config.py                # 配置文件
├── tasks.py                 # ⭐ Celery 任务定义
├── start_worker.py          # Celery Worker 启动脚本
├── run_api.sh               # API 服务启动脚本
│
├── scripts/                 # ⭐ 爬虫脚本目录
│   ├── step_one.py          # 专利爬取 v1
│   ├── step_one_v2.py       # 专利爬取 v2（当前版本）
│   ├── task_crawl_patent.py        # 专利爬取任务
│   ├── task_crawl_patent_client.py # 专利爬取客户端
│   ├── task_crawl_patent_v2.py     # 专利爬取 v2
│   ├── company_patent_full_crawl.py    # 企业专利全文爬取
│   ├── company_patent_count_crawl.py   # 企业专利数量爬取
│   ├── task_classify_news.py       # 新闻分类任务
│   ├── tyc_*.py                    # 天眼查爬虫（11个维度）
│   │   ├── tyc_business.py         # 企业业务
│   │   ├── tyc_certificate.py      # 资质证书
│   │   ├── tyc_competitive_dimension.py  # 竞争力维度
│   │   ├── tyc_financing.py        # 融资历史
│   │   ├── tyc_honor.py            # 企业荣誉
│   │   ├── tyc_investment.py       # 对外投资
│   │   ├── tyc_member.py           # 主要人员
│   │   ├── tyc_member_detail.py    # 人员详情
│   │   ├── tyc_news.py             # 新闻舆情
│   │   ├── tyc_operation_dimension.py  # 经营维度
│   │   ├── tyc_potential_dimension.py  # 潜力维度
│   │   ├── tyc_reputation_dimension.py # 声誉维度
│   │   ├── tyc_shareholder.py      # 股东信息
│   │   ├── tyc_standard.py         # 企业标准
│   │   ├── tyc_ztb.py              # 招投标
│   │   └── tyc_directory_label.py  # 目录标签
│   └── hello_world.py       # 测试脚本
│
├── news_classification/     # 新闻分类模块
│   ├── core.py              # 分类核心逻辑
│   ├── news_dao.py          # 新闻数据访问
│   ├── news_sql.py          # SQL 查询
│   ├── config/settings.py   # 分类配置
│   └── models/news.py       # 新闻模型
│
├── utils/                   # 工具模块
│   ├── celery_app.py        # Celery 应用配置
│   ├── database.py          # 数据库连接
│   ├── sql_util.py          # SQL 工具
│   ├── sql_queries.py       # SQL 查询
│   ├── crawl_sql.py         # 爬虫 SQL
│   ├── account_redis.py     # 账号 Redis 管理
│   ├── import_accounts.py   # 账号导入
│   ├── logger.py            # 日志配置
│   ├── obj.py               # 对象工具
│   ├── response_codes.py    # 响应码
│   └── response_utils.py    # 响应工具
│
├── data/                    # 数据目录
├── doc/                     # 文档目录
├── logs/                    # 日志目录
├── test/                    # 测试目录
│   ├── api_submit_example.py
│   ├── sync_client_example.py
│   ├── test_*.py
│   └── ...
│
├── .env                     # 环境变量
├── pyproject.toml           # 项目依赖
└── uv.lock                  # 依赖锁定
```

---

## 四、核心模块详解

### 4.1 API 服务 (`api.py`)

Flask 应用，提供以下端点：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/tasks` | POST | 提交 Celery 异步爬虫任务 |
| `/api/local/tasks` | POST | 提交本地直接执行任务（同步） |
| `/api/tasks/<task_id>` | GET | 查询 Celery 任务状态 |
| `/api/patent/tasks` | POST | 提交专利爬虫任务 |
| `/api/scripts` | GET | 列出可用爬虫脚本 |
| `/api/stream/data` | POST | 流式数据传输（chunked） |
| `/api/health` | GET | 健康检查 |
| `/api/insert_task_record` | POST | 插入任务记录 |
| `/api/task_mirror/upsert` | POST | 任务镜像同步 |
| `/api/task_mirror/<task_id>` | GET | 获取任务镜像 |
| `/api/insert_industry_query` | POST | 插入产业查询 |
| `/api/sync_data` | GET | 数据同步 |

#### 任务提交流程

```
POST /api/tasks
    ↓
验证脚本路径（防路径遍历）
    ↓
序列化参数为 JSON
    ↓
提交到 Celery → run_crawler_task.delay()
    ↓
返回 task_id（202 Accepted）

POST /api/local/tasks
    ↓
验证脚本路径
    ↓
直接 subprocess.Popen 执行
    ↓
实时读取 stdout
    ↓
返回执行结果（同步）
```

### 4.2 Celery 任务 (`tasks.py`)

| 任务 | 说明 | 超时 |
|------|------|------|
| `run_crawler_task` | 通用爬虫脚本执行器 | 1 小时 |
| `run_patent_crawler_task` | 专利爬虫任务执行器 | 1 小时 |

**安全特性**：
- 路径遍历攻击防护
- 参数 JSON 序列化验证
- 实时日志输出
- 超时自动终止

### 4.3 天眼查爬虫（11 个维度）

| 脚本 | 维度 | 数据类型 | API 单价 |
|------|------|----------|----------|
| `tyc_business.py` | 经营 | 企业业务 | ¥0.10 |
| `tyc_honor.py` | 经营 | 企业荣誉 | ¥0.50 |
| `tyc_ztb.py` | 经营 | 招投标 | ¥0.20 |
| `tyc_standard.py` | 竞争力 | 企业标准 | ¥1.00 |
| `tyc_certificate.py` | 竞争力 | 资质证书 | ¥0.20 |
| `tyc_investment.py` | 竞争力 | 对外投资 | ¥0.15 |
| `tyc_shareholder.py` | 潜力 | 股东信息 | ¥0.15 |
| `tyc_financing.py` | 潜力 | 融资历史 | ¥0.10 |
| `tyc_member.py` | 潜力 | 主要人员 | ¥0.15 |
| `tyc_member_detail.py` | 潜力 | 人员简介 | ¥0.10 |
| `tyc_news.py` | 声誉 | 新闻舆情 | ¥0.15 |

### 4.4 业务 API (`business_api.py`)

提供主系统与爬虫服务的数据同步接口：

| 函数 | 说明 |
|------|------|
| `upsert_task_mirror()` | 任务镜像同步（industry/batch/task/industry_query） |
| `get_task_mirror()` | 获取任务镜像 |
| `insert_task_record()` | 插入任务记录 |
| `insert_industry_query()` | 插入产业查询 |
| `sync_data()` | 数据同步 |

### 4.5 新闻分类 (`news_classification`)

| 模块 | 说明 |
|------|------|
| `core.py` | 分类核心逻辑（基于 jieba 分词 + 词典） |
| `news_dao.py` | 新闻数据访问层 |
| `news_sql.py` | SQL 查询 |
| `config/settings.py` | 分类配置 |
| `models/news.py` | 新闻数据模型 |

### 4.6 工具模块 (`utils`)

| 模块 | 说明 |
|------|------|
| `celery_app.py` | Celery 应用配置（Redis Broker） |
| `database.py` | 数据库连接管理 |
| `sql_util.py` | SQL 工具函数 |
| `sql_queries.py` | 数据库查询 |
| `crawl_sql.py` | 爬虫相关 SQL |
| `account_redis.py` | 天眼查账号 Redis 管理（并发控制） |
| `import_accounts.py` | 账号批量导入 |
| `logger.py` | loguru 日志配置 |

---

## 五、数据流

### 5.1 专利爬取流程

```
主系统 → POST /api/tasks
        {script_name: "step_one_v2.py", params: {...}}
              ↓
        Celery: run_crawler_task
              ↓
        执行 step_one_v2.py
              ↓
        Selenium 爬取专利数据
              ↓
        结果写入 MySQL
              ↓
        返回执行结果
```

### 5.2 企业数据爬取流程

```
主系统 → POST /api/local/tasks
        {script_name: "tyc_*.py", params: {company_id, industry_id}}
              ↓
        直接执行（同步等待）
              ↓
        调用天眼查 API
              ↓
        数据写入 MySQL
              ↓
        返回结果
```

### 5.3 数据同步流程

```
爬虫服务 (MySQL:test_asc)
        ↓
    sync_data API
        ↓
主系统 (MySQL:test_as)
```

---

## 六、配置说明

### 环境变量（`.env`）

| 变量 | 说明 | 示例值 |
|------|------|--------|
| `db.host` | MySQL 主机 | 139.159.157.172 |
| `db.port` | MySQL 端口 | 16121 |
| `db.user` | MySQL 用户 | root |
| `db.password` | MySQL 密码 | - |
| `db.name` | 数据库名 | test_asc |
| `redis.host` | Redis 主机 | 127.0.0.1 |
| `redis.port` | Redis 端口 | 6379 |
| `redis.password` | Redis 密码 | - |
| `CELERY_DEFAULT_QUEUE` | Celery 队列名 | ai_scout_crawler_test |
| `tianyancha_api_key` | 天眼查 API Token | - |
| `env` | 环境标识 | TEST |

### Celery 配置

```python
BROKER_URL = f'redis://:{password}@{host}:{port}/5'
RESULT_BACKEND = f'redis://:{password}@{host}:{port}/6'
CELERY_DEFAULT_QUEUE = 'ai_scout_crawler_test'
TASK_TIMEOUT = 3600  # 1小时
MAX_RETRIES = 0      # 不重试
```

---

## 七、启动方式

### 方式一：Flask 直接启动（开发环境）

```bash
# 安装依赖
pip install -r requirements.txt

# 启动 API 服务
python api.py
# 或
bash run_api.sh

# 默认地址：http://127.0.0.1:5000
```

### 方式二：分离启动（推荐）

```bash
# 1. 启动 Celery Worker
python start_worker.py
# 或
celery -A utils.celery_app worker --loglevel=info -Q ai_scout_crawler_test

# 2. 启动 API 服务
python api.py
```

---

## 八、与主系统的交互

```
┌─────────────────────────────────────────────────────────────┐
│                    ai_scout (Django)                         │
│                                                             │
│  common/tasks.py                                            │
│      │                                                      │
│      ├─ crawl_patent_task                                   │
│      │   └─ POST {CLAWER_API_URL}/api/local/tasks          │
│      │       {script_name: "step_one_v2.py", ...}           │
│      │                                                      │
│      ├─ monitor_company_data_crawl                          │
│      │   └─ POST {CLAWER_API_URL}/api/local/tasks          │
│      │       {script_name: "tyc_*.py", ...}                 │
│      │                                                      │
│      └─ trigger_patent_count_crawl                          │
│          └─ POST {CLAWER_API_URL}/api/local/tasks           │
│              {script_name: "company_patent_count_crawl.py"} │
│                                                             │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              ai_scout_crawler (Flask)                        │
│                                                             │
│  api.py                                                     │
│      ├─ /api/local/tasks → 直接执行脚本                       │
│      ├─ /api/tasks → Celery 异步执行                         │
│      └─ /api/stream/data → 流式数据传输                       │
│                                                             │
│  business_api.py                                            │
│      ├─ /api/task_mirror/upsert → 任务镜像同步                │
│      ├─ /api/insert_task_record → 插入任务记录                │
│      └─ /api/sync_data → 数据同步                            │
│                                                             │
│  scripts/                                                   │
│      ├─ step_one_v2.py → 专利爬取                            │
│      ├─ company_patent_*.py → 企业专利爬取                    │
│      ├─ tyc_*.py → 天眼查数据采集                             │
│      └─ task_classify_news.py → 新闻分类                     │
│                                                             │
└───────────────────────────┬─────────────────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
         天眼查 API    专利数据库     新闻来源
```

---

## 九、天眼查 API 集成

### API 调用配置

```python
TIANYANCHA_TOKEN = os.getenv('tianyancha_api_key')
```

### 费用管理

系统内置了天眼查 API 价格配置，用于成本追踪：

```python
TIANYANCHA_API_PRICE = {
    '招投标': 0.20,
    '企业荣誉': 0.50,
    '企业标准': 1.00,
    '企业主要人员': 0.15,
    '企业主要人员简介': 0.10,
    '企业融资历史': 0.10,
    '企业对外投资': 0.15,
    '企业股东信息': 0.15,
    '企业资质证书': 0.20,
    '企业业务': 0.10,
    '企业新闻舆情': 0.15,
}
```

---

## 十、开发指南

### 添加新爬虫脚本

1. 在 `scripts/` 目录创建 Python 脚本
2. 脚本接收 JSON 参数（通过 `sys.argv[1]`）
3. 输出结果到 stdout（JSON 格式）
4. 通过 `/api/tasks` 或 `/api/local/tasks` 调用

### 脚本标准模板

```python
#!/usr/bin/env python
import sys
import json

def main(params):
    """主函数"""
    # 从 params 获取参数
    company_id = params.get('company_id')
    
    # 执行爬取逻辑
    result = do_crawl(company_id)
    
    # 返回 JSON 结果
    print(json.dumps({
        "success": True,
        "data": result
    }, ensure_ascii=False))

if __name__ == '__main__':
    params = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    main(params)
```

### 错误处理规范

- 所有 API 返回统一 JSON 格式，包含 `success` 字段
- `success=True` 表示成功，`success=False` 表示失败
- 错误响应包含 `error` 字段描述错误原因
- HTTP 状态码：200 成功，400 参数错误，403 安全拦截，500 服务错误

---

## 十一、注意事项

### 安全

- ✅ 已实现路径遍历攻击防护
- ✅ 参数 JSON 序列化验证
- ⚠️ `.env` 包含数据库密码和 API Key，不要提交到 Git
- ⚠️ 生产环境应设置 `debug=False`
- ⚠️ 建议使用 gunicorn 等 WSGI 服务器部署

### 性能

- Celery Worker 默认 1 个并发（可通过 `-c` 参数调整）
- 任务超时 1 小时，不自动重试
- 天眼查 API 调用受频率限制，需控制并发

### 兼容性

- Python 版本要求 3.8（pyproject.toml 限制 <3.9）
- Selenium 3.141.0（较旧版本，注意浏览器驱动兼容性）
- urllib3 < 1.26（Selenium 3.x 兼容要求）

### 依赖关系

- 依赖 Redis（Celery Broker）
- 依赖 MySQL（数据存储）
- 依赖天眼查 API（企业数据）
- 主系统通过 `CLAWER_API_URL` 环境变量连接本服务
