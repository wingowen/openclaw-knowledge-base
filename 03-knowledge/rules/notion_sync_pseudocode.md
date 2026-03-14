# Notion 同步执行伪代码（基于 notion_sync_rules.yaml）

```python
# 输入：doc_title, markdown_content, source_path
# 输出：notion_page_url

rules = load_yaml('config/notion_sync_rules.yaml')

# 1) 路由
route = match_route_by_keywords(doc_title, markdown_content, rules.routes)
parent_page_id = route.parent_page_id if route else rules.notion.default_parent_page_id

# 2) 查重（父页面子页标题精确匹配）
children = notion_list_children(parent_page_id)
existing_page = find_child_by_title(children, doc_title)

if existing_page:
    # 3A) 增量更新
    update_heading = f"Update @{now_hhmm()}"
    blocks = md_to_notion_blocks("## " + update_heading + "\n\n" + markdown_content)
    for chunk in chunk_blocks(blocks, max_blocks=rules.sync_policy.write.max_blocks_per_request):
        notion_append_blocks(existing_page.id, chunk)
    target_page_id = existing_page.id
else:
    # 3B) 新建页面
    target_page_id = notion_create_child_page(parent_page_id, doc_title)
    blocks = md_to_notion_blocks(markdown_content)
    for chunk in chunk_blocks(blocks, max_blocks=rules.sync_policy.write.max_blocks_per_request):
        notion_append_blocks(target_page_id, chunk)

# 4) 记录日志
journal = {
  "time": now_iso(),
  "title": doc_title,
  "route": route.name if route else "default",
  "parent_page_id": parent_page_id,
  "target_page_id": target_page_id,
  "source_path": source_path,
}
append_jsonl(rules.logging.journal_file, journal)

# 5) 返回链接
return f"https://www.notion.so/{target_page_id.replace('-', '')}"
```

## 冲突处理补充

- 同标题但语义不同：在标题后添加 `（v2）/（优化版）/（修复版）`
- 高频写入：每次最多 80 blocks，串行写入，避免 429
- 未指定页面：统一回落到 Openclaw 根页面
