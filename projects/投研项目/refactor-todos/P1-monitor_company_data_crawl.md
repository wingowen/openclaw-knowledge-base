# P1: monitor_company_data_crawl 重构 TODO 文档

## 任务概述

**位置**: `common/tasks.py:1045`

**功能**: 监听企业数据爬取状态的轮询任务：
1. 通过 HTTP 调用爬虫服务获取企业数据
2. 轮询检查爬取状态
3. 爬取完成后触发下游任务：
   - 新闻分类任务
   - 批量评分任务（竞争力、经营、潜力、声誉、专利）
   - 专利标签和应用场景提取
   - 企业技术评估生成
   - 总分计算

**当前问题**:
- 爬虫数据写入 test_asc（爬虫库）
- 后续处理直接读取 company_shortlist 表
- 需要改为：爬虫数据先写 test_asc，同步后再做后续处理

## 涉及的数据库表

### test_as (主库)
| 表名 | 操作 | 说明 |
|------|------|------|
| `company_shortlist` | READ | 企业短名单 |
| `company_longlist` | READ/WRITE | 企业长名单 |

### test_asc (爬虫库)
| 表名 | 操作 | 说明 |
|------|------|------|
| `company` | READ/WRITE | 爬取的原始企业数据 |
| `company_shareholder` | READ | 股东信息 |
| `company_patent` | READ | 企业专利 |
| `company_financing` | READ | 融资信息 |
| `company_certificate` | READ | 资质证书 |
| 其他企业相关表 | READ | 各类企业维度数据 |

## 当前数据流

```
monitor_company_data_crawl(company_ids, industry_id)
    ├── HTTP 调用爬虫服务触发爬取
    │   └── POST /api/local/tasks
    ├── while 轮询检查爬取状态
    │   └── get_company_crawl_status() 读取 company_shortlist 表
    ├── 爬取完成
    │   ├── 触发新闻分类: task_classify_news.py
    │   ├── 批量评分任务
    │   │   ├── batch_calculate_company_competitiveness_scores
    │   │   ├── batch_calculate_company_operation_scores
    │   │   ├── batch_calculate_company_potential_scores
    │   │   ├── batch_calculate_company_reputation_scores
    │   │   └── batch_score_patents
    │   ├── 专利标签提取: batch_extract_tags_and_scenarios
    │   ├── 技术评估: batch_generate_company_tech_evaluations
    │   └── 总分计算: calculate_and_update_all_company_total_scores
    │                 batch_calculate_company_tech_scores
```

## 目标数据流

```
monitor_company_data_crawl (重构后)
    ├── HTTP 调用爬虫服务触发爬取
    │   └── 数据写入 test_asc
    ├── while 轮询检查爬取状态
    │   └── get_company_crawl_status() 
    ├── 爬取完成
    │   ├── Step 0: sync_company_data() 同步企业数据
    │   │   └── 新增：创建企业数据同步函数
    │   ├── 触发下游任务 (修改为读取同步后的主库数据)
    │   └── ...
```

## 详细重构步骤

### 步骤 1: 添加企业数据同步函数

**文件**: `data_processing/sync_client.py`

需要添加新的同步函数：

```python
def sync_company_data(industry_id, company_ids=None):
    """同步企业相关数据
    
    Args:
        industry_id: 产业ID
        company_ids: 指定的公司ID列表，None表示同步该产业所有公司
    
    Returns:
        dict: 同步结果
    """
    # 需要同步的表
    tables = [
        'company', 
        'company_shareholder', 
        'company_patent',
        'company_financing',
        'company_certificate',
        'company_standard',
        'company_member',
        'company_investment',
        'company_honor',
        'company_business',
        'company_tender',
        'company_news'
    ]
    
    results = {}
    for table in tables:
        result = sync_table_data(table)
        results[table] = result
    
    all_success = all(r.get('success') for r in results.values())
    return {
        'success': all_success,
        'results': results
    }
```

### 步骤 2: 修改 monitor_company_data_crawl 添加同步调用

**文件**: `common/tasks.py`

**修改位置**: 第 1201 行附近，所有公司数据爬取完成后

```python
# 在 "所有公司数据爬取完成后，启动新闻分类任务" 之前添加：

# ===== 新增：同步企业数据到主库 =====
logger.info(f"所有公司数据爬取完成，开始同步企业数据到主库 - industry_id: {industry_id}")
try:
    from data_processing.sync_client import sync_company_data
    sync_result = sync_company_data(industry_id=industry_id, company_ids=company_ids)
    if not sync_result.get('success'):
        raise Exception(f"企业数据同步失败: {sync_result}")
    logger.info(f"企业数据同步完成 - industry_id: {industry_id}, 结果: {sync_result}")
except Exception as e:
    logger.error(f"企业数据同步失败 - industry_id: {industry_id}, 错误: {e}")
    # 决定是否继续执行，或者终止任务
    raise
# ===== 同步结束 =====

# 然后继续原有逻辑：启动新闻分类任务
logger.info(f"企业数据同步完成，开始启动新闻分类任务")
...
```

### 步骤 3: 确保下游任务从主库读取

**修改范围**: 以下任务需要确保从主库读取数据

1. `batch_calculate_company_competitiveness_scores`
2. `batch_calculate_company_operation_scores`
3. `batch_calculate_company_potential_scores`
4. `batch_calculate_company_reputation_scores`
5. `batch_score_patents`
6. `batch_extract_tags_and_scenarios`
7. `batch_generate_company_tech_evaluations`
8. `calculate_and_update_all_company_total_scores`
9. `batch_calculate_company_tech_scores`

**检查方法**: 确认这些模块使用 `get_db_connection()` 连接主库

## 依赖关系

- **前置任务**: 
  - integrated_patenter_task (P0)
  - process_patent_data (P0)
- **依赖模块**:
  - `data_processing.sync_client` - 需要新增 sync_company_data
  - `company_shortlist.company_shortlist_sql` - 现有查询函数
  - 各评分模块 - 需确保从主库读取

## 测试验证方法

### 1. 测试同步函数
```python
from data_processing.sync_client import sync_company_data
result = sync_company_data(industry_id=1, company_ids=[1,2,3])
assert result.get('success') == True
```

### 2. 集成测试
```bash
# 触发任务
celery call common.tasks.monitor_company_data_crawl --args='[[1,2,3], 1]'
```

### 3. 验证清单
- [ ] 爬取完成后同步执行
- [ ] 同步后数据可从主库读取
- [ ] 下游任务正确读取同步后数据
- [ ] 评分结果正确写入主库

## 风险点和注意事项

1. **数据量**: 企业数据表可能很大，需要考虑增量同步
2. **同步顺序**: 部分表有外键依赖，需要按正确顺序同步
3. **字段映射**: 爬虫库和主库字段名可能不同，需要映射
4. **状态一致性**: company_shortlist 和 company_longlist 需要同步更新
5. **失败处理**: 同步失败时需要决定是否继续下游任务
