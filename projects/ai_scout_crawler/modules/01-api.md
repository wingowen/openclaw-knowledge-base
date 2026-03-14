# 模块分析：api（Flask API 服务）

> 项目：ai_scout_crawler_refactor
> 路径：`api.py`
> 生成时间：2026-03-14

---

## 职责

爬虫服务的 API 入口。提供 RESTful 接口管理爬虫任务的提交、执行和查询，支持 Celery 异步执行和本地直接执行两种模式。

## 文件信息

- **文件**：`api.py`（单文件模块）
- **框架**：Flask + Flask-CORS
- **端口**：5000

## API 端点

### 任务管理

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/tasks` | POST | 提交 Celery 异步任务 |
| `/api/local/tasks` | POST | 提交本地直接执行（同步） |
| `/api/tasks/<task_id>` | GET | 查询 Celery 任务状态 |
| `/api/patent/tasks` | POST | 提交专利爬虫专用任务 |

### 信息查询

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/scripts` | GET | 列出 scripts/ 下所有可用脚本 |
| `/api/health` | GET | 健康检查 |

### 数据传输

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/stream/data` | POST | 流式数据传输（chunked JSON Lines） |

### 业务接口（从 business_api 导入）

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/insert_task_record` | POST | 插入任务记录 |
| `/api/task_mirror/upsert` | POST | 任务镜像同步 |
| `/api/task_mirror/<task_id>` | GET | 获取任务镜像 |
| `/api/insert_industry_query` | POST | 插入产业查询 |
| `/api/sync_data` | GET | 数据同步 |

## 核心逻辑

### 1. 异步任务提交（/api/tasks）

```
接收 JSON → 验证 script_name → 校验路径安全 → 参数序列化
    ↓
run_crawler_task.delay(script_name, params)  # Celery 异步
    ↓
返回 task_id (202 Accepted)
```

### 2. 本地任务执行（/api/local/tasks）

```
接收 JSON → 验证 script_name → 校验路径安全 → 参数序列化
    ↓
subprocess.Popen([python, script, params_json])  # 直接执行
    ↓
实时读取 stdout（逐行打印）
    ↓
等待完成（超时 3600s）→ 解析 JSON 输出
    ↓
返回执行结果 (200)
```

**关键差异**：
- `/api/tasks` → Celery 异步，立即返回 task_id
- `/api/local/tasks` → 同步执行，等待完成后返回结果

### 3. 安全防护

```python
# 路径遍历防护
script_path = (SCRIPTS_DIR / script_name).resolve()
if not str(script_path).startswith(str(SCRIPTS_DIR.resolve())):
    return error("检测到路径遍历攻击!")

# 文件类型验证
if not script_path.name.endswith('.py'):
    return error("无效的脚本文件")

# 参数序列化验证
json.dumps(params)  # 必须可序列化
```

### 4. 流式数据传输（/api/stream/data）

使用 `chunked` 编码逐条发送 JSON Lines 格式数据：
```python
def generate():
    for record in records:
        yield json.dumps(record) + '\n'

return Response(generate(), mimetype='application/x-ndjson')
```

## 依赖关系

- **上游**：`ai_scout` 主系统通过 HTTP 调用
- **下游**：`tasks.py`（Celery 任务）、`business_api.py`（业务接口）、`scripts/`（爬虫脚本）
- **外部**：Celery Worker、Redis

## 注意事项

- `TASK_TIMEOUT = 3600`（1小时），本地执行的脚本受此限制
- `debug=False` 在生产环境必须设置
- CORS 全局开放（`CORS(app)`），生产环境应限制来源
- 路径安全校验是关键安全措施，修改需谨慎
