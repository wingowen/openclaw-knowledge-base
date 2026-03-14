# 模块分析：company_list（企业长名单）

> 项目：ai_scout_refactor
> 路径：`company_list/`
> 生成时间：2026-03-14

---

## 职责

企业长名单（Longlist）管理。存储从专利分析中提取的原始企业数据，是进入精细化评估前的候选企业池。

## 文件结构

```
company_list/
├── models.py              # 企业列表模型
├── views.py               # 企业列表 API
├── urls.py                # 路由
├── company_list_sql.py    # 原生 SQL 查询
├── admin.py               # Admin 注册
├── apps.py                # App 配置
└── tests.py               # 测试
```

## 在业务流程中的位置

```
专利权人提取 → company_longlist（本模块）→ 筛选 → company_shortlist → 评分/报告
                        ↑
                   原始企业池
```

## 数据来源

企业长名单的数据来自专利权人提取流程：
1. 爬取产业相关专利
2. 从专利中提取专利权人（企业）
3. 专利权人转企业，写入 `company_longlist`

## 关联关系

```
industry
  └── batch
       └── industry_query
            └── task（爬虫任务）
                 └── patent（专利数据）
                      └── patenter（专利权人）
                           └── company_longlist（本模块）
                                └── company_shortlist（短名单）
```

## 依赖关系

- **上游**：`common/tasks.py` → `integrated_patenter_task`（专利权人→企业转换）
- **下游**：`company_shortlist`（筛选后的短名单）
- **数据源**：`patent_crawler` 爬取的专利数据

## 注意事项

- 长名单包含所有从专利中提取的企业，数量可能很大
- 需要通过 `pass_company_num` 参数控制进入短名单的企业数量
- 企业去重依赖专利权人名称匹配，可能存在同一企业多条记录的情况
