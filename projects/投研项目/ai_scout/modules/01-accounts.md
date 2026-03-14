# 模块分析：accounts（用户认证）

> 项目：ai_scout_refactor
> 路径：`accounts/`
> 生成时间：2026-03-14

---

## 职责

用户认证与 API 访问审计。提供基于 Django Session 的登录/登出机制，以及全量 API 请求日志记录。

## 文件结构

```
accounts/
├── models.py          # APILog 模型（接口审计日志）
├── views.py           # LoginAPIView / LogoutAPIView / UserInfoAPIView
├── serializers.py     # DRF 序列化器
├── urls.py            # 路由配置
├── middleware.py       # API 日志中间件
├── admin.py           # Django Admin 注册
└── apps.py            # App 配置
```

## 核心功能

### 1. 用户认证 API

| 接口 | 方法 | 权限 | 说明 |
|------|------|------|------|
| `/user/login/` | POST | 无需认证 | 用户名密码登录，创建 Session |
| `/user/logout/` | GET | 需认证 | 清除 Session 登出 |
| `/user/info/` | GET | 需认证 | 返回当前登录用户信息 |

**登录流程**：
1. `LoginSerializer` 验证用户名密码格式
2. `authenticate()` 校验用户凭证
3. `login()` 创建 Django Session
4. 返回 `username` + `user_id`

### 2. API 访问日志（APILog）

**模型字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `timestamp` | DateTime | 访问时间（自动） |
| `path` | CharField(500) | 请求路径 |
| `method` | CharField(10) | HTTP 方法 |
| `ip_address` | GenericIPAddressField | 客户端 IP |
| `user` | ForeignKey(User) | 操作用户（可空） |
| `request_data` | TextField | 请求体（脱敏） |
| `query_params` | TextField | 查询参数（脱敏） |
| `status_code` | IntegerField | 响应状态码 |
| `response_time` | FloatField | 响应时间(ms) |
| `response_data` | TextField | 响应体（脱敏） |
| `correlation_id` | CharField(100) | 关联追踪 ID |

**关键特性**：
- `managed = False` → 映射已有表，Django 不管理迁移
- **敏感数据脱敏**：自动识别 `password/pwd/secret/token` 字段，保留前3后2位
- 长度截断：request_data 10K、query_params 5K、response_data 20K

### 3. API 日志中间件

`APILoggingMiddleware` 自动记录所有 API 请求（排除路径可在 settings 配置）。

**排除路径**：`/admin/`、`/static/`、`/media/`、`/api/schema/`、`*/user/login/`、`*/user/logout/`、`*/api/docs/`

## 依赖关系

- **上游**：所有需要认证的 API 视图
- **下游**：Django Auth 系统、MySQL `api_log` 表
- **被依赖**：所有 DRF 视图的 `IsAuthenticated` 权限类

## 配置

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}
```

## 注意事项

- Session 认证适用于 Web 端，API 调用建议扩展 Token 认证
- APILog 表会快速增长，需定期清理（`cleanup_apilogs.py`）
- 脱敏规则仅针对常见密码字段名，自定义字段需手动处理
