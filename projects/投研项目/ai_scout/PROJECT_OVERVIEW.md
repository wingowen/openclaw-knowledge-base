# AI Scout 投研系统 - 项目文档

> 生成时间：2026-03-14
> 项目路径：`/mnt/d/Pycharm/ai_scout_refactor`

---

## 一、项目概述

**AI Scout** 是一个基于 AI 的投资研究分析系统，专注于产业与企业的智能化评估。系统通过爬虫采集专利、企业工商信息、新闻舆情等多维数据，利用 LLM（大语言模型）进行自动评分、报告生成和相关性分析，最终输出产业报告和企业评估报告。

### 核心能力

| 能力 | 说明 |
|------|------|
| **产业分析** | 基于专利数据生成产业报告、核心标签提取 |
| **企业评估** | 多维度企业评分（竞争力/经营/潜力/声誉/技术） |
| **专利分析** | 专利爬取、相关性评分、标签提取、应用场景分析 |
| **数据采集** | 对接天眼查 API，采集企业多维度数据 |
| **报告生成** | LLM 自动生成产业报告和企业评估报告 |

---

## 二、技术栈

| 层级 | 技术 | 版本/说明 |
|------|------|-----------|
| **Web 框架** | Django + DRF | Django 5.2.9, DRF 3.16.1 |
| **任务队列** | Celery + Redis | Celery 5.6.0+ |
| **数据库** | MySQL | mysqlclient 2.2 |
| **AI/LLM** | LangChain + 多模型 | 豆包/Kimi/Qwen/Ollama |
| **API 文档** | drf-spectacular | Swagger UI |
| **可观测性** | Langfuse | LLM 调用追踪 |
| **包管理** | uv | Python >= 3.12 |
| **部署** | Docker + Gunicorn | 4 workers |

### Python 依赖分组

```toml
[project]          # 核心：Django, Celery, MySQL, gunicorn
agent              # AI：langchain, openai, pandas, scikit-learn
crawler            # 爬虫：selenium, lxml, paramiko
data-processing    # 数据：pymysql
dev                # 开发：basedpyright, jieba
test               # 测试：pytest, langfuse
```

---

## 三、项目结构

