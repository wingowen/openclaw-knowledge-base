# 📊 股票看板系统重构整合方案

**目标**：整合 `watchlist_tracker`（候选票）和 `daily_stock_analysis`（深度分析）两个系统，统一在一个 Web 界面中展示。

---

## 🎯 现状分析

| 维度 | watchlist_tracker（5000端口） | daily_stock_analysis（8000端口） |
|------|-----------------------------|--------------------------------|
| **核心** | 候选票池管理（三仓：观察/确认/进攻） | AI 深度分析单股（8章节报告） |
| **数据** | `watchlist_records`（简表，含状态流转） | `analysis_history`（完整Json报告） |
| **页面** | `/stock/<code>` 显示候选历史轨迹 | `/stock/<code>` 显示分析历史图表 |
| **现状** | ✅ 已聚合页，有趋势图，有同板块关联 | ✅ 独立仪表盘，48条记录 |

**问题**：两个服务独立运行，数据不通，需要切换端口查看完整信息。

---

## 💡 整合策略：方案 C（推荐）

### 核心思想
- **主系统**：保留 `watchlist_dashboard`（Flask，5000端口）作为主入口
- **子系统**：保留 `daily_stock_analysis`（FastAPI，8000端口）作为分析引擎
- **数据层**：在 5000 端口直接读取 `daily_stock_analysis` 的数据库，无需 API 调用
- **展示层**：在候选票聚合页 `/stock/<code>` 中嵌入深度分析卡片

### 架构图

```
用户访问 http://localhost:5000
    ↓
Flask 主应用（watchlist_dashboard）
    ├── 首页：候选票三仓看板（watchlist_records）
    └── 聚合页：/stock/<code>
        ├── 候选票历史（当前已有）
        ├── 技术指标趋势图（当前已有）
        ├── 同板块关联（当前已有）
        └── [新增] 深度分析模块
            ├── 最新 AI 报告摘要
            ├── 分析历史列表（从 analysis_history 读取）
            └── 查看完整报告链接（跳转 8000 或 Modal 弹窗）
```

---

## 🔧 技术实现步骤

### 步骤 1：在 watchlist_dashboard 中读取 analysis_history

**修改 `watchlist_dashboard.py`**：

```python
# 新增：获取股票的分析历史
def get_analysis_history(code: str, limit: int = 5):
    """从 daily_stock_analysis 的数据库读取该股票的分析记录"""
    db_path = Path("/root/.openclaw/workspace/daily_stock_analysis/data/stock_analysis.db")
    if not db_path.exists():
        return []

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT id, code, name, operation_advice, sentiment_score,
               trend_prediction, analysis_summary, created_at
        FROM analysis_history
        WHERE code = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (code, limit))
    records = [dict(r) for r in cur.fetchall()]
    conn.close()
    return records
```

### 步骤 2：修改聚合页路由 `/stock/<code>`

在 `stock_detail` 函数中新增：

```python
# 获取分析历史（深度分析模块）
analysis_records = get_analysis_history(code, limit=5)
```

### 步骤 3：修改聚合页模板（STOCK_DETAIL_TEMPLATE）

在模板末尾新增一个区块：

```html
<!-- 深度分析模块 -->
<section class="analysis-section">
  <h2>📊 AI 深度分析</h2>
  {% if analysis_records %}
    <div class="analysis-list">
      {% for rec in analysis_records %}
        <div class="analysis-card">
          <div class="analysis-header">
            <span class="date">{{ rec.created_at[:10] }}</span>
            <span class="sentiment">情绪分: {{ rec.sentiment_score or 'N/A' }}</span>
            <span class="advice">{{ rec.operation_advice or '分析' }}</span>
          </div>
          <div class="analysis-summary">
            {{ rec.analysis_summary[:200] if rec.analysis_summary else '无摘要' }}{% if rec.analysis_summary|length > 200 %}...{% endif %}
          </div>
          <div class="analysis-actions">
            <a href="http://localhost:8000/stock/{{ code }}" target="_blank" class="btn btn-primary">
              查看完整报告
            </a>
          </div>
        </div>
      {% endfor %}
    </div>
  {% else %}
    <p class="text-muted">暂无深度分析记录。</p>
  {% endif %}
</section>
```

### 步骤 4：样式调整（可选）

在 CSS 部分新增：

```css
.analysis-section {
  margin-top: 30px;
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.analysis-card {
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  margin-bottom: 12px;
  padding: 12px;
}
.analysis-header {
  display: flex;
  gap: 16px;
  margin-bottom: 8px;
  font-size: 13px;
  color: #666;
}
.analysis-header .sentiment {
  font-weight: bold;
  color: #2c3e50;
}
.analysis-actions {
  margin-top: 8px;
}
```

---

## 🎨 最终效果

访问 `http://localhost:5000/stock/600036` 会看到：

1. **候选票历史**（现有）
2. **技术指标趋势图**（现有）
3. **同板块关联**（现有）
4. **新增：AI 深度分析卡片**（最多展示5条最新分析）
 - 每张卡片：日期 + 情绪分 + 操作建议 + 摘要 + 完整报告链接
 - 点击"查看完整报告"在新窗口打开 8000 端口的详细页

---

## 📦 数据同步说明

- **实时查询**：每次访问聚合页时，直接从 8000 端口的数据库读取 `analysis_history`
- **无需同步**：因为 daily_stock_analysis 每天定时写入新记录，数据源天然一致
- **性能影响**：每次查询 8000 的数据库，但分析数据量小（最多几十条），无压力

---

## 🚀 部署步骤

1. ✅ 确保 `daily_stock_analysis` 正在运行（8000端口）
2. ✅ 确保 `watchlist_dashboard` 正在运行（5000端口）
3. 编辑 `scripts/watchlist_dashboard.py`：
   - 添加 `get_analysis_history()` 函数
   - 修改 `stock_detail()` 传入 `analysis_records`
   - 更新 `STOCK_DETAIL_TEMPLATE` 模板
4. 重启 watchlist_dashboard
5. 访问 `http://localhost:5000/stock/600036` 查看效果

---

## ⚖️ 优缺点分析

| 优点 | 缺点 |
|------|------|
| ✅ 代码改动小（仅一个文件） | ⚠️ 仍有两个独立服务（需同时运行） |
| ✅ 用户在一个页面查看所有信息 | ⚠️ 深度分析仍使用独立数据库（无法跨表查询） |
| ✅ 保持系统解耦，降低风险 | ⚠️ 8000端口数据库路径硬编码（未来需配置化） |
| ✅ 未来可独立升级任一部分 |  |
| ✅ 深度分析仍可以在 8000 独立使用 |  |

---

## 🔮 未来可选：完全统一

如果后续想彻底合并为单一应用，可以考虑：

1. 将 `daily_stock_analysis` 作为 Python 包导入，在 Flask 中直接调用分析逻辑
2. 或者将 Flask 应用升级为 FastAPI，合并所有路由
3. 或者共享同一个数据库（统一表结构）

但当前**方案C已满足需求**，无需过度设计。

---

## ✅ 结论

**立即实施**：按步骤修改 `watchlist_dashboard.py`，在聚合页嵌入深度分析卡片。

需要我现在帮你修改代码吗？🎯
