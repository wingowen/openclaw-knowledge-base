# 模块分析：tasks（Celery 任务）

> 项目：ai_scout_crawler_refactor
> 路径：`tasks.py`
> 生成时间：2026-03-14

---

## 职责

定义爬虫服务的 Celery 异步任务。提供安全的子进程执行框架，负责启动和监控爬虫脚本的运行。

## 文件信息

- **文件**：`tasks.py`（单文件模块）
- **Celery App**：从 `utils.celery_app` 导入

## 任务定义

### 1. run_crawler_task（通用爬虫执行器）

```python
@app.task(bind=True, soft_time_limit=3600, time_limit=3630)
def run_crawler_task(self, script_name: str, params: dict)
```

**功能**：安全执行 `scripts/` 目录下的任意 Python 爬虫脚本。

**执行流程**：
1. **路径验证**：防止路径遍历，确保脚本在 `scripts/` 目录内
2. **参数序列化**：JSON 序列化参数，确保可传递
3. **子进程执行**：`subprocess.Popen` 启动脚本
4. **实时日志**：逐行读取 stdout/stderr 并记录
5. **结果解析**：尝试 JSON 解析输出，失败则返回原始文本
6. **状态返回**：包含 `success`、`returncode`、`stderr`

**安全特性**：
```python
# 路径遍历防护
if not str(script_path).startswith(str(SCRIPTS_DIR.resolve())):
    raise ValueError("检测到路径遍历攻击!")

# 文件类型检查
if not script_path.name.endswith('.py'):
    raise ValueError("无效的脚本文件")

# 显式禁用 shell
subprocess.Popen(..., shell=False)
```

### 2. run_patent_crawler_task（专利爬虫执行器）

```python
@app.task(bind=True, soft_time_limit=3600, time_limit=3630)
def run_patent_crawler_task(self, keywords: str, task_id: int, use_api: bool = False)
```

**功能**：专用的专利爬虫任务，通过客户端脚本调用主爬虫逻辑。

**执行流程**：
1. 验证客户端脚本 `task_crawl_patent_client.py` 存在
2. 构建参数：keywords + task_id + use_api
3. 执行客户端脚本
4. 实时日志输出
5. 返回执行结果

**设计意图**：使用客户端脚本而非直接运行爬虫，避免 Celery 环境中的兼容性问题。

## 子进程管理

**输出读取方式**：
```python
process = subprocess.Popen(
    [python_exec, script_path, params_json],
    cwd=SCRIPTS_DIR,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    env=env,
    shell=False
)

# 实时读取
while process.poll() is None:
    stdout_line = process.stdout.readline()
    stderr_line = process.stderr.readline()
    # 记录到日志...
```

**超时处理**：
- 软超时 3600s → 发出信号，任务可清理
- 硬超时 3630s → 强制终止

## 依赖关系

- **上游**：`api.py` 通过 `task.delay()` 触发
- **下游**：`scripts/` 目录下的爬虫脚本
- **依赖**：Redis（Celery Broker）、`utils.celery_app`

## 错误处理

| 错误类型 | 处理方式 |
|----------|----------|
| 脚本不存在 | 返回 `{"error": "无效的脚本文件", "success": False}` |
| 路径遍历 | 返回 `{"error": "检测到路径遍历攻击", "success": False}` |
| 参数序列化失败 | 返回 `{"error": "参数无法JSON序列化", "success": False}` |
| 执行超时 | `TimeoutError` + 任务标记失败 |
| 脚本非零退出 | 返回 `success: False` + stdout/stderr |

## 注意事项

- 所有脚本通过 `sys.argv[1]` 接收 JSON 参数
- 脚本输出应为 JSON 格式，否则返回原始文本
- `PYTHONPATH` 设置为 `scripts/` 的父目录，确保模块导入正确
- 不设置自动重试（`MAX_RETRIES = 0`）
