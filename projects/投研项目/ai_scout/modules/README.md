# AI Scout 主系统 - 模块分析索引

> 项目路径：`/mnt/d/Pycharm/ai_scout_refactor/`
> 文档路径：`~/.openclaw/workspace/projects/ai_scout/modules/`

---

## 模块列表

| # | 模块 | 路径 | 职责 | 文档 |
|---|------|------|------|------|
| 1 | accounts | `accounts/` | 用户认证 + API 审计日志 | [01-accounts.md](./01-accounts.md) |
| 2 | industrial_definition | `industrial_definition/` | 产业定义管理 | [02-industrial-definition.md](./02-industrial-definition.md) |
| 3 | company_list | `company_list/` | 企业长名单 | [03-company-list.md](./03-company-list.md) |
| 4 | company_shortlist | `company_shortlist/` | 企业短名单 + 评分存储 | [04-company-shortlist.md](./04-company-shortlist.md) |
| 5 | ai_scout_agent | `ai_scout_agent/` | ⭐ AI 核心（LLM 评分/报告/相关性） | [05-ai-scout-agent.md](./05-ai-scout-agent.md) |
| 6 | data_processing | `data_processing/` | 数据处理管道 + 批量评分 | [06-data-processing.md](./06-data-processing.md) |
| 7 | tagging | `modules/tagging/` | 专利标签提取 | [07-tagging.md](./07-tagging.md) |
| 8 | patent_crawler | `patent_crawler/` | 专利爬虫任务管理 | [08-patent-crawler.md](./08-patent-crawler.md) |
| 9 | common | `common/` | ⭐ Celery 任务编排中心 | [09-common-tasks.md](./09-common-tasks.md) |
| 10 | settings | `ai_scout/` | Django 项目配置 | [10-settings-config.md](./10-settings-config.md) |

## 模块依赖图

```
                    ┌─────────────┐
                    │  settings   │ (全局配置)
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
  ┌──────────┐     ┌──────────────┐    ┌──────────┐
  │ accounts │     │    common    │    │  config  │
  │ (认证)   │     │ (任务编排)⭐  │    │ (配置)   │
  └──────────┘     └──────┬───────┘    └──────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
   ┌────────────┐  ┌────────────┐  ┌────────────┐
   │ ai_scout_  │  │  data_     │  │  patent_   │
   │ agent ⭐   │  │ processing │  │  crawler   │
   │ (AI核心)   │  │ (数据处理) │  │ (爬虫管理) │
   └────────────┘  └────────────┘  └────────────┘
          │               │               │
          ▼               ▼               ▼
   ┌────────────┐  ┌────────────┐  ┌────────────────┐
   │  tagging   │  │  company_  │  │ ai_scout_crawler│
   │ (标签提取) │  │  shortlist │  │ (爬虫服务)      │
   └────────────┘  │ (短名单)   │  └────────────────┘
                   └────────────┘
                          ▲
                   ┌────────────┐
                   │ company_   │
                   │ list       │
                   │ (长名单)   │
                   └────────────┘
                          ▲
                   ┌────────────┐
                   │ industrial │
                   │ _definition│
                   │ (产业定义) │
                   └────────────┘
```

## 关键模块说明

### ⭐ common/tasks.py - 任务编排中心
所有异步任务的入口，编排完整的产业分析流程（爬取→处理→评分→报告）。

### ⭐ ai_scout_agent - AI 核心
封装所有 LLM 功能：多维度评分（5维企业+9维专利）、报告生成、相关性计算。

### ⭐ data_processing - 数据处理管道
连接爬虫数据和 AI 评分系统的桥梁，负责数据清洗、批量评分执行。
