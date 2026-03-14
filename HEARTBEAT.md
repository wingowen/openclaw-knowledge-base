# HEARTBEAT.md

# 文档更新提醒任务

- 若存在 `/root/.openclaw/workspace/memory/doc_update_prompt.md`：
  1) 读取内容
  2) 直接把“是否现在同步这些更新到 Notion？”这条提醒发给用户
  3) 发送后删除该文件，避免重复提醒
- 若文件不存在：回复 HEARTBEAT_OK
