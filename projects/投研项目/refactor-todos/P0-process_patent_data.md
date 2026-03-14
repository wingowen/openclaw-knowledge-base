# P0: process_patent_data 重构 TODO 文档

## 任务概述

**位置**: `common/tasks.py:325`

**功能**: 专利数据处理任务，在爬虫任务成功完成后触发，负责：
1. 构建专利_query关联数据 (PatentTaskToPatentQuery)
2. 执行专利相关性评分 (PatentRelevanceProcessor)
3. 提取专利权人 (QueryPatentToPatenter)
4. 处理产业专利权人数据 (IndustryPatenterExtractor)

**当前问题**: 
- 代码中有 `# TODO 待改造` 注释（340行、384行、391行）
- 直接读写主库数据，假设爬虫数据已同步到本地
- 没有在处理前调用同步逻辑

## 涉及的数据库表

### test_as (主库)
| 表名 | 操作 | 说明 |
|------|------|------|
| `task` | READ | 获取 query_id, crawl_is_complete |
| `patent_task` | READ | 获取关联的专利ID |
| `patent` | READ | 获取专利权人信息 |
| `patent_query` | READ/WRITE | 专利与query关联 |
| `patenter` | READ/WRITE | 专利权人表 |
| `patent_patenter` | WRITE | 专利-专利权人关联 |
| `patent_query_score` | WRITE | 专利相关性评分 |
| `batch` | READ | 批次信息 |
| `industry_query` | READ | 产业查询信息 |

### test_asc (爬虫库)
| 表名 | 操作 | 说明 |
|------|------|------|
| `patent` | READ | 爬取的原始专利数据 |
| `patenter` | READ | 爬取的原始专利权人 |
| `patent_task` | READ | 爬取任务关联 |

## 当前数据流

```
crawl_patent_task (已完成重构)
    ↓
sync_patent_data()  ← 同步爬虫数据到主库
    ↓
process_patent_data (当前问题点)
    ├── PatentTaskToPatentQuery
    │   ├── READ: task, patent_task (假设已同步)
    │   └── WRITE: patent_query
    ├── PatentRelevanceProcessor
    │   ├── READ: task, industry_query, patent, patent_query
    │   └── WRITE: patent_query_score
    ├── QueryPatentToPatenter
    │   ├── READ: patent_task, patent (假设已同步)
    │   └── WRITE: patenter, patent_patenter
    └── IndustryPatenterExtractor
        └── READ: batch, industry_query, patent_query, patent_patenter, patenter
```

## 目标数据流

```
process_patent_data (重构后)
    ├── Step 0: 调用 sync_patent_data() 同步爬虫数据
    │   └── 使用 sync_client.sync_patent_data(task_id, industry_id)
    ├── Step 1: PatentTaskToPatentQuery
    ├── Step 2: PatentRelevanceProcessor  
    ├── Step 3: QueryPatentToPatenter
    └── Step 4: IndustryPatenterExtractor
```

## 详细重构步骤

### 步骤 1: 在 process_patent_data 中添加同步调用

**文件**: `common/tasks.py`

**修改位置**: 第 335-341 行之间，在 `try:` 块开始后立即添加同步逻辑

```python
def process_patent_data(self, task_id, industry_id):
    logger.info(f"开始执行专利数据处理任务 - task_id: {task_id}, industry_id: {industry_id}")
    
    try:
        # ===== 新增：同步爬虫数据 =====
        from data_processing.sync_client import sync_patent_data
        logger.info(f"开始同步爬虫数据 - task_id: {task_id}, industry_id: {industry_id}")
        sync_result = sync_patent_data(task_id=task_id, industry_id=industry_id)
        if not sync_result.get('success'):
            raise Exception(f"爬虫数据同步失败: {sync_result.get('error', '未知错误')}")
        logger.info(f"爬虫数据同步完成 - task_id: {task_id}, 结果: {sync_result}")
        # ===== 同步结束 =====
        
        # 导入数据处理类
        from data_processing.data_processor import PatentTaskToPatentQuery, QueryPatentToPatenter, IndustryPatenterExtractor
        ...
```

### 步骤 2: 检查 sync_patent_data 函数签名

**文件**: `data_processing/sync_client.py`

**确认**: 查看 sync_patent_data 是否支持 task_id 和 industry_id 参数
- 如果只支持 task_id，则只需要传入 task_id
- 如果需要 industry_id，则传入两个参数

### 步骤 3: 更新 sync_patent_data (如需要)

**文件**: `data_processing/sync_client.py`

如果 sync_patent_data 不接受 industry_id 参数，需要添加支持：

```python
def sync_patent_data(task_id=None, industry_id=None):
    """同步专利相关数据"""
    tables = ['patent', 'industry_query', 'patenter', 'patent_query', 'patent_patenter', 'patent_task']
    # ... 现有逻辑 ...
    
    # 如果指定了 industry_id，额外同步该产业相关数据
    if industry_id:
        # 确保 industry_query 等表也同步
        pass
```

## 依赖关系

- **前置任务**: 无（这是 P0 最高优先级）
- **依赖模块**: 
  - `data_processing.sync_client.sync_patent_data` (已存在)
  - `data_processing.data_processor.PatentTaskToPatentQuery` (已存在)
  - `data_processing.data_processor.QueryPatentToPatenter` (已存在)
  - `data_processing.data_processor.IndustryPatenterExtractor` (已存在)

## 测试验证方法

### 1. 单元测试
```python
# 测试 sync_patent_data 可正常调用
from data_processing.sync_client import sync_patent_data
result = sync_patent_data(task_id=1, industry_id=1)
assert result.get('success') == True
```

### 2. 集成测试
```bash
# 触发 process_patent_data 任务
celery -A ai_scout worker -Q ai_scout_crawler -l info &
celery call common.tasks.process_patent_data --args='[1, 1]'
```

### 3. 验证清单
- [ ] 同步调用在处理前执行
- [ ] 同步失败时任务正确报错
- [ ] 同步完成后数据可正常读取
- [ ] 处理结果正确写入主库

## 风险点和注意事项

1. **同步时机**: 确保在所有数据处理前完成同步
2. **幂等性**: sync_patent_data 使用 UPSERT，可重复执行
3. **错误处理**: 同步失败应立即终止任务
4. **性能**: 大数据量同步可能耗时较长，考虑超时设置
5. **增量同步**: 确保只同步增量数据，避免全量同步
