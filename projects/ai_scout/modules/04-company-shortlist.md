# 模块分析：company_shortlist（企业短名单）

> 项目：ai_scout_refactor
> 路径：`company_shortlist/`
> 生成时间：2026-03-14

---

## 职责

企业短名单（Shortlist）管理。存储经过筛选进入深度评估的企业，管理企业的多维度爬取状态、评分结果和总分计算。

## 文件结构

```
company_shortlist/
├── models.py                  # 短名单模型
├── views.py                   # 短名单 API
├── urls.py                    # 路由
├── company_shortlist_sql.py   # ⭐ 核心 SQL（评分计算、爬取状态管理）
├── admin.py                   # Admin 注册
├── apps.py                    # App 配置
└── tests.py                   # 测试
```

## 核心功能

### 1. 爬取状态管理

跟踪每个企业的 11 个数据维度爬取状态：

| 字段 | 数据类型 | 对应爬虫脚本 |
|------|----------|-------------|
| `patent_is_crawl` | 0/1/2 | `company_patent_full_crawl.py` |
| `shareholder_is_crawl` | 0/1/2 | `tyc_potential_dimension.py` |
| `financing_is_crawl` | 0/1/2 | `tyc_potential_dimension.py` |
| `member_is_crawl` | 0/1/2 | `tyc_potential_dimension.py` |
| `standard_is_crawl` | 0/1/2 | `tyc_competitive_dimension.py` |
| `certificate_is_crawl` | 0/1/2 | `tyc_competitive_dimension.py` |
| `investment_is_crawl` | 0/1/2 | `tyc_competitive_dimension.py` |
| `honor_is_crawl` | 0/1/2 | `tyc_operation_dimension.py` |
| `business_is_crawl` | 0/1/2 | `tyc_operation_dimension.py` |
| `tender_is_crawl` | 0/1/2 | `tyc_operation_dimension.py` |
| `news_is_crawl` | 0/1/2 | `tyc_reputation_dimension.py` |

状态值：`0`=未爬取, `1`=已爬取, `2`=爬取失败

### 2. 评分存储与计算

| 评分维度 | 说明 |
|----------|------|
| 竞争力评分 | 标准、证书、投资、招投标综合 |
| 经营评分 | 业务、荣誉、招投标综合 |
| 潜力评分 | 股东、融资、人员综合 |
| 声誉评分 | 新闻舆情分析 |
| 技术评分 | 专利质量 + 技术评估 |
| **总分** | 各维度加权汇总 |

### 3. 评估报告存储

- `llm_evaluation`：LLM 生成的企业评估文本
- `core_tech_tags`：核心技术标签

## 核心函数（company_shortlist_sql.py）

| 函数 | 说明 |
|------|------|
| `get_company_crawl_status()` | 获取企业各维度爬取状态 |
| `update_company_crawl_status()` | 更新爬取状态 |
| `calculate_and_update_all_company_total_scores()` | 计算并更新所有企业总分 |

## 在业务流程中的位置

```
company_longlist → 筛选 → company_shortlist（本模块）
                              ↓
                    多维度数据爬取（11个维度）
                              ↓
                    批量评分（5个维度）
                              ↓
                    技术评估 + 总分计算
                              ↓
                    企业报告生成
```

## 依赖关系

- **上游**：`company_list`（长名单筛选）、`integrated_patenter_task`
- **下游**：评分系统、报告生成
- **被依赖**：`monitor_company_data_crawl` 任务轮询本模块的爬取状态

## API 端点

| 接口 | 方法 | 说明 |
|------|------|------|
| `/company_shortlist/` | GET | 短名单列表 |
| `/company_shortlist/<id>/` | GET | 企业详情（含评分） |

## 注意事项

- 总分计算依赖所有维度评分完成后执行
- 爬取状态的轮询间隔默认 10 秒，可通过 `poll_interval` 调整
- `llm_evaluation` 在报告生成开始时更新为"节点评估生成中"
