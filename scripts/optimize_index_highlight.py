#!/usr/bin/env python3
"""优化 #2：候选票主页高亮即将归档的股票"""

from pathlib import Path

file_path = Path("/root/.openclaw/workspace/scripts/watchlist_dashboard.py")
lines = file_path.read_text(encoding="utf-8").splitlines(keepends=True)

# 找到需要修改的位置：在 "# 获取当日数据" 之后
insert_idx = None
for i, line in enumerate(lines):
    if '# 获取当日数据' in line and 'buckets = ["进攻", "确认", "观察"]' in lines[i+1]:
        insert_idx = i + 3  # 在 data = {} 之后插入
        break

if insert_idx is None:
    print("❌ 未找到插入位置")
    exit(1)

# 准备插入的代码块
insert_code = '''
    # 先获取最新日期（用于计算剩余天数）
    cur.execute("SELECT MAX(report_date) as latest FROM watchlist_records")
    latest_row = cur.fetchone()
    latest_date = datetime.strptime(latest_row['latest'], '%Y-%m-%d').date() if latest_row and latest_row['latest'] else datetime.now().date()
    
    # 获取所有活跃股票的最后出现日期（用于计算剩余天数）
    cur.execute("""
        SELECT code, MAX(report_date) as last_date
        FROM watchlist_records
        WHERE status != '失效'
        GROUP BY code
    """)
    last_date_map = {r['code']: r['last_date'] for r in cur.fetchall()}
    
'''

# 找到 data[b] = [dict(r) for r in cur.fetchall()] 这一行，在它之后添加剩余天数计算
# 我们需要在 data[b] = ... 这一行的下一行插入计算逻辑，并且需要包裹在循环内
# 实际上需要修改整段循环

# 重新构建数据获取部分
old_loop_start = insert_idx - 1  # data = {} 那一行
old_loop_end = None
for i in range(insert_idx, len(lines)):
    if 'data[b] = [dict(r) for r in cur.fetchall()]' in lines[i]:
        old_loop_end = i
        break

if old_loop_end is None:
    print("❌ 未找到数据查询结束位置")
    exit(1)

print(f"✅ 找到数据查询段：行 {old_loop_start+1} - {old_loop_end+1}")

# 新的循环体
new_loop = '''    data = {}
    for b in buckets:
        cur.execute(
            """
            SELECT code, name, sector, chg_pct, status, note, target_range, ideal_buy, secondary_buy, stop_loss
            FROM watchlist_records
            WHERE report_date=? AND bucket=?
            ORDER BY chg_pct DESC
            """,
            (date, b),
        )
        rows = [dict(r) for r in cur.fetchall()]
        # 为每条记录计算剩余天数
        for r in rows:
            last_dt = datetime.strptime(last_date_map.get(r['code'], date), '%Y-%m-%d').date()
            gap = (latest_date - last_dt).days
            r['remaining_days'] = max(0, 7 - gap)  # 剩余天数（小于等于2表示即将归档）
        data[b] = rows
'''

# 替换旧代码
new_lines = lines[:old_loop_start] + [new_loop + '\n'] + lines[old_loop_end+1:]

# 现在修改模板 INDEX_TEMPLATE，在表格行中添加高亮样式
# 找到表格行的渲染部分
template_start = None
for i, line in enumerate(new_lines):
    if '<tr>' in line and '{{ r.code }}' in line and '{{ r.name }}' in line:
        template_start = i
        break

if template_start is not None:
    # 找到这一行的结束标签 </tr> 之后的位置，插入 <td> 剩余天数列
    # 先找到该行的结束 </tr> 位置
    # 简单处理：找到下一个 </tr> 的位置，在其前面插入剩余天数列
    # 但需要保持列的顺序。我们先确定表格头是否有剩余数列，如果没有需要添加
    # 我们添加在"状态"列后面
    tr_end = None
    for j in range(template_start, min(template_start+50, len(new_lines))):
        if '</tr>' in new_lines[j]:
            tr_end = j
            break
    
    if tr_end:
        # 插入剩余天数列
        insert_td = '            <td style="color: {% if r.remaining_days <= 2 %}#e74c3c;{% endif %}">{% if r.remaining_days is defined %}{{ r.remaining_days }}{% else %}-{% endif %}</td>\n'
        # 在 "状态" 列之后插入（状态列在 data[b] 字典中有 'status' 字段）
        # 表格头也需要增加一列
        # 先找表头 <thead> 部分
        thead_start = None
        for k in range(max(0, template_start-50), template_start):
            if '<thead>' in new_lines[k]:
                thead_start = k
                break
        if thead_start:
            # 找到表头行的 </tr>
            thead_tr_end = None
            for m in range(thead_start, thead_start+20):
                if '</tr>' in new_lines[m]:
                    thead_tr_end = m
                    break
            if thead_tr_end:
                # 在表头中插入 "剩余" 列，放在"状态"列之后
                # 需要找到"状态"这个<th>
                ths = []
                for n in range(thead_start, thead_tr_end+1):
                    if '<th>' in new_lines[n]:
                        ths.append(n)
                # 找到包含"状态"的<th>位置
                status_th_idx = None
                for idx in ths:
                    if '状态' in new_lines[idx]:
                        status_th_idx = idx
                        break
                if status_th_idx is not None:
                    # 在状态列后插入剩余列表头
                    status_th_line = new_lines[status_th_idx]
                    # 检查是否已经存在剩余列表头，如果不存在则插入
                    if '剩余' not in status_th_line:
                        # 插入新列
                        new_th = '            <th>剩余天数</th>\n'
                        insert_pos = status_th_idx + 1
                        new_lines.insert(insert_pos, new_th)
                        # 同时也要在表格体每行插入对应 <td>
                        # 需要重新定位表格体（因为已插入一行，行号变化）
                        # 简单化：在模板中找到 <td>{{ r.status }}</td> 这一行，插入之后
                        status_td_idx = None
                        for p in range(template_start, template_start+50):
                            if '{{ r.status }}' in new_lines[p]:
                                status_td_idx = p
                                break
                        if status_td_idx is not None:
                            # 找到该行的 </td> 结束标签
                            status_line = new_lines[status_td_idx]
                            # 插入剩余天数 td
                            new_td = '            <td style="color: {% if r.remaining_days <= 2 %}#e74c3c;{% endif %}">{% if r.remaining_days is defined %}{{ r.remaining_days }}{% else %}-{% endif %}</td>\n'
                            new_lines.insert(status_td_idx + 1, new_td)
                            print("✅ 已插入剩余天数列到状态列后")
                        else:
                            print("⚠️ 未找到状态列的td位置")
                    else:
                        print("ℹ️ 剩余列表头已存在，跳过")
                else:
                    print("⚠️ 未找到状态列的表头")
            else:
                print("⚠️ 未找到 thead 的 tr 结束")
        else:
            print("⚠️ 未找到 thead")
    else:
        print("⚠️ 未找到 tr_end")
else:
    print("⚠️ 未找到表格行，跳过模板修改")

file_path.write_text(''.join(new_lines), encoding="utf-8")
print("✅ 优化 #2 完成：聚合页已添加即将归档高亮（剩余天数≤2显示红色）")