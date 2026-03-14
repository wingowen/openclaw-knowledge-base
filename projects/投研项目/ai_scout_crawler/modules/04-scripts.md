# 模块分析：scripts（爬虫脚本集）

> 项目：ai_scout_crawler_refactor
> 路径：`scripts/`
> 生成时间：2026-03-14

---

## 职责

爬虫脚本目录。存放所有可执行的数据采集脚本，通过 API 服务调度执行。

## 脚本清单

### 专利爬取

| 脚本 | 说明 | 调用方 |
|------|------|--------|
| `step_one.py` | 专利爬取 v1（已废弃） | - |
| `step_one_v2.py` | 专利爬取 v2（当前） | `ai_scout::crawl_patent_task` |
| `task_crawl_patent.py` | 专利爬取任务封装 | Celery |
| `task_crawl_patent_client.py` | 专利爬取客户端 | `run_patent_crawler_task` |
| `task_crawl_patent_v2.py` | 专利爬取 v2 任务 | Celery |
| `company_patent_full_crawl.py` | 企业专利全文爬取 | `monitor_company_data_crawl` |
| `company_patent_count_crawl.py` | 企业专利数量爬取 | `integrated_patenter_task` 后触发 |
| `patent_crawler_test.py` | 专利爬取测试 | 手动 |

### 天眼查爬虫（11 个维度）

| 脚本 | 维度 | 数据类型 | API 单价 |
|------|------|----------|----------|
| `tyc_business.py` | 经营 | 企业业务 | ¥0.10 |
| `tyc_honor.py` | 经营 | 企业荣誉 | ¥0.50 |
| `tyc_ztb.py` | 经营 | 招投标 | ¥0.20 |
| `tyc_standard.py` | 竞争力 | 企业标准 | ¥1.00 |
| `tyc_certificate.py` | 竞争力 | 资质证书 | ¥0.20 |
| `tyc_investment.py` | 竞争力 | 对外投资 | ¥0.15 |
| `tyc_shareholder.py` | 潜力 | 股东信息 | ¥0.15 |
| `tyc_financing.py` | 潜力 | 融资历史 | ¥0.10 |
| `tyc_member.py` | 潜力 | 主要人员 | ¥0.15 |
| `tyc_member_detail.py` | 潜力 | 人员简介 | ¥0.10 |
| `tyc_news.py` | 声誉 | 新闻舆情 | ¥0.15 |

**维度分组脚本**：
| 脚本 | 包含维度 |
|------|----------|
| `tyc_potential_dimension.py` | 股东 + 融资 + 人员 |
| `tyc_competitive_dimension.py` | 标准 + 证书 + 投资 |
| `tyc_operation_dimension.py` | 荣誉 + 业务 + 招投标 |
| `tyc_reputation_dimension.py` | 新闻 |

### 新闻处理

| 脚本 | 说明 |
|------|------|
| `task_classify_news.py` | 新闻分类任务 |
| `classification_lexicon.json` | 分类词典 |

### 工具脚本

| 脚本 | 说明 |
|------|------|
| `hello_world.py` | 测试脚本 |
| `mysql_multi_db_demo.py` | 多数据库示例 |
| `tyc_directory_label.py` | 目录标签 |

## 脚本标准接口

所有脚本通过 `sys.argv[1]` 接收 JSON 参数：

```python
import sys, json

def main(params):
    # 执行逻辑
    result = do_something(params)
    # 输出 JSON 结果
    print(json.dumps({"success": True, "data": result}, ensure_ascii=False))

if __name__ == '__main__':
    params = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    main(params)
```

## 调用链

```
ai_scout 主系统
    ↓ HTTP POST
api.py::submit_local_task / submit_task
    ↓ subprocess.Popen / Celery.delay
scripts/xxx.py
    ↓
天眼查 API / Selenium / 直接 HTTP
    ↓
结果写入 MySQL
    ↓
JSON 输出到 stdout
```

## 依赖关系

- **上游**：`api.py` 调度执行
- **外部 API**：天眼查开放平台
- **数据源**：专利数据库、企业工商信息
- **输出**：MySQL `test_asc` 数据库

## 注意事项

- 每个脚本独立运行，通过 JSON 参数和输出通信
- 脚本执行超时 1 小时（`TASK_TIMEOUT = 3600`）
- Selenium 脚本需要 Chrome/ChromeDriver（注意版本兼容）
- 天眼查 API 调用受频率限制，脚本内需控制请求间隔
- 错误信息通过 stderr 输出，结果通过 stdout 输出
