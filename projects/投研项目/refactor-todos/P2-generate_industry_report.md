# P2: generate_industry_report 重构 TODO 文档

## 任务概述

**位置**: `common/tasks.py:257`

**功能**: 产业报告生成任务，在所有爬虫任务完成后触发：
1. 调用 IndustryReportGenerator 生成产业报告
2. 结果写入 industry 表的 llm_evaluation、llm_tech_tags 字段

**当前问题**:
- 读取的数据已在主库，风险较低
- 需确认数据源正确（来自同步后的主库）
- 主要依赖上游 extract_patent_tags 任务完成

## 涉及的数据库表

### test_as (主库)
| 表名 | 操作 | 说明 |
|------|------|------|
| `industry` | READ/WRITE | 产业信息，写入 llm_evaluation, llm_tech_tags |
| `patent_tech_keyword` | READ | 专利技术关键词 |
| `batch` | READ | 批次信息 |
| `industry_query` | READ | 产业查询信息 |

## 当前数据流

```
generate_industry_report(industry_id)
    ├── convert_industry_data(industry_id)
    │   └── 读取 industry, patent_tech_keyword 等
    ├── IndustryReportGenerator.generate(industry_input)
    │   └── 调用 LLM 生成报告
    └── data_lib.save_industry_report_result()
        └── 写入 industry.llm_evaluation, industry.llm_tech_tags
```

## 目标数据流

```
generate_industry_report (重构后)
    ├── Step 0: 验证上游数据已就绪
    │   └── 检查 extract_patent_tags 是否完成
    ├── convert_industry_data(industry_id)
    ├── IndustryReportGenerator.generate(industry_input)
    └── data_lib.save_industry_report_result()
```

## 详细重构步骤

### 步骤 1: 添加上游任务完成验证

**文件**: `common/tasks.py`

**修改位置**: 第 264-278 行之间

```python
def generate_industry_report(self, industry_id):
    logger.info(f"开始执行产业报告生成任务 - industry_id: {industry_id}")
    
    try:
        # ===== 新增：验证上游数据已就绪 =====
        from data_processing.sql_queries import get_patent_keyword_wordcloud
        try:
            wordcloud_data = get_patent_keyword_wordcloud(industry_id)
            if not wordcloud_data or len(wordcloud_data) == 0:
                raise Exception("专利标签数据未就绪，请先执行 extract_patent_tags 任务")
        except Exception as e:
            logger.error(f"验证上游数据失败 - industry_id: {industry_id}, 错误: {e}")
            raise Exception(f"上游任务未完成: {str(e)}")
        # ===== 验证结束 =====
        
        # 导入所需模块
        ...
```

### 步骤 2: 确认数据读取来自主库

**检查模块**:
- `ai_scout_agent.examples.report_tests.integrated_report.convert_industry_data`
- `ai_scout_agent.core.report.industry.IndustryReportGenerator`

**验证方法**: 确认这些模块使用 Django ORM 或 get_db_connection() 连接主库

## 依赖关系

- **前置任务**: extract_patent_tags (P1)
- **依赖模块**:
  - `ai_scout_agent.examples.report_tests.integrated_report` - 已存在
  - `ai_scout_agent.core.report.industry` - 已存在
  - `data_processing.data_lib` - 已存在

## 测试验证方法

### 1. 验证数据就绪
```python
from data_processing.sql_queries import get_patent_keyword_wordcloud
data = get_patent_keyword_wordcloud(industry_id=1)
assert len(data) > 0
```

### 2. 集成测试
```bash
celery call common.tasks.generate_industry_report --args='[1]'
```

### 3. 验证清单
- [ ] 上游数据验证通过
- [ ] 产业数据正确读取
- [ ] LLM 报告正确生成
- [ ] 结果正确写入 industry 表

## 风险点和注意事项

1. **低风险**: 此任务主要依赖上游任务完成，数据已在主库
2. **LLM 调用**: 需要有效的 LLM API Key
3. **报告质量**: LLM 生成结果可能不稳定，需考虑重试机制
4. **字段更新**: 多次执行会覆盖之前的报告
