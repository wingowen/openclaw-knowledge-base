# P3: orchestrate_company_report_flow 重构 TODO 文档

## 任务概述

**位置**: `common/tasks.py:953`

**功能**: 企业报告流程编排任务，负责协调整个企业评估报告的生成流程：
1. 触发批量评分任务（竞争力、经营、潜力、声誉、技术）
2. 触发专利标签和应用场景提取
3. 触发企业技术评估生成
4. 触发企业报告生成
5. 触发完成检查

**当前问题**:
- **纯编排逻辑**，不直接操作数据库
- 通过 Celery 任务调用链触发其他任务
- 不涉及数据读写，因此**风险最低**
- 无需数据库层面的重构，但需要确认编排的任务都是重构后的版本

**优先级**: P3（最低风险，纯编排逻辑）

## 涉及的数据库表

**无直接数据库操作**。此任务只负责：
- 调用其他 Celery 任务
- 传递参数（industry_id, company_ids 等）

间接受影响的表（通过子任务）：
| 表名 | 操作 | 通过哪个子任务 |
|------|------|----------------|
| `company_longlist` | READ/WRITE | generate_company_reports |
| `company_shortlist` | READ | monitor_company_data_crawl |
| `patent_tech_keyword` | WRITE | extract_patent_tags |
| `industry` | WRITE | generate_industry_report |

## 当前数据流

```
orchestrate_company_report_flow(industry_id)
    ├── 1. batch_company_competitiveness_scoring.delay(industry_id)
    ├── 2. batch_company_operation_scoring.delay(industry_id)
    ├── 3. batch_company_potential_scoring.delay(industry_id)
    ├── 4. batch_company_reputation_scoring.delay(industry_id)
    ├── 5. batch_patent_scoring.delay(industry_id)
    ├── 6. batch_patent_tagging.delay(industry_id)
    ├── 7. batch_company_tech_evaluation.delay(industry_id)
    ├── 8. generate_company_reports.delay(industry_id)
    └── 9. check_all_downstream_tasks.delay(industry_id)
```

## 目标数据流

```
orchestrate_company_report_flow (重构后)
    ├── 不变：纯编排逻辑
    ├── 确认：所有子任务已正确重构
    └── 可选优化：添加任务依赖关系和错误处理
```

## 详细重构步骤

### 步骤 1: 确认所有子任务已重构

在执行编排前，确保以下子任务已完成双库分离重构：

| 子任务 | 状态 | 需要先完成 |
|--------|------|-----------|
| batch_company_competitiveness_scoring | 待确认 | 检查数据源 |
| batch_company_operation_scoring | 待确认 | 检查数据源 |
| batch_company_potential_scoring | 待确认 | 检查数据源 |
| batch_company_reputation_scoring | 待确认 | 检查数据源 |
| batch_patent_scoring | 待确认 | 检查数据源 |
| batch_patent_tagging | 待确认 | 检查数据源 |
| batch_company_tech_evaluation | 待确认 | 检查数据源 |
| generate_company_reports | ✅ P2 已分析 | 需添加上游验证 |
| check_all_downstream_tasks | ✅ P3 已分析 | 低风险 |

### 步骤 2（可选）: 添加任务依赖关系管理

**文件**: `common/tasks.py`

当前编排是简单的顺序/并行调用，可考虑添加依赖检查：

```python
# Before: 直接触发，无依赖检查
batch_company_competitiveness_scoring.delay(industry_id)

# After: 添加前置条件检查
def orchestrate_company_report_flow(self, industry_id):
    # 检查前置任务是否完成
    if not self._check_prerequisite('integrated_patenter_task', industry_id):
        raise Exception("integrated_patenter_task 尚未完成")
    
    if not self._check_prerequisite('monitor_company_data_crawl', industry_id):
        raise Exception("monitor_company_data_crawl 尚未完成")
    
    # 触发评分任务（可并行）
    scoring_tasks = [
        batch_company_competitiveness_scoring,
        batch_company_operation_scoring,
        batch_company_potential_scoring,
        batch_company_reputation_scoring,
        batch_patent_scoring,
    ]
    for task in scoring_tasks:
        task.delay(industry_id)
    
    # 后续任务等待评分完成...
```

### 步骤 3（可选）: 添加错误处理和重试机制

```python
# 添加任务失败回调
from celery import group, chain, chord

# 使用 chord 等待所有评分任务完成后再触发后续
scoring_group = group(
    batch_company_competitiveness_scoring.s(industry_id),
    batch_company_operation_scoring.s(industry_id),
    batch_company_potential_scoring.s(industry_id),
    batch_company_reputation_scoring.s(industry_id),
    batch_patent_scoring.s(industry_id),
)

workflow = chord(scoring_group)(
    batch_patent_tagging.s(industry_id)
)
```

## 依赖关系

- **前置任务**: `integrated_patenter_task`, `monitor_company_data_crawl`
- **触发的子任务**: 9 个批量处理和报告生成任务
- **依赖模块**: `common/tasks.py` 中的所有批量评分任务

## 测试验证方法

### 1. 验证编排逻辑
```python
# 测试编排任务可正常启动
from common.tasks import orchestrate_company_report_flow
result = orchestrate_company_report_flow.delay(industry_id=1)
assert result is not None
```

### 2. 端到端测试
```bash
# 触发完整编排流程
celery call common.tasks.orchestrate_company_report_flow --args='[1]'

# 监控各子任务执行状态
celery -A ai_scout events
```

### 3. 验证清单
- [ ] 所有子任务可正常触发
- [ ] 任务执行顺序正确
- [ ] 参数传递正确
- [ ] 最终状态正确更新

## 风险点和注意事项

1. **最低风险**: 纯编排逻辑，不直接操作数据
2. **子任务状态**: 需要确保所有子任务都已正确重构后才能完成整体重构
3. **执行顺序**: 当前是简单触发，不保证严格的执行顺序
4. **超时问题**: 整个编排流程可能耗时较长，注意 Celery 任务超时设置
5. **幂等性**: 重复执行编排可能导致重复处理，考虑添加去重逻辑

## 重构优先级建议

此任务应该是**最后重构**的，因为：
1. 它依赖所有其他任务的正确实现
2. 纯编排逻辑，没有独立的数据问题
3. 其他任务重构完成后，此任务可能只需微调

**建议流程**：
```
P0 tasks → P1 tasks → P2 tasks → P3 check_all_downstream_tasks → P3 orchestrate_company_report_flow
```