```
ai_scout_refactor/
├── ai_scout/                    # Django 项目配置
│   ├── settings.py              # 全局配置（DB/Redis/Celery/LLM/日志）
│   ├── urls.py                  # 路由配置
│   ├── celery.py                # Celery 应用初始化
│   └── wsgi.py / asgi.py        # WSGI/ASGI 入口
│
├── accounts/                    # 用户认证模块
│   ├── models.py                # APILog（接口审计日志）
│   ├── views.py                 # 登录/登出/用户信息 API
│   ├── serializers.py           # DRF 序列化器
│   ├── middleware.py            # API 日志中间件
│   └── urls.py                  # 认证路由
│
├── industrial_definition/       # 产业定义模块
│   ├── models.py                # 产业模型
│   ├── views.py                 # 产业 CRUD API
│   └── industry_sql.py          # 原生 SQL 查询
│
├── company_list/                # 企业长名单模块
│   ├── models.py                # 企业列表模型
│   ├── views.py                 # 企业列表 API
│   └── company_list_sql.py      # 原生 SQL 查询
│
├── company_shortlist/           # 企业短名单模块
│   ├── models.py                # 企业短名单模型
│   ├── views.py                 # 短名单 API
│   └── company_shortlist_sql.py # 评分计算、爬取状态管理
│
├── common/                      # 公共模块
│   ├── tasks.py                 # ⭐ 核心 Celery 任务（见下方详述）
│   ├── response_utils.py        # 统一响应格式
│   ├── response_codes.py        # 响应码定义
│   ├── logger_utils.py          # 日志工具
│   └── cleanup_apilogs.py       # 日志清理
│
├── ai_scout_agent/              # ⭐ AI Agent 模块（核心业务逻辑）
│   ├── core/
│   │   ├── query_gen.py         # 查询生成器
│   │   ├── query_parser.py      # 查询解析器
│   │   ├── schema.py            # 数据模式定义
│   │   ├── relevance/           # 相关性计算
│   │   │   ├── llm.py           # LLM 相关性评分
│   │   │   ├── vector.py        # 向量相关性评分
│   │   │   └── base.py          # 基础接口
│   │   ├── scoring/             # ⭐ 多维度评分系统
│   │   │   ├── company/         # 企业评分
│   │   │   │   ├── scorer.py                # 企业评分器
│   │   │   │   ├── dimensions/              # 5个评分维度
│   │   │   │   │   ├── competitiveness_scorer.py  # 竞争力
│   │   │   │   │   ├── operation_scorer.py        # 经营
│   │   │   │   │   ├── potential_scorer.py        # 潜力
│   │   │   │   │   ├── reputation_scorer.py       # 声誉
│   │   │   │   │   └── tech_scorer.py             # 技术
│   │   │   │   ├── tech_evaluation_builder.py     # 技术评估构建
│   │   │   │   ├── tech_evaluator.py              # 技术评估器
│   │   │   │   ├── reputation_service.py          # 声誉服务
│   │   │   │   └── providers/                     # 数据提供者
│   │   │   ├── dimensions/      # 专利评分维度
│   │   │   │   ├── application_value_scorer.py    # 应用价值
│   │   │   │   ├── development_potential_scorer.py # 发展潜力
│   │   │   │   ├── industrialization_feasibility_scorer.py  # 产业化可行性
│   │   │   │   ├── patent_impact_scorer.py        # 专利影响力
│   │   │   │   ├── patent_status_scorer.py        # 专利状态
│   │   │   │   ├── patent_type_scorer.py          # 专利类型
│   │   │   │   ├── technical_importance_scorer.py # 技术重要性
│   │   │   │   ├── technical_innovation_scorer.py # 技术创新性
│   │   │   │   └── technical_scarcity_scorer.py   # 技术稀缺性
│   │   │   ├── aggregator.py    # 评分聚合器
│   │   │   └── context.py       # 评分上下文
│   │   ├── report/              # 报告生成
│   │   │   ├── industry.py      # 产业报告生成器
│   │   │   ├── company.py       # 企业报告生成器
│   │   │   ├── context_builder.py    # 上下文构建
│   │   │   ├── patent_tag_extractor.py  # 专利标签提取
│   │   │   └── application_scenario_summarizer.py  # 应用场景总结
│   │   └── summarization/       # 摘要服务
│   │       └── reputation_summarizers.py  # 声誉摘要
│   ├── utils/
│   │   ├── llm_client.py        # ⭐ LLM 客户端工厂（多模型支持）
│   │   ├── search_provider.py   # 搜索提供者
│   │   ├── observability.py     # 可观测性（Langfuse）
│   │   ├── metrics.py           # 指标收集
│   │   ├── concurrency.py       # 并发工具
│   │   ├── summary/             # 摘要工具
│   │   └── url_checker/         # URL 检查
│   ├── prompts/                 # Prompt 管理
│   │   └── manager.py           # Prompt 模板管理器
│   └── examples/                # 使用示例和测试脚本
│
├── data_processing/             # 数据处理模块
│   ├── data_lib.py              # 数据访问层
│   ├── data_processor.py        # 专利数据处理管道
│   ├── company_data_processor.py # 企业数据处理
│   ├── sync_client.py           # 数据同步客户端
│   ├── sql_queries.py           # SQL 查询定义
│   ├── sql_util.py              # SQL 工具
│   ├── tyc_company.py           # 天眼查企业数据
│   ├── tyc_patenter_interface.py # 天眼查专利人接口
│   ├── batch_company_*_scoring.py  # 批量企业评分（5个维度）
│   ├── batch_company_tech_evaluation.py  # 批量技术评估
│   └── batch_patent_score/      # 批量专利评分
│       ├── batch_patent_scoring.py       # 综合专利评分
│       ├── batch_patent_tagging.py       # 专利标签提取
│       └── batch_patent_*_scoring.py     # 各维度专利评分
│
├── modules/tagging/             # 专利标签模块
│   ├── patent_tagging_batch.py  # 批量标签处理
│   ├── rule_based_extractor.py  # 规则提取器
│   └── schema.py                # 标签模式
│
├── patent_crawler/              # 专利爬虫模块
│   ├── task_crawl_patent.py     # 专利爬取任务
│   ├── get_data_from_tyc_api.py # 天眼查 API 调用
│   └── tyc.py                   # 天眼查封装
│
├── tests/                       # 测试目录
│   ├── scoring/                 # 评分测试
│   ├── report_gen/              # 报告生成测试
│   ├── relevance/               # 相关性测试
│   └── ...                      # 其他单元测试
│
├── docs/                        # 文档
├── docker-compose.yml           # Docker 编排
├── Dockerfile                   # Docker 镜像
├── start.sh                     # 生产启动脚本
└── pyproject.toml               # 项目依赖
```

---

## 四、核心模块详解

### 4.1 用户认证 (`accounts`)

提供基于 Django Session 的认证机制：

| 接口 | 方法 | 说明 |
|------|------|------|
| `/ai_scout/user/login/` | POST | 用户登录 |
| `/ai_scout/user/logout/` | GET | 用户登出 |
| `/ai_scout/user/info/` | GET | 获取当前用户信息 |

- 支持 API 访问日志审计（`APILog` 模型）
- 敏感数据自动脱敏（密码、Token 等）

### 4.2 评分系统 (`ai_scout_agent.core.scoring`)

#### 企业评分（5 个维度）

