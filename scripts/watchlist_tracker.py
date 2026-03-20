#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""轻量追踪系统：盘前候选记录入库 + 查询

用法：
  python3 scripts/watchlist_tracker.py init
  python3 scripts/watchlist_tracker.py ingest --file reports/preopen_watchlist_20260320.md
  python3 scripts/watchlist_tracker.py list --date 2026-03-20
  python3 scripts/watchlist_tracker.py stats
"""

from __future__ import annotations

import argparse
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List

DB_PATH = Path('/root/.openclaw/workspace/data/watchlist_tracker.db')


def conn_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = conn_db()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS watchlist_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_date TEXT NOT NULL,
            bucket TEXT NOT NULL,
            code TEXT NOT NULL,
            name TEXT,
            sector TEXT,
            chg_pct REAL,
            turnover_pct REAL,
            excess_vs_index REAL,
            vol_ratio5 REAL,
            rsi14 REAL,
            ideal_buy REAL,
            secondary_buy REAL,
            stop_loss REAL,
            target_range TEXT,
            status TEXT DEFAULT '待观察',
            note TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(report_date, bucket, code)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS process_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_date TEXT NOT NULL,
            metric_key TEXT NOT NULL,
            metric_value TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(report_date, metric_key)
        )
        """
    )

    conn.commit()
    conn.close()


def _to_float(s: str):
    try:
        s = s.replace('%', '').strip()
        if not s:
            return None
        return float(s)
    except Exception:
        return None


def _split_target(s: str) -> str:
    return s.strip()


def _extract_report_date(text: str) -> str:
    # 从“生成时间：2026-03-20 12:26”提取日期
    for line in text.splitlines():
        if '生成时间：' in line:
            x = line.split('生成时间：', 1)[1].strip()
            return x.split(' ')[0]
    return datetime.now().strftime('%Y-%m-%d')


def _parse_table_rows(lines: List[str]) -> List[List[str]]:
    rows = []
    for line in lines:
        s = line.strip()
        if not s.startswith('|'):
            continue
        if set(s.replace('|', '').replace('-', '').replace(':', '').strip()) == set():
            continue
        cells = [c.strip() for c in s.strip('|').split('|')]
        rows.append(cells)
    return rows


def _parse_bucket(text: str, section: str) -> List[Dict]:
    lines = text.splitlines()
    collecting = False
    buf = []
    for line in lines:
        if line.startswith('## '):
            if collecting:
                break
            collecting = (section in line)
            continue
        if collecting:
            buf.append(line)

    rows = _parse_table_rows(buf)
    if len(rows) < 2:
        return []

    header = rows[0]
    data_rows = rows[1:]

    results = []
    for r in data_rows:
        if len(r) != len(header):
            continue
        obj = dict(zip(header, r))
        code = obj.get('代码')
        if not code:
            continue

        results.append(
            {
                'code': code,
                'name': obj.get('名称', ''),
                'sector': obj.get('板块', ''),
                'chg_pct': _to_float(obj.get('涨幅', '')),
                'turnover_pct': _to_float(obj.get('换手', '')),
                'excess_vs_index': _to_float(obj.get('超额vs大盘', '')),
                'vol_ratio5': _to_float(obj.get('量比5日', '')),
                'rsi14': _to_float(obj.get('RSI', '')),
                'ideal_buy': _to_float(obj.get('理想买点(MA5)', '')),
                'secondary_buy': _to_float(obj.get('次优买点(MA10)', '')),
                'stop_loss': _to_float(obj.get('止损位', '')),
                'target_range': _split_target(obj.get('目标位区间', '')),
            }
        )
    return results


def _parse_process_metrics(text: str) -> Dict[str, str]:
    lines = text.splitlines()
    collecting = False
    out = {}
    for line in lines:
        if line.startswith('## '):
            if collecting:
                break
            collecting = ('生成过程明细' in line)
            continue
        if collecting:
            s = line.strip()
            if not s:
                continue
            if s[0].isdigit() and '. ' in s:
                k, v = s.split('. ', 1)
                out[f'step_{k}'] = v
    return out


