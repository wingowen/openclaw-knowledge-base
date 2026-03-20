#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自动归档长时间未出现的候选票

规则：
- 连续 N 天未出现在 watchlist_records 的股票
- 从当前活跃池移到历史状态（或独立表）

用法：
  python3 archive_stale_candidates.py --days 7 [--dry-run]
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3

DB_PATH = Path('/root/.openclaw/workspace/data/watchlist_tracker.db')

def conn_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_latest_date():
    """获取最新的候选票日期"""
    conn = conn_db()
    cur = conn.cursor()
    cur.execute("SELECT MAX(report_date) as latest FROM watchlist_records")
    row = cur.fetchone()
    conn.close()
    return row['latest'] if row else None

def get_active_candidates():
    """获取所有活跃候选票（有过记录且未标记为失效）"""
    conn = conn_db()
    cur = conn.cursor()
    # 假设我们有 status 字段，不等于 '失效' 的为活跃
    cur.execute("""
        SELECT DISTINCT code, name, sector, MAX(report_date) as last_date
        FROM watchlist_records
        WHERE status != '失效'
        GROUP BY code, name, sector
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def is_stale(last_date_str: str, days_threshold: int, reference_date: str = None) -> bool:
    """判断是否过期（连续 days_threshold 天未出现）"""
    if not last_date_str:
        return True
    last_date = datetime.strptime(last_date_str, '%Y-%m-%d').date()
    ref_date = datetime.strptime(reference_date, '%Y-%m-%d').date() if reference_date else datetime.now().date()
    gap = (ref_date - last_date).days
    return gap >= days_threshold

def archive_stale(days: int, dry_run: bool = False):
    """归档过期候选票"""
    conn = conn_db()
    cur = conn.cursor()

    # 确保存在归档状态（如果 status 字段不够用，可以新增 '历史' 状态）
    # 这里我们直接更新为 '失效'，或者你可以新增状态值

    active = get_active_candidates()
    latest_date = get_latest_date()
    if not latest_date:
        print("ERROR: 没有找到候选票记录")
        conn.close()
        return

    archived = []
    for cand in active:
        if is_stale(cand['last_date'], days, latest_date):
            archived.append(cand)
            if dry_run:
                print(f"[DRY-RUN] 将归档: {cand['code']} {cand['name']} (最后出现: {cand['last_date']})")
            else:
                # 更新该股票的所有记录为 '失效' 状态（或可只更新最新状态）
                cur.execute("""
                    UPDATE watchlist_records
                    SET status = '失效'
                    WHERE code = ? AND status != '失效'
                """, (cand['code'],))
                print(f"归档: {cand['code']} {cand['name']} (最后出现: {cand['last_date']})")

    conn.commit()
    conn.close()

    print(f"\n总计: 扫描 {len(active)} 只活跃候选票，归档 {len(archived)} 只")
    if dry_run:
        print("（dry-run 模式，未修改数据库）")

def main():
    p = argparse.ArgumentParser(description='归档长时间未出现的候选票')
    p.add_argument('--days', type=int, default=7, help='过期天数阈值（默认7天）')
    p.add_argument('--dry-run', action='store_true', help='仅打印，不修改数据库')
    args = p.parse_args()

    print(f"开始归档检查（阈值: {args.days} 天）...")
    archive_stale(args.days, args.dry_run)

if __name__ == '__main__':
    main()