| 维度 | Scorer | 说明 |
|------|--------|------|
| 竞争力 | `CompetitivenessScorer` | 标准、证书、投资、招投标 |
| 经营 | `OperationScorer` | 业务、荣誉、招投标 |
| 潜力 | `PotentialScorer` | 股东、融资、人员 |
| 声誉 | `ReputationScorer` | 新闻舆情分析 |
| 技术 | `TechScorer` | 专利质量、技术评估 |

#### 专利评分（9 个维度）

| 维度 | 说明 |
|------|------|
| 应用价值 | 专利的商业应用潜力 |
| 发展潜力 | 技术发展趋势 |
| 产业化可行性 | 落地可行性评估 |
| 专利影响力 | 引用和影响范围 |
| 专利状态 | 法律状态 |
| 专利类型 | 发明/实用新型/外观 |
| 技术重要性 | 在技术链中的位置 |
| 技术创新性 | 创新程度 |
| 技术稀缺性 | 技术独占性 |

### 4.3 LLM 客户端 (`ai_scout_agent.utils.llm_client`)

支持多模型自动切换和降级：

| 提供者 | 模型 | 用途 |
|--------|------|------|
| 豆包 (Doubao) | doubao-seed-1-8 / 1-6-flash | 主力模型 |
| Kimi | kimi-k2-turbo-preview | 备选模型 |
| 通义千问 (Qwen) | qwen-plus / qwen-flash | 备选模型 |
| Ollama | qwen3:4b-instruct | 本地模型 |

### 4.4 Celery 任务 (`common/tasks`)

核心异步任务：

| 任务 | 说明 |
|------|------|
| `crawl_patent_task` | 专利爬取（调用爬虫服务） |
| `process_patent_data` | 专利数据处理（相关性评分→专利权人提取） |
| `extract_patent_tags` | 专利标签提取 |
| `generate_industry_report` | 产业报告生成 |
| `generate_company_reports` | 批量企业报告生成 |
| `integrated_patenter_task` | 专利权人→企业转换全流程 |
| `monitor_company_data_crawl` | 企业数据爬取监控（轮询） |
| `orchestrate_company_report_flow` | 企业报告流程编排 |
| `check_all_downstream_tasks` | 下游任务完成检查 |

### 4.5 数据处理 (`data_processing`)

| 模块 | 说明 |
|------|------|
| `data_lib.py` | 数据访问层，封装数据库操作 |
| `data_processor.py` | 专利数据处理管道 |
| `company_data_processor.py` | 企业数据处理（query_ids/类型/专利人回填） |
| `sync_client.py` | 爬虫数据同步到主库 |
| `batch_*_scoring.py` | 批量评分任务（竞争力/经营/潜力/声誉/技术） |

---

## 五、完整业务流程

```
1. 创建产业 → 定义搜索关键词
         ↓
2. 生成查询 (query_gen) → 生成搜索策略
         ↓
3. 专利爬取 (crawl_patent_task) → 调用爬虫服务
         ↓
4. 专利数据处理 (process_patent_data)
   ├→ 专利-Query 关联
   ├→ 专利相关性评分
   └→ 专利权人提取
         ↓
5. 专利标签提取 (extract_patent_tags)
         ↓
6. 专利权人→企业转换 (integrated_patenter_task)
   ├→ 企业数据处理
   ├→ 企业类型处理
   └→ 专利人名称回填
         ↓
7. 企业数据爬取 (monitor_company_data_crawl)
   ├→ 天眼查多维度数据（股东/融资/人员/标准/证书/投资/荣誉/业务/招投标/新闻）
   ├→ 专利全文爬取
   └→ 新闻分类
         ↓
8. 批量评分
   ├→ 竞争力评分
   ├→ 经营评分
   ├→ 潜力评分
   ├→ 声誉评分
   ├→ 专利评分
   ├→ 专利标签和应用场景提取
   └→ 技术评估生成
         ↓
9. 报告生成
   ├→ 产业报告 (generate_industry_report)
   └→ 企业报告 (generate_company_reports)
         ↓
10. 完成检查 (check_all_downstream_tasks)
```

---

## 六、API 端点

### 路由结构

| 前缀 | 模块 | 说明 |
|------|------|------|
| `/ai_scout/user/` | accounts | 用户认证 |
| `/ai_scout/industrial/` | industrial_definition | 产业管理 |
| `/ai_scout/company_list/` | company_list | 企业长名单 |
| `/ai_scout/company_shortlist/` | company_shortlist | 企业短名单 |
| `/ai_scout/admin/` | Django Admin | 管理后台 |
| `/ai_scout/api/docs/` | Swagger UI | API 文档（需 ENABLE_SWAGGER=True） |
| `/ai_scout/api/schema/` | OpenAPI Schema | API Schema |

