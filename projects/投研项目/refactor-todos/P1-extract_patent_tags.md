# P1: extract_patent_tags 重构 TODO 文档

## 任务概述

**位置**: `common/tasks.py:212`

**功能**: 专利标签提取任务，在所有爬虫任务完成后触发：
1. 调用 patent_tagging_batch.py 的 process_industry_patents
2. 通过 sql_queries.py 读取专利数据
3. 写入 patent_tech_keyword 表

**当前问题**:
- 读取的专利数据应该来自同步后的主库
- 需要确保在调用前已完成数据同步
- 依赖 process_patent_data 任务完成

## 涉及的数据库表

### test_as (主库)
| 表名 | 操作 | 说明 |
|------|------|------|
| `batch` | READ | 批次信息 |
| `industry_query` | READ | 产业查询信息 |
| `patent_query` | READ | 专利-查询关联 |
| `patent` | READ | 专利信息 |
| `patent_tech_keyword` | WRITE | 专利技术关键词 |

## 当前数据流

```
extract_patent_tags(industry_id)
    ├── process_industry_patents(industry_id)
    │   ├── get_patents_by_industry
    │   │   ├── get_latest_batch_id → [READ: batch]
    │   │   ├── get_filtered_industry_query → [READ: industry_query]
    │   │   ├── get_patent_ids_by_queries → [READ: patent_query]
    │   │   └── batch_query_patents → [READ: patent]
    │   ├── extract_tags_for_patents (规则提取)
    │   └── batch_insert_patent_tech_keywords → [WRITE: patent_tech_keyword]
    └── 触发 generate_industry_report
```

## 目标数据流

```
extract_patent_tags (重构后)
    ├── Step 0: 验证/确保数据已同步
    │   └── 调用 sync_patent_data 或检查同步状态
    ├── process_industry_patents(industry_id)
    └── 触发 generate_industry_report
```

## 详细重构步骤

### 步骤 1: 在 extract_patent_tags 中添加同步验证

**文件**: `common/tasks.py`

**修改位置**: 第 221-223 行之间

```python
def extract_patent_tags(self, industry_id):
    logger.info(f"开始执行专利标签提取任务 - industry_id: {industry_id}")
    
    try:
        # ===== 新增：验证/确保专利数据已同步 =====
        from data_processing.sync_client import check_patent_sync_status
        logger.info(f"检查专利数据同步状态 - industry_id: {industry_id}")
        sync_status = check_patent_sync_status(industry_id)
        if not sync_status.get('synced'):
            # 如果数据未同步，触发同步
            logger.warning(f"专利数据未同步，触发同步 - industry_id: {industry_id}")
            from data_processing.sync_client import sync_patent_data
            sync_result = sync_patent_data(industry_id=industry_id)
            if not sync_result.get('success'):
                raise Exception(f"专利数据同步失败: {sync_result}")
        # ===== 验证结束 =====
        
        from modules.tagging.patent_tagging_batch import process_industry_patents
        ...
```

### 步骤 2: 添加同步状态检查函数

**文件**: `data_processing/sync_client.py`

```python
def check_patent_sync_status(industry_id):
    """检查专利数据是否已同步
    
    Args:
        industry_id: 产业ID
    
    Returns:
        dict: {'synced': bool, 'details': dict}
    """
    from django.db import connection
    
    try:
        with connection.cursor() as cursor:
            # 检查关键表的记录数
            cursor.execute("SELECT COUNT(*) FROM patent")
            patent_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM patent_query")
            patent_query_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM patent_patenter")
            patent_patenter_count = cursor.fetchone()[0]
            
            synced = patent_count > 0 and patent_query_count > 0
            
            return {
                'synced': synced,
                'details': {
                    'patent_count': patent_count,
                    'patent_query_count': patent_query_count,
                    'patent_patenter_count': patent_patenter_count
                }
            }
    except Exception as e:
        logger.error(f"检查专利同步状态失败: {e}")
        return {'synced': False, 'error': str(e)}
```

### 步骤 3: 确保触发顺序正确

**依赖链确认**:
1. `crawl_patent_task` → 触发爬虫
2. `sync_patent_data` → 同步数据 (在 crawl_patent_task 中调用)
3. `process_patent_data` → 处理数据 (依赖同步完成)
4. `extract_patent_tags` → 提取标签 (依赖 process_patent_data 完成)

**验证**: 确保 extract_patent_tags 只在所有爬虫任务完成后才被调用

## 依赖关系

- **前置任务**: process_patent_data (P0)
- **依赖模块**:
  - `data_processing.sync_client.check_patent_sync_status` - 需新增
  - `data_processing.sync_client.sync_patent_data` - 已存在
  - `modules.tagging.patent_tagging_batch.process_industry_patents` - 已存在

## 测试验证方法

### 1. 测试同步状态检查
```python
from data_processing.sync_client import check_patent_sync_status
status = check_patent_sync_status(industry_id=1)
assert 'synced' in status
```

### 2. 测试完整流程
```bash
# 确保依赖任务已完成
celery call common.tasks.extract_patent_tags --args='[1]'
```

### 3. 验证清单
- [ ] 同步状态检查函数正常工作
- [ ] 未同步时自动触发同步
- [ ] 专利数据正确读取
- [ ] 标签正确写入 patent_tech_keyword

## 风险点和注意事项

1. **时序依赖**: extract_patent_tags 必须在 process_patent_data 完成后执行
2. **数据完整性**: 确保 patent_tech_keyword 写入前所有关联数据已就绪
3. **性能**: 大批量专利处理时注意内存使用
4. **幂等性**: 重复执行应能正确处理（不重复插入已有数据）
