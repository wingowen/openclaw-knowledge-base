# P3: check_all_downstream_tasks 重构 TODO 文档

## 任务概述

**位置**: `common/tasks.py:102`

**功能**: 检查所有下游任务的完成状态，判断整个产业分析流程是否全部完成：
1. 读取 `task` 表检查爬虫任务状态
2. 读取 `data_task` 表检查数据处理任务状态
3. 汇总所有任务状态，判断是否全部完成
4. 更新产业/批次的整体完成状态

**当前问题**:
- 直接读取 `task` 表（爬虫侧表），应从同步后的数据读取
- 读取 `data_task` 表（主系统表），位置正确
- 整体风险较低：只读操作，不写入爬虫侧表

**优先级**: P3（低风险，纯状态检查）

## 涉及的数据库表

### test_as (主库)
| 表名 | 操作 | 说明 |
|------|------|------|
| `task` | READ | 爬虫任务状态（应从同步后数据读取） |
| `data_task` | READ | 数据处理任务状态（主系统表，正确） |
| `batch` | READ | 批次信息 |
| `industry` | READ/WRITE | 产业状态更新 |

### test_asc (爬虫库)
| 表名 | 操作 | 说明 |
|------|------|------|
| `task` | READ | 爬虫任务的原始状态 |

## 当前数据流

```
check_all_downstream_tasks(industry_id)
    ├── 读取 task 表 → 获取爬虫任务状态
    ├── 读取 data_task 表 → 获取数据处理任务状态
    ├── 汇总状态判断
    └── 更新 industry 表完成状态
```

## 目标数据流

```
check_all_downstream_tasks (重构后)
    ├── 方案 A（推荐）: 直接读取主库 task 表
    │   └── task 表已通过 sync_task_data() 同步到主库
    ├── 方案 B: 通过 API 获取任务状态
    │   └── GET /api/tasks/<task_id> 查询爬虫服务
    ├── 读取 data_task 表（不变）
    ├── 汇总状态判断
    └── 更新 industry 表完成状态
```

## 详细重构步骤

### 步骤 1: 确认 task 表同步机制

**文件**: `data_processing/sync_client.py`

**检查**: 确认 `sync_patent_data()` 或其他同步函数是否同步了 `task` 表
- 如果已同步 → 无需额外改动，task 表数据已可用
- 如果未同步 → 需要在上游任务中增加 task 表同步

### 步骤 2（可选）: 添加任务状态查询 API 调用

**文件**: `common/tasks.py`

如果需要实时状态而非同步后的状态，可调用爬虫服务 API：

```python
# Before: 直接查询主库 task 表
cursor.execute("SELECT status FROM task WHERE id = %s", (task_id,))

# After: 调用爬虫服务 API 获取实时状态
import requests
CLAWER_API_URL = os.getenv('clawer.api.url')
response = requests.get(f"{CLAWER_API_URL}/api/tasks/{task_id}")
task_status = response.json().get('status')
```

### 步骤 3: 保持现有逻辑不变（如 task 表已同步）

如果上游任务已有 task 表同步步骤，则此任务无需大改，仅需：
- 确认 task 表在主库的数据是最新的
- 添加数据时效性检查（如同步时间戳检查）

## 依赖关系

- **前置任务**: 无特定前置，但依赖 task 表已同步
- **被依赖**: `orchestrate_company_report_flow` 调用此任务判断流程完成
- **依赖模块**: 无特殊依赖

## 测试验证方法

### 1. 验证 task 表数据可用
```python
from data_processing.sql_util import get_db_connection
conn = get_db_connection()
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM task WHERE industry_id = %s", (industry_id,))
count = cursor.fetchone()[0]
assert count > 0, "task 表应有数据"
```

### 2. 集成测试
```bash
celery call common.tasks.check_all_downstream_tasks --args='[1]'
```

### 3. 验证清单
- [ ] task 表数据可正常读取
- [ ] data_task 表数据可正常读取
- [ ] 状态汇总逻辑正确
- [ ] industry 表完成状态正确更新

## 风险点和注意事项

1. **低风险**: 此任务只做状态检查和更新，不影响核心数据
2. **数据时效**: 如果 task 表同步有延迟，可能导致状态判断不准确
3. **幂等性**: 重复执行不会产生副作用

## 与其他任务的关系

```
crawl_patent_task → task 表写入
       ↓
process_patent_data → data_task 表写入
       ↓
extract_patent_tags → data_task 表写入
       ↓
integrated_patenter_task → data_task 表写入
       ↓
monitor_company_data_crawl → data_task 表写入
       ↓
check_all_downstream_tasks ← 汇总所有状态
       ↓
orchestrate_company_report_flow ← 依赖本任务结果
```
