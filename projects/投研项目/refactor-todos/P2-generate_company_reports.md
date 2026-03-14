# P2: generate_company_reports 重构 TODO 文档

## 任务概述

**位置**: `common/tasks.py:433`

**功能**: 生成指定产业下的企业报告：
1. 获取企业列表
2. 调用 CompanyReportGenerator 为每个企业生成报告
3. 结果写入 company_longlist 表

**当前问题**:
- 读取的数据已在主库，风险较低
- 需确认数据源正确（来自同步后的主库）
- 主要依赖上游 integrated_patenter_task 和 monitor_company_data_crawl 任务完成

## 涉及的数据库表

### test_as (主库)
| 表名 | 操作 | 说明 |
|------|------|------|
| `company_longlist` | READ/WRITE | 企业长名单，写入报告内容 |
| `company` | READ | 企业信息 |
| `industry` | READ | 产业信息 |

## 当前数据流

```
generate_company_reports(industry_id, limit=300)
    ├── data_lib.get_company_list_for_reports(industry_id, limit)
    │   └── 读取 company_longlist
    ├── CompanyReportGenerator.generate(company_input)
    │   └── 调用 LLM 生成企业报告
    └── 保存报告到 company_longlist
```

## 目标数据流

```
generate_company_reports (重构后)
    ├── Step 0: 验证上游数据已就绪
    │   └── 检查 integrated_patenter_task 和 monitor_company_data_crawl 是否完成
    ├── data_lib.get_company_list_for_reports()
    ├── CompanyReportGenerator.generate()
    └── 保存报告到 company_longlist
```

## 详细重构步骤

### 步骤 1: 添加上游任务完成验证

**文件**: `common/tasks.py`

**修改位置**: 第 458-470 行之间

```python
def generate_company_reports(self, industry_id, limit=300):
    logger.info(f"开始执行企业报告生成任务 - industry_id: {industry_id}, limit: {limit}")
    
    try:
        # ===== 新增：验证上游数据已就绪 =====
        from django.db import connection
        with connection.cursor() as cursor:
            # 检查企业数据是否已生成
            cursor.execute(
                "SELECT COUNT(*) FROM company_longlist WHERE industry_id = %s AND is_pass = 1",
                (industry_id,)
            )
            company_count = cursor.fetchone()[0]
            
            if company_count == 0:
                raise Exception("企业数据未就绪，请先执行 integrated_patenter_task 任务")
            
            logger.info(f"企业数据已就绪，共 {company_count} 家企业 - industry_id: {industry_id}")
        # ===== 验证结束 =====
        
        # 更新任务状态为开始
        ...
```

### 步骤 2: 确认数据读取来自主库

**检查模块**:
- `data_processing.data_lib.DataLib.get_company_list_for_reports`
- `ai_scout_agent.core.report.company.CompanyReportGenerator`

**验证方法**: 确认这些模块使用 Django ORM 或 get_db_connection() 连接主库

## 依赖关系

- **前置任务**: 
  - integrated_patenter_task (P0)
  - monitor_company_data_crawl (P1)
- **依赖模块**:
  - `data_processing.data_lib` - 已存在
  - `ai_scout_agent.core.report.company` - 已存在

## 测试验证方法

### 1. 验证数据就绪
```python
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute(
        "SELECT COUNT(*) FROM company_longlist WHERE industry_id = %s AND is_pass = 1",
        (1,)
    )
    count = cursor.fetchone()[0]
    assert count > 0
```

### 2. 集成测试
```bash
celery call common.tasks.generate_company_reports --args='[1, 300]'
```

### 3. 验证清单
- [ ] 上游数据验证通过
- [ ] 企业列表正确读取
- [ ] LLM 报告正确生成
- [ ] 结果正确写入 company_longlist

## 风险点和注意事项

1. **低风险**: 此任务主要依赖上游任务完成，数据已在主库
2. **LLM 调用**: 需要有效的 LLM API Key，每个企业都需要调用
3. **性能**: 大量企业报告生成耗时长，需考虑异步处理
4. **字段更新**: 多次执行会覆盖之前的报告
5. **错误恢复**: 单个企业失败不应影响整体流程
