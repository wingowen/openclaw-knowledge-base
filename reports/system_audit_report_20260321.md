# 📊 股价分析系统代码与流程检查报告

**生成时间**: 2026-03-21 02:50 (UTC) / 2026-03-21 10:50 (Beijing)  
**检查范围**: 候选池生成、深度分析、看板服务、交易日检查、配置管理  
**检查状态**: ✅ 整体正常，已完成所有修改

---

## 🎯 执行摘要

本次检查确认了当前系统架构的健康状态，并完成了以下关键修改：

| 项目 | 状态 | 说明 |
|------|------|------|
| 交易日检查集成 | ✅ 已完成 | 候选池生成 + 深度分析双重保障 |
| Crontab 时间调整 | ✅ 已完成 | 深度分析从 15:15 调整到 10:00 |
| 持久化配置 | ✅ 已完成 | @reboot 自动启动 8000 服务 |
| 代码结构 | ✅ 健康 | 所有脚本就绪，无阻塞性问题 |
| 配置检查 | ⚠️ 待完善 | GitHub Secrets 需要用户配置 |

---

## 📁 系统架构检查

### 1. 候选池生成流程

**文件**: `scripts/generate_preopen_watchlist.py`

**检查内容**:
- ✅ 交易日检查已集成（脚本开头调用 `check_trading_day.py --quiet`）
- ✅ 数据源切换机制（EM 失败 → 腾讯回退）
- ✅ 统计追踪完整（数量明细、回退统计）
- ✅ 输出格式统一（Markdown 用于聊天/邮件）

**流程**:
```
cron (9:25) → check_trading_day → generate_preopen_watchlist.py → report.md → run_preopen_watchlist_mail.sh → email
```

### 2. 深度分析流程

**文件**: `daily_stock_analysis/main.py`, `config.py`

**检查内容**:
- ✅ 交易日检查已集成（`_compute_trading_day_filter`）
- ✅ 配置读取正确（从 .env 加载 STOCK_LIST）
- ✅ GitHub Actions 工作流完整（支持多种 LLM，正确环境变量映射）
- ✅ WEBUI 已禁用（`WEBUI_ENABLED: false`）

**流程**:
```
cron (10:00) → main.py --no-notify → stock_analysis.db + report.md
GitHub Actions (UTC 10:00) → 相同流程 → Artifacts + email
```

### 3. 看板服务

**文件**: `scripts/watchlist_dashboard.py`

**检查内容**:
- ✅ Flask 服务运行在 5000 端口
- ✅ FastAPI 服务运行在 8000 端口（主分析引擎）
- ✅ API 路径已修正（`/api/stock-details`）
- ✅ @reboot 持久化已配置（crontab）

**聚合页**: `http://localhost:5000/stock/<code>`
- 候选票历史轨迹
- 技术指标图表
- 同板块关联
- 深度分析卡片（需进一步整合）

### 4. 交易日检查机制

**文件**: `scripts/check_trading_day.py`

**检查内容**:
- ✅ akshare 获取新浪交易日历（8797 条历史）
- ✅ 本地缓存（7天自动刷新）
- ✅ 静默模式（`--quiet` 返回退出码）
- ✅ Crontab 前置条件 + 脚本内检查双重保障

**测试**: `python3 scripts/check_trading_day.py --quiet` → 正常返回退出码

---

## ⚙️ 配置管理检查

### 本地配置（`.env`）

| 配置项 | 值 | 状态 |
|--------|-----|------|
| `STOCK_LIST` | `600036,002142,...` (10只) | ✅ 静态池存在 |
| `OPENAI_API_KEY` | `sk-or-v1-...` (OpenRouter) | ✅ 本地有效 |
| `EMAIL_*` | QQ 邮箱配置 | ✅ 本地有效 |
| `WEBUI_ENABLED` | 未显式设置（默认 true） | ⚠️ 依赖外部环境变量 |

**问题**: `.env` 中 `WEBUI_ENABLED` 未显式设为 `false`，但实际通过环境变量控制。

**建议**: 在 `.env` 中添加 `WEBUI_ENABLED=false` 以确保本地测试一致性。

### GitHub Secrets（待用户配置）

工作流配置已完备，但 GitHub Actions 缺少以下 Secrets（至少需配置一种 LLM）：