---

## 七、部署架构

```
┌─────────────────────────────────────────────────┐
│                    Nginx 反向代理                  │
│              /ai_scout → Gunicorn                │
│              /flower → Celery Flower             │
└──────────────┬──────────────────┬───────────────┘
               │                  │
    ┌──────────▼──────┐  ┌───────▼────────┐
    │  Gunicorn :8000 │  │  Flower  :5555 │
    │  (4 workers)    │  │  (Celery监控)  │
    └──────────┬──────┘  └───────┬────────┘
               │                  │
    ┌──────────▼──────────────────▼──────────┐
    │            Celery Workers               │
    │         (queue: ai_scout_crawler)       │
    │         concurrency: 3                  │
    └──────────┬──────────────────┬──────────┘
               │                  │
    ┌──────────▼──────┐  ┌───────▼────────┐
    │  MySQL  :16121  │  │  Redis  :6379  │
    │  (test_as)      │  │  (Broker+结果)  │
    └─────────────────┘  └────────────────┘
               │
    ┌──────────▼──────────────────────────────┐
    │        爬虫服务 (ai_scout_crawler)        │
    │        Flask API :5000                   │
    └─────────────────────────────────────────┘
```

### Docker 部署

```bash
# 构建并启动
docker-compose up -d

# 服务端口
# - 8700 → Django (8000)
# - 5555 → Celery Flower
```

### 手动部署

```bash
# 1. 安装依赖
uv sync --all-groups

# 2. 启动服务
bash start.sh
# 包含：Gunicorn + Celery Worker + Celery Beat
```

---

## 八、配置说明

### 环境变量（`.env`）

| 变量 | 说明 | 示例 |
|------|------|------|
| `db.*` | MySQL 连接配置 | host/port/user/password/name |
| `redis_*` | Redis 连接配置 | host/port/password |
| `LLM_*` | LLM 配置 | API_KEY/BASE_URL/MODEL |
| `LLM_DOUBAO_*` | 豆包模型配置 | API_KEY/BASE_URL/MODEL |
| `LLM_KIMI_*` | Kimi 模型配置 | API_KEY/BASE_URL/MODEL |
| `LLM_QWEN_*` | 通义千问配置 | API_KEY/BASE_URL/MODEL |
| `LLM_OLLAMA_*` | Ollama 本地模型 | BASE_URL/MODEL |
| `LANGFUSE_*` | 可观测性配置 | SECRET_KEY/PUBLIC_KEY/BASE_URL |
| `tianyancha_api_key` | 天眼查 API Token | - |
| `clawer.api.url` | 爬虫服务地址 | http://127.0.0.1:5000 |

### Celery 配置

```python
CELERY_BROKER_URL = "redis://:{password}@{host}:{port}/1"
CELERY_RESULT_BACKEND = "redis://:{password}@{host}:{port}/2"
CELERY_TASK_TIME_LIMIT = 10800       # 3小时硬超时
CELERY_TASK_SOFT_TIME_LIMIT = 10200  # 2小时50分软超时
CELERY_WORKER_CONCURRENCY = 3        # 3个并发 worker
CELERY_DEFAULT_QUEUE = 'ai_scout_crawler'
```

---

## 九、开发指南

### 本地开发

```bash
# 安装依赖
uv sync --all-groups

# 设置环境变量
cp .env.sample .env
# 编辑 .env 配置数据库和 API Key

# 运行开发服务器
uv run python manage.py runserver

# 运行 Celery Worker
uv run celery -A ai_scout worker -l info

# 运行测试
uv run pytest
```

### 测试覆盖

| 测试目录 | 覆盖范围 |
|----------|----------|
| `tests/scoring/` | 企业评分、专利评分、声誉评分 |
| `tests/report_gen/` | 产业报告、企业报告集成测试 |
| `tests/relevance/` | LLM 相关性、向量相关性 |
| `tests/` (根) | 查询生成、LLM 客户端、可观测性、Schema 兼容性 |

---

## 十、注意事项

### 安全

- ⚠️ `.env` 文件包含敏感信息（API Keys、数据库密码），**不要提交到 Git**
- ⚠️ Django `SECRET_KEY` 硬编码在 `settings.py`，生产环境应改为环境变量
- ⚠️ `DEBUG = True` 在生产环境应关闭
- ⚠️ `CORS_ALLOW_ALL_ORIGINS = True` 生产环境应限制来源

### 性能

- Celery worker 并发数为 3，可根据服务器资源调整
- Gunicorn 使用 4 workers + 300s 超时
- LLM 调用是主要瓶颈，建议使用 flash 模型处理批量任务

### 依赖

- Python >= 3.12
- MySQL（需 libmariadb-dev 编译依赖）
- Redis（Celery Broker + 结果存储）
- 天眼查 API（企业数据采集）