def ingest_report(path: Path):
    text = path.read_text(encoding='utf-8')
    report_date = _extract_report_date(text)

    observe = _parse_bucket(text, '观察仓')
    confirm = _parse_bucket(text, '确认仓')
    attack = _parse_bucket(text, '进攻仓')
    metrics = _parse_process_metrics(text)

    init_db()
    conn = conn_db()
    cur = conn.cursor()

    def upsert(bucket: str, rows: List[Dict]):
        for r in rows:
            cur.execute(
                """
                INSERT INTO watchlist_records
                (report_date,bucket,code,name,sector,chg_pct,turnover_pct,excess_vs_index,vol_ratio5,rsi14,ideal_buy,secondary_buy,stop_loss,target_range)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(report_date,bucket,code) DO UPDATE SET
                    name=excluded.name,
                    sector=excluded.sector,
                    chg_pct=excluded.chg_pct,
                    turnover_pct=excluded.turnover_pct,
                    excess_vs_index=excluded.excess_vs_index,
                    vol_ratio5=excluded.vol_ratio5,
                    rsi14=excluded.rsi14,
                    ideal_buy=excluded.ideal_buy,
                    secondary_buy=excluded.secondary_buy,
                    stop_loss=excluded.stop_loss,
                    target_range=excluded.target_range
                """,
                (
                    report_date,
                    bucket,
                    r['code'],
                    r['name'],
                    r['sector'],
                    r['chg_pct'],
                    r['turnover_pct'],
                    r['excess_vs_index'],
                    r['vol_ratio5'],
                    r['rsi14'],
                    r['ideal_buy'],
                    r['secondary_buy'],
                    r['stop_loss'],
                    r['target_range'],
                ),
            )

    upsert('观察', observe)
    upsert('确认', confirm)
    upsert('进攻', attack)

    for k, v in metrics.items():
        cur.execute(
            """
            INSERT INTO process_metrics (report_date, metric_key, metric_value)
            VALUES (?,?,?)
            ON CONFLICT(report_date, metric_key) DO UPDATE SET metric_value=excluded.metric_value
            """,
            (report_date, k, v),
        )

    conn.commit()
    conn.close()
    print(f"ingested: date={report_date}, 观察={len(observe)}, 确认={len(confirm)}, 进攻={len(attack)}")


def list_records(report_date: str):
    conn = conn_db()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT report_date,bucket,code,name,sector,chg_pct,status,target_range
        FROM watchlist_records
        WHERE report_date=?
        ORDER BY CASE bucket WHEN '进攻' THEN 1 WHEN '确认' THEN 2 ELSE 3 END, chg_pct DESC
        """,
        (report_date,),
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        print('no records')
        return
    for r in rows:
        print(f"[{r['bucket']}] {r['code']} {r['name']} {r['sector']} 涨幅={r['chg_pct']} 状态={r['status']} 目标={r['target_range']}")


def stats():
    conn = conn_db()
    cur = conn.cursor()
    cur.execute("SELECT report_date, bucket, COUNT(*) c FROM watchlist_records GROUP BY report_date,bucket ORDER BY report_date DESC")
    rows = cur.fetchall()
    conn.close()
    for r in rows:
        print(f"{r['report_date']} {r['bucket']} {r['c']}")


def update_status(report_date: str, bucket: str, code: str, status: str, note: str = ''):
    """更新候选票状态"""
    VALID_STATUSES = ['待观察', '已入场', '已止盈', '已止损', '失效']
    if status not in VALID_STATUSES:
        print(f"ERROR: 无效状态 '{status}'，可选: {VALID_STATUSES}")
        return False

    conn = conn_db()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE watchlist_records
        SET status=?, note=?
        WHERE report_date=? AND bucket=? AND code=?
        """,
        (status, note, report_date, bucket, code),
    )
    if cur.rowcount == 0:
        print(f"WARNING: 未找到记录 date={report_date} bucket={bucket} code={code}")
        conn.close()
        return False
    conn.commit()
    conn.close()
    print(f"OK: [{bucket}] {code} -> {status} | note={note or '(无)'}")
    return True


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd', required=True)

    sub.add_parser('init')
    ing = sub.add_parser('ingest')
    ing.add_argument('--file', required=True)

    ls = sub.add_parser('list')
    ls.add_argument('--date', required=True)

    sub.add_parser('stats')

    # update-status 子命令
    up = sub.add_parser('update-status')
    up.add_argument('--date', required=True)
    up.add_argument('--bucket', required=True, choices=['观察', '确认', '进攻'])
    up.add_argument('--code', required=True)
    up.add_argument('--status', required=True, choices=['待观察', '已入场', '已止盈', '已止损', '失效'])
    up.add_argument('--note', default='')

    args = p.parse_args()

    if args.cmd == 'init':
        init_db()
        print(f'initialized: {DB_PATH}')
    elif args.cmd == 'ingest':
        ingest_report(Path(args.file))
    elif args.cmd == 'list':
        list_records(args.date)
    elif args.cmd == 'stats':
        stats()
    elif args.cmd == 'update-status':
        update_status(args.date, args.bucket, args.code, args.status, args.note)


if __name__ == '__main__':
    main()