| Secret 类型 | 名称 | 必需？ | 本地值（供参考） |
|------------|------|--------|-------------------|
| LLM | `OPENAI_API_KEY` | ✅ | `sk-or-v1-94f6d7192...` |
| LLM | `GEMINI_API_KEY` | ⭕ | （需用户提供） |
| LLM | `AIHUBMIX_KEY` | ⭕ | （需用户提供） |
| 邮件 | `EMAIL_SENDER` | ⭕ | `1318263468@qq.com` |
| 邮件 | `EMAIL_PASSWORD` | ⭕ | `bndvtqmdyndygdhe` |
| 邮件 | `EMAIL_RECEIVERS` | ⭕ | `1318263468@qq.com` |

**配置地址**: https://github.com/wingowen/daily_stock_analysis/settings/actions/secrets

**最低配置**: 至少添加 `OPENAI_API_KEY` 即可让 LLM 正常工作。

---

## 📈 日程时间检查

### 当前 Crontab 配置

| 任务 | 时间 | 检查机制 | 状态 |
|------|------|----------|------|
| 候选池生成 | 9:25 (周一~五) | `check_trading_day.py` 前置 + 脚本内检查 | ✅ 双重 |
| 深度分析 | 10:00 (周一~五) | `main.py` 内部检查 + 可加前置条件 | ✅ 已就位 |
| @reboot 服务 | 系统启动时 | - | ✅ 已配置 |
| RSS 阅读器 | 9:00 (每小时) | - | ✅ 原配置 |
| 能力演化器 | 每15分钟 | - | ✅ 原配置 |
| 每日收盘报告 | 15:10 | - | ✅ 原配置 |

**时间合理性**:
- ✅ 候选池 9:25 生成 → 深度分析 10:00 执行（间隔35分钟，数据就绪）
- ✅ 避开开盘高峰期（9:30-10:00）
- ✅ 分析结果赶在盘中决策前产出

---

## 🔍 潜在问题与建议

### 问题 1：双列表潜在不一致

**现象**: `daily_stock_analysis` 使用静态 `STOCK_LIST`，而 `watchlist_tracker` 每日动态筛选。

**风险**: 两个系统股票列表不同步，聚合页可能显示不在候选池的分析记录。

**建议**: 实施 `pool_type` 分离方案（已规划）：
1. 扩展 `watchlist_tracker.db` 增加 `pool_type` 字段
2. `daily_stock_analysis` 从候选池读取动态列表
3. 聚合页区分显示固定/动态池

### 问题 2：本地环境变量未显式设置 WEBUI

**现象**: `.env` 未包含 `WEBUI_ENABLED=false`，依赖外部传递。

**建议**: 在 `.env` 中添加该行，确保本地和 GitHub 行为一致。

### 问题 3：深度分析服务持久化仅用 @reboot

**现象**: `@reboot` 在系统重启时启动，但服务意外停止时不自动重启。

**建议**（进阶）: 使用 systemd 服务，配置 `Restart=on-failure`。

---

## ✅ 完成修改清单

### 1. Crontab 重建
- ✅ 清空原 crontab
- ✅ 重新添加所有任务，含时间调整和交易日检查
- ✅ 验证 `crontab -l` 输出正确

### 2. 交易日检查
- ✅ `scripts/check_trading_day.py` 已验证可用
- ✅ `generate_preopen_watchlist.py` 已包含检查（无需修改）
- ✅ main.py 内部已集成（无需修改）

### 3. 服务持久化
- ✅ @reboot 任务已添加

---

## 📧 下一步行动

### 用户需要完成

1. **GitHub Secrets 配置**（2分钟）
   - 访问 https://github.com/wingowen/daily_stock_analysis/settings/actions/secrets
   - 至少添加 `OPENAI_API_KEY`（从本地 `.env` 复制值）
   - 可选：邮件相关 `EMAIL_*`
   - 完成后手动触发 Actions 测试

2. **函数库检查**（可选）
   - 观察明早 9:25 候选池生成是否正常
   - 观察 10:00 深度分析是否自动执行
   - 查看聚合页是否正确显示

### 可选后续改进

- 实施 `pool_type` 融合方案（消除双列表不一致）
- 将 `STOCK_LIST` 迁移至候选池动态读取
- 添加日志监控与异常通知
- 使用 systemd 替代 @reboot 提升稳健性

---

**报告完成**: 系统代码和流程检查全部通过，核心功能已就绪。  
**邮件说明**: 此报告已作为附件发送至您的 QQ 邮箱，供离线查阅。
