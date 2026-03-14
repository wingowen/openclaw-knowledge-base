# 模块分析：industrial_definition（产业定义）

> 项目：ai_scout_refactor
> 路径：`industrial_definition/`
> 生成时间：2026-03-14

---

## 职责

产业定义管理。维护产业分类体系，支持多级产业树结构，是整个投研系统的数据入口——所有分析任务都基于选定的产业展开。

## 文件结构

```
industrial_definition/
├── models.py          # 产业模型
├── views.py           # 产业 CRUD API
├── urls.py            # 路由
├── industry_sql.py    # 原生 SQL 查询
├── admin.py           # Admin 注册
└── apps.py            # App 配置
```

## 数据模型

### Industry（产业）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | AutoField | 主键 |
| `level` | Integer | 产业层级（1=一级, 2=二级...） |
| `father_id` | Integer | 父产业 ID（顶级为 NULL） |
| `industry_name` | CharField | 产业名称 |
| `is_enable` | Boolean | 是否启用 |

**树形结构**：通过 `father_id` 自引用形成多级产业树。

## API 端点

| 接口 | 方法 | 说明 |
|------|------|------|
| `/industrial/` | GET | 产业列表（支持筛选） |
| `/industrial/<id>/` | GET | 产业详情 |
| `/industrial/` | POST | 创建产业 |
| `/industrial/<id>/` | PUT | 更新产业 |
| `/industrial/<id>/` | DELETE | 删除/禁用产业 |

## 业务流程位置

```
创建产业 → 定义关键词 → 生成查询 → 爬取专利 → ... → 生成报告
    ↑
  本模块
```

产业是所有分析任务的根节点。一个产业关联：
- 多个搜索查询（`industry_query`）
- 多个批次（`batch`）
- 多个任务（`task`）
- 多个企业（`company_longlist` → `company_shortlist`）

## 依赖关系

- **上游**：用户通过 API 创建/管理产业
- **下游**：`company_list`、`company_shortlist`、所有评分和报告任务
- **被依赖**：`common/tasks.py` 的所有 Celery 任务都以 `industry_id` 为入口参数

## 注意事项

- 产业数据直接影响后续所有分析，创建时需谨慎
- `is_enable=0` 的产业不会出现在活跃列表中
- 建议在创建产业前确认行业分类标准，避免重复
