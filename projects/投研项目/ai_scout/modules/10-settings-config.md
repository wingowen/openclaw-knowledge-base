# 模块分析：ai_scout 配置层（Django 项目配置）

> 项目：ai_scout_refactor
> 路径：`ai_scout/`
> 生成时间：2026-03-14

---

## 职责

Django 项目配置和入口。包含全局设置、路由、Celery 初始化、WSGI/ASGI 入口。

## 文件结构

```
ai_scout/
├── settings.py        # ⭐ 全局配置
├── urls.py            # 路由配置
├── celery.py          # Celery 应用初始化
├── wsgi.py            # WSGI 入口
├── asgi.py            # ASGI 入口
├── local_settings.py  # 本地开发覆盖
└── __init__.py        # 包初始化
```

## 核心配置（settings.py）

### 应用注册

```python
INSTALLED_APPS = [
    # Django 内置
    'django.contrib.admin',
    'django.contrib.auth',
    # ...
    # 项目应用
    'accounts',
    'common',
    'industrial_definition',
    'company_list',
    'company_shortlist',
    # 第三方
    'rest_framework',
    'corsheaders',
    'drf_spectacular',
]
```

### 中间件

```python
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # CORS（最前）
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # 'accounts.middleware.APILoggingMiddleware',  # 已注释
]
```

### 数据库

MySQL（从环境变量读取）：
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('db.name', 'ai_scout'),
        'HOST': os.getenv('db.host', 'localhost'),
        'PORT': os.getenv('db.port', '16121'),
        # ...
    }
}
```

### Celery 配置

```python
CELERY_BROKER_URL = f"redis://:{password}@{host}:{port}/1"
CELERY_RESULT_BACKEND = f"redis://:{password}@{host}:{port}/2"
CELERY_TASK_TIME_LIMIT = 10800        # 3小时
CELERY_TASK_SOFT_TIME_LIMIT = 10200   # 2小时50分
CELERY_WORKER_CONCURRENCY = 3
```

### 日志配置

分级别分文件记录：
- `logs/debug.log` — DEBUG 级别
- `logs/info.log` — INFO 级别
- `logs/error.log` — ERROR 级别
- 各模块独立 logger：`ai_scout`、`ai_scout_agent`、`accounts`、`common`、`data_processing` 等

### API 文档

drf-spectacular 自动生成 OpenAPI Schema + Swagger UI：
- Schema: `/ai_scout/api/schema/`
- Swagger: `/ai_scout/api/docs/`
- 需设置 `ENABLE_SWAGGER=True` 环境变量

## 路由配置（urls.py）

| 路径 | 模块 |
|------|------|
| `/` | 首页 |
| `/admin/` | Django Admin |
| `/user/` | accounts（认证） |
| `/industrial/` | industrial_definition（产业） |
| `/company_list/` | company_list（长名单） |
| `/company_shortlist/` | company_shortlist（短名单） |
| `/api/schema/` | OpenAPI Schema（DEBUG 模式） |
| `/api/docs/` | Swagger UI（DEBUG 模式） |

## Celery 初始化（celery.py）

```python
app = Celery('ai_scout')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.worker_concurrency = 3
app.autodiscover_tasks()
app.conf.task_default_queue = 'ai_scout_crawler'
```

## 注意事项

- `SECRET_KEY` 硬编码在 settings.py，生产环境必须改为环境变量
- `DEBUG = True` 生产环境必须关闭
- `CORS_ALLOW_ALL_ORIGINS = True` 仅限开发环境
- `ALLOWED_HOSTS = ['*']` 生产环境应限制具体域名
- API 日志中间件已注释（`APILoggingMiddleware`），如需启用取消注释
