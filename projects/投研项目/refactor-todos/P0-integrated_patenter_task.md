# P0: integrated_patenter_task 重构 TODO 文档

## 任务概述

**位置**: `common/tasks.py:589`

**功能**: 整合后的专利权人处理任务，在后台执行专利权人转企业的完整流程：
1. 调用 IntegratedPatenterTaskProcessor 处理专利权人
2. 调用 CompanyDataProcessor 更新 company_longlist.query_ids
3. 调用 CompanyTypeProcessor 更新 company_longlist.company_type
4. 调用 CompanyPatenterNameBackfiller 回填专利权人名称
5. 触发企业报告生成任务

**当前问题**:
- **关键问题**: `IntegratedPatenterTaskProcessor` 类已定义（`data_processor.py:535`），但需确认其内部实现是否正确处理双库分离
- 读取 patenter 表（爬虫数据），写入 company、company_longlist（主系统数据）
- 没有确保 patenter 数据来自同步后的主库

## 涉及的数据库表

### test_as (主库)
| 表名 | 操作 | 说明 |
|------|------|------|
| `batch` | READ | 批次信息 |
| `industry_query` | READ | 产业查询信息 |
| `company_longlist` | READ/WRITE | 企业长名单 |
| `company` | READ/WRITE | 企业信息 |
| `data_task` | WRITE | 任务状态记录 |

### test_asc (爬虫库)
| 表名 | 操作 | 说明 |
|------|------|------|
| `patenter` | READ | 爬取的原始专利权人数据 |
| `patent_patenter` | READ | 专利-专利权人关联 |
| `patent_query` | READ | 专利-查询关联 |
| `company` | READ | 爬取的原始企业数据 |

## 当前数据流

```
integrated_patenter_task
    ├── IntegratedPatenterTaskProcessor.run()  ← 类未定义！
    │   └── 读取 patenter, patent_patenter, patent_query
    │   └── 写入 company_longlist
    ├── CompanyDataProcessor.process_company_query_ids()
    │   └── 读取: batch, industry_query, company
    │   └── 写入: company_longlist.query_ids
    ├── CompanyTypeProcessor.process_company_types()
    │   └── 读取: company_longlist, company, patent_patenter, patenter
    │   └── 写入: company_longlist.company_type
    └── CompanyPatenterNameBackfiller.process_backfill()
        └── 读取: company_longlist, company, listed_company_list
        └── 写入: company.patenter_name, company_longlist.patenter_name
```

## 目标数据流

```
integrated_patenter_task
    ├── Step 0: 调用 sync_patenter_data() 同步专利权人数据
    │   └── 新增：创建 sync_patenter_data 或扩展 sync_client
    ├── IntegratedPatenterTaskProcessor.run()
    ├── CompanyDataProcessor.process_company_query_ids()
    ├── CompanyTypeProcessor.process_company_types()
    └── CompanyPatenterNameBackfiller.process_backfill()
```

## 详细重构步骤

### 步骤 1: 创建 IntegratedPatenterTaskProcessor 类

**文件**: `data_processing/data_processor.py`

需要在文件中添加此类定义。基于代码使用模式，推断其功能应包括：

```python
class IntegratedPatenterTaskProcessor:
    def __init__(self, industry_id, top=300, task_id=None, pass_company_num=10):
        self.industry_id = industry_id
        self.top = top
        self.task_id = task_id
        self.pass_company_num = pass_company_num
    
    def run(self):
        """执行专利权人转企业流程"""
        # 1. 从 patent_patenter 获取专利权人
        # 2. 从 patenter 获取专利权人详情
        # 3. 匹配或创建企业记录到 company_longlist
        # 4. 返回处理结果
        pass
```

### 步骤 2: 添加专利权人数据同步函数

**文件**: `data_processing/sync_client.py`

需要添加新的同步函数：

```python
def sync_patenter_data(industry_id=None):
    """同步专利权人相关数据"""
    tables = ['patenter', 'patent_patenter', 'patent_query']
    
    results = {}
    for table in tables:
        result = sync_table_data(table)
        results[table] = result
    
    # 检查是否全部成功
    all_success = all(r.get('success') for r in results.values())
    return {
        'success': all_success,
        'results': results
    }
```

### 步骤 3: 修改 integrated_patenter_task 添加同步调用

**文件**: `common/tasks.py`

**修改位置**: 第 603-617 行之间

```python
@shared_task(queue='ai_scout_crawler', bind=True)
def integrated_patenter_task(self, industry_id, top=300, pass_company_num=10):
    logger.info(f"开始执行整合后的专利权人处理任务 - industry_id: {industry_id}, top: {top}")
    
    try:
        # ===== 新增：同步专利权人数据 =====
        from data_processing.sync_client import sync_patenter_data
        logger.info(f"开始同步专利权人数据 - industry_id: {industry_id}")
        sync_result = sync_patenter_data(industry_id=industry_id)
        if not sync_result.get('success'):
            raise Exception(f"专利权人数据同步失败: {sync_result}")
        logger.info(f"专利权人数据同步完成 - industry_id: {industry_id}, 结果: {sync_result}")
        # ===== 同步结束 =====
        
        from data_processing.data_processor import IntegratedPatenterTaskProcessor
        ...
```

## 依赖关系

- **前置任务**: process_patent_data (P0)
- **依赖模块**:
  - `data_processing.sync_client` - 需要新增 sync_patenter_data
  - `data_processing.data_processor` - 需要新增 IntegratedPatenterTaskProcessor 类
  - `data_processing.company_data_processor` - 已存在

## 测试验证方法

### 1. 测试 IntegratedPatenterTaskProcessor 类
```python
# 验证类可以实例化
from data_processing.data_processor import IntegratedPatenterTaskProcessor
processor = IntegratedPatenterTaskProcessor(industry_id=366, top=300)
assert processor is not None
```

### 2. 测试同步函数
```python
from data_processing.sync_client import sync_patenter_data
result = sync_patenter_data(industry_id=1)
assert result.get('success') == True
```

### 3. 验证清单
- [ ] IntegratedPatenterTaskProcessor 类存在且可实例化
- [ ] 同步函数可正常调用
- [ ] 同步后 patenter 数据可从主库读取
- [ ] 处理结果正确写入 company_longlist

## 风险点和注意事项

1. **类未定义问题**: 当前代码会直接报错，需要先实现 IntegratedPatenterTaskProcessor
2. **数据一致性**: 确保同步完成后才开始处理
3. **性能考虑**: patent_patenter 表可能很大，需要分批处理
4. **公司匹配**: patenter 转 company 需要合理的匹配逻辑
5. **类型映射**: patenter_type 到 company_type 的映射需要准确
