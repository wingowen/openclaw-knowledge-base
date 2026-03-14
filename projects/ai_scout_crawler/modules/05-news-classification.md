# 模块分析：news_classification（新闻分类）

> 项目：ai_scout_crawler_refactor
> 路径：`news_classification/`
> 生成时间：2026-03-14

---

## 职责

新闻分类模块。对爬取的企业新闻进行自动分类，基于 jieba 中文分词和预定义词典进行文本分类。

## 文件结构

```
news_classification/
├── core.py                # 分类核心逻辑
├── news_dao.py            # 新闻数据访问层
├── news_sql.py            # SQL 查询
├── config/
│   └── settings.py        # 分类配置
└── models/
    └── news.py            # 新闻数据模型
```

## 核心功能

### 1. 分类引擎（core.py）

**分类方式**：基于词典的关键词匹配

**流程**：
1. 使用 jieba 对新闻标题和内容分词
2. 与分类词典（`classification_lexicon.json`）匹配
3. 根据匹配度确定新闻类别
4. 写入分类结果

### 2. 数据访问（news_dao.py）

| 方法 | 说明 |
|------|------|
| `get_unclassified_news()` | 获取未分类新闻 |
| `save_classification()` | 保存分类结果 |
| `get_news_by_company()` | 按企业获取新闻 |

### 3. SQL 查询（news_sql.py）

新闻相关的数据库操作。

## 触发时机

在 `monitor_company_data_crawl` 任务中，所有企业数据爬取完成后自动触发：

```python
# common/tasks.py
def monitor_company_data_crawl(...):
    # ... 所有企业爬取完成 ...
    
    # 启动新闻分类
    payload = {
        "script_name": "task_classify_news.py",
        "params": {"industry_id": industry_id}
    }
    requests.post(f'{CLAWER_API_URL}/api/local/tasks', json=payload)
```

## 依赖关系

- **上游**：`task_classify_news.py` 脚本调用本模块
- **下游**：MySQL 新闻表
- **被依赖**：声誉评分（`reputation_scorer`）使用分类后的新闻

## 注意事项

- 分类精度依赖词典质量，需定期维护 `classification_lexicon.json`
- jieba 分词对专业术语可能不准确，可添加自定义词典
- 分类结果直接影响声誉评分的准确性
