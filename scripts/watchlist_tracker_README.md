# 候选票追踪系统使用说明

## 概述

轻量级 A 股候选票追踪系统，基于 SQLite 存储，支持命令行记录更新和 Web 可视化。

## 文件结构

```
scripts/
├── watchlist_tracker.py       # 命令行工具
├── watchlist_dashboard.py     # Web 看板
└── watchlist_tracker_README.md # 本说明文件
data/
└── watchlist_tracker.db       # SQLite 数据库
```

## 命令行工具 `watchlist_tracker.py`

### 初始化数据库

```bash
python3 scripts/watchlist_tracker.py init
```

### 导入候选票报告

```bash
python3 scripts/watchlist_tracker.py ingest --file reports/preopen_watchlist_20260320.md
```

### 查看当日候选票

```bash
python3 scripts/watchlist_tracker.py list --date 2026-03-20
```

### 查看统计

```bash
python3 scripts/watchlist_tracker.py stats
```

### 更新候选票状态（新增）

```bash
# 基本用法
python3 scripts/watchlist_tracker.py update-status \
  --date 2026-03-20 \
  --bucket 进攻 \
  --code 600519 \
  --status 已入场

# 带备注
python3 scripts/watchlist_tracker.py update-status \
  --date 2026-03-20 \
  --bucket 确认 \
  --code 000858 \
  --status 已止盈 \
  --note "涨停板出货"

# 状态可选值
# - 待观察  (默认)
# - 已入场  (已买入)
# - 已止盈  (达到目标价卖出)
# - 已止损  (跌破止损位卖出)
# - 失效    (不再关注)
```

## Web 看板 `watchlist_dashboard.py`

### 启动看板

```bash
python3 scripts/watchlist_dashboard.py
```

访问 http://localhost:5000

### 页面功能

- **首页**：显示当日三仓（进攻/确认/观察）的候选票
- **日期切换**：选择任意日期查看历史记录
- **状态颜色**：
  - 🟢 待观察（绿色）
  - 🔵 已入场（蓝色）
  - 🟠 已止盈（橙色）
  - 🔴 已止损（红色）
  - ⚪ 失效（灰色）

### API 接口

#### 查询记录

```bash
# 按日期查询
curl "http://localhost:5000/records?date=2026-03-20"

# 按状态筛选
curl "http://localhost:5000/records?status=已入场"

# 按代码模糊查询
curl "http://localhost:5000/records?code=600"
```

#### 统计数据

```bash
curl http://localhost:5000/stats
```

返回示例：
```json
{
  "total": 15,
  "settled": 8,
  "hit_rate": "62.5%",
  "profit_rate": "40.0%",
  "loss_rate": "20.0%"
}
```

**统计说明**：
- `total`: 总记录数
- `settled`: 已结算数（止盈+止损+失效）
- `hit_rate`: 命中率 = 止盈数 / 已结算数（样本<3 显示 N/A）
- `profit_rate`: 止盈率 = 止盈数 / 总数（样本<3 显示 N/A）
- `loss_rate`: 止损率 = 止损数 / 总数（样本<3 显示 N/A）

## 典型工作流

1. **盘前** 生成候选票报告并导入
   ```bash
   python3 scripts/watchlist_tracker.py ingest --file reports/preopen_watchlist_20260320.md
   ```

2. **盘中** 启动看板查看
   ```bash
   python3 scripts/watchlist_dashboard.py
   ```

3. **操作后** 更新状态
   ```bash
   # 买入后
   python3 scripts/watchlist_tracker.py update-status --date 2026-03-20 --bucket 进攻 --code 600519 --status 已入场

   # 止盈后
   python3 scripts/watchlist_tracker.py update-status --date 2026-03-20 --bucket 进攻 --code 600519 --status 已止盈 --note "目标价达成"

   # 止损后
   python3 scripts/watchlist_tracker.py update-status --date 2026-03-20 --bucket 进攻 --code 600519 --status 已止损 --note "跌破止损位"
   ```

4. **盘后** 查看统计
   ```bash
   curl http://localhost:5000/stats
   ```

## 数据库结构

### watchlist_records 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| report_date | TEXT | 报告日期 |
| bucket | TEXT | 仓类型（进攻/确认/观察） |
| code | TEXT | 股票代码 |
| name | TEXT | 股票名称 |
| sector | TEXT | 板块 |
| chg_pct | REAL | 涨幅 |
| turnover_pct | REAL | 换手率 |
| excess_vs_index | REAL | 超额vs大盘 |
| vol_ratio5 | REAL | 量比5日 |
| rsi14 | REAL | RSI |
| ideal_buy | REAL | 理想买点 |
| secondary_buy | REAL | 次优买点 |
| stop_loss | REAL | 止损位 |
| target_range | TEXT | 目标位区间 |
| status | TEXT | 状态（默认待观察） |
| note | TEXT | 备注 |
| created_at | TEXT | 创建时间 |

## 依赖

```
Flask>=2.0
```

安装依赖：
```bash
pip install Flask
```
