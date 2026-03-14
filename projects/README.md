# 📁 项目文档索引

> 维护时间：2026-03-14
> 说明：工作空间中的项目文档备份，定期从源项目同步更新

---

## 项目列表

### 投研项目

| 项目 | 路径 | 文档 | 源路径 |
|------|------|------|--------|
| **AI Scout** (投研主系统) | `投研项目/ai_scout/` | [PROJECT_OVERVIEW.md](./投研项目/ai_scout/PROJECT_OVERVIEW.md) | `/mnt/d/Pycharm/ai_scout_refactor/` |
| **AI Scout Crawler** (爬虫服务) | `投研项目/ai_scout_crawler/` | [PROJECT_OVERVIEW.md](./投研项目/ai_scout_crawler/PROJECT_OVERVIEW.md) | `/mnt/d/Pycharm/ai_scout_crawler_refactor/` |

### 教育项目

| 项目 | 路径 | 文档 | 源路径 |
|------|------|------|--------|
| **sentences-dictation** (英语听写) | `sentences-dictation/` | [PROJECT_OVERVIEW.md](./sentences-dictation/PROJECT_OVERVIEW.md) | `/home/wingo/code/sentences-dictation/` |

---

## 项目关系

```
ai_scout (Django :8700)  ──HTTP──▶  ai_scout_crawler (Flask :5000)
     │                                      │
     ▼                                      ▼
  MySQL (test_as)                       MySQL (test_asc)
  Redis (:6379/1,2)                     Redis (:6379/5,6)
```

- **ai_scout**: Django + DRF + Celery，负责评分、报告生成、用户管理
- **ai_scout_crawler**: Flask + Celery，负责专利爬取、天眼查数据采集、新闻分类

---

## 同步说明

文档从源项目 `docs/PROJECT_OVERVIEW.md` 同步到工作空间。
如需更新，请告知我重新分析源项目并刷新文档。
