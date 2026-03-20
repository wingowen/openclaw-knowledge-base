# HEARTBEAT.md

# 文档更新提醒任务

- 若存在 `/root/.openclaw/workspace/memory/doc_update_prompt.md`：
  1) 读取内容
  2) 直接把"是否现在同步这些更新到 Notion？"这条提醒发给用户
  3) 发送后删除该文件，避免重复提醒

# 股票池周审提醒（每周五 18:00-20:00 触发一次）
- 若今天是周五且当前时间在 18:00-20:00 之间：
  - 检查 `memory/heartbeat-state.json` 中 `lastStockPoolReview` 是否为本周
  - 若不是，执行以下操作：
    1) 运行 `python3 /root/.openclaw/workspace/daily_stock_analysis/scripts/generate_daily_report.py` 获取最新数据
    2) 读取 `daily_stock_analysis/STOCK_POOL.md` 当前池子
    3) 基于当日分析，评估是否有需要新增或剔除的标的
    4) 将建议发送给用户
    5) 更新 `lastStockPoolReview` 为本周日期
- 若不符合条件：跳过

# 候选票历史池归档（每个交易日触发一次）
- 检查 `memory/heartbeat-state.json` 中 `lastCandidateArchive` 是否为今日
- 若不是，且当前时间在 09:30-15:00 之间（交易时段）：
  1) 运行 `python3 /root/.openclaw/workspace/scripts/archive_stale_candidates.py --days 7`
  2) 若归档结果 >0，发送通知给用户（列出被归档的股票）
  3) 更新 `lastCandidateArchive` 为今日日期
- 若已执行过：跳过

# 默认
- 若以上均不触发：回复 HEARTBEAT_OK
