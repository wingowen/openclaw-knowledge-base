#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""开盘前候选观察名单（放宽版）生成器
- 数据：新浪行业板块 + 新浪节点个股 + akshare 日线指标
- 输出：Markdown 文件到 /root/.openclaw/workspace/reports/
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime
from pathlib import Path

import akshare as ak
import pandas as pd
import requests

WORKSPACE = Path('/root/.openclaw/workspace')
OUT_DIR = WORKSPACE / 'reports'

H = {'User-Agent': 'Mozilla/5.0'}


def req_get(url: str, params=None, retries: int = 4, timeout: int = 20):
    last = None
    for i in range(retries):
        try:
            r = requests.get(url, params=params, headers=H, timeout=timeout)
            r.raise_for_status()
            return r
        except Exception as e:
            last = e
            time.sleep(1.2 * (i + 1))
    raise last


def ema(s: pd.Series, span: int) -> pd.Series:
    return s.ewm(span=span, adjust=False).mean()


def macd(close: pd.Series):
    dif = ema(close, 12) - ema(close, 26)
    dea = ema(dif, 9)
    return dif, dea


def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    d = close.diff()
    up = d.clip(lower=0)
    down = -d.clip(upper=0)
    rs = up.rolling(n).mean() / (down.rolling(n).mean() + 1e-9)
    return 100 - (100 / (1 + rs))


def fetch_main_sectors():
    text = req_get('https://vip.stock.finance.sina.com.cn/q/view/newSinaHy.php').text
    m = re.search(r'var\s+S_Finance_bankuai_sinaindustry\s*=\s*(\{.*\});?\s*$', text, re.S)
    obj = json.loads(m.group(1))

    sectors = []
    for node, val in obj.items():
        p = val.split(',')
        if len(p) < 13:
            continue
        try:
            sectors.append({'node': node, 'name': p[1], 'chg': float(p[5]), 'count': int(float(p[2]))})
        except Exception:
            continue

    sectors = sorted(sectors, key=lambda x: x['chg'], reverse=True)
    return [s for s in sectors if s['chg'] > 0][:6]


def fetch_index_chg() -> float:
    t = req_get('https://qt.gtimg.cn/q=sh000001', timeout=10).text
    p = t.split('~')
    return float(p[32]) if len(p) > 33 else 0.0


def fetch_sector_stocks(main):
    stats = {
        'sector_count': len(main),
        'raw_members': 0,
        'removed_non_mainboard': 0,
        'removed_st_delist': 0,
        'kept_pre_dedupe': 0,
        'dedup_removed': 0,
        'kept_after_dedupe': 0,
    }

    stocks = []
    for s in main:
        url = 'https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData'
        params = {'page': '1', 'num': '120', 'sort': 'changepercent', 'asc': '0', 'node': s['node'], 'symbol': '', '_s_r_a': 'page'}
        arr = req_get(url, params=params).json()
        if not isinstance(arr, list):
            continue

        stats['raw_members'] += len(arr)
        for x in arr:
            code = str(x.get('code', ''))
            name = str(x.get('name', ''))
            if not (code.startswith('60') or code.startswith('00')):
                stats['removed_non_mainboard'] += 1
                continue
            if 'ST' in name.upper() or '退' in name:
                stats['removed_st_delist'] += 1
                continue
            try:
                stocks.append({
                    'code': code,
                    'name': name,
                    'sector': s['name'],
                    'sector_chg': s['chg'],
                    'chg': float(x.get('changepercent') or 0),
                    'turnover': float(x.get('turnoverratio') or 0),
                    'amount': float(x.get('amount') or 0),
                })
            except Exception:
                # 字段异常也视作剔除
                stats['removed_non_mainboard'] += 1
                continue

    stats['kept_pre_dedupe'] = len(stocks)

    best = {}
    for x in stocks:
        c = x['code']
        if c not in best or (x['sector_chg'], x['chg']) > (best[c]['sector_chg'], best[c]['chg']):
            best[c] = x

    deduped = list(best.values())
    stats['kept_after_dedupe'] = len(deduped)
    stats['dedup_removed'] = stats['kept_pre_dedupe'] - stats['kept_after_dedupe']

    return deduped, stats


def enrich_indicators(stocks, idx_chg):
    stats = {
        'input_after_dedupe': len(stocks),
        'hist_failed': 0,
        'hist_too_short': 0,
        'indicator_ok': 0,
        'fallback_tx_used': 0,
        'fallback_tx_failed': 0,
    }

    rows = []
    for s in stocks:
        code = s['code']

        # 主数据源：EM；失败时回退腾讯历史数据
        hist = None
        try:
            hist = ak.stock_zh_a_hist(
                symbol=code,
                period='daily',
                start_date='20251201',
                end_date=datetime.now().strftime('%Y%m%d'),
                adjust='qfq',
            )
        except Exception:
            hist = None

        if hist is None or len(hist) < 35:
            tx_symbol = f"sh{code}" if code.startswith('6') else f"sz{code}"
            try:
                tx_df = ak.stock_zh_a_hist_tx(
                    symbol=tx_symbol,
                    start_date='20251201',
                    end_date=datetime.now().strftime('%Y%m%d'),
                    adjust='qfq',
                )
                if tx_df is not None and not tx_df.empty:
                    # 对齐字段到 EM 命名
                    col_map = {
                        'date': '日期',
                        'open': '开盘',
                        'close': '收盘',
                        'high': '最高',
                        'low': '最低',
                        'amount': '成交量',  # tx amount 对应成交量
                        'vol': '成交额',
                    }
                    tx_df = tx_df.rename(columns=col_map)
                    # 仅保留需要字段
                    need_cols = ['日期', '开盘', '收盘', '最高', '最低', '成交量', '成交额']
                    for c in need_cols:
                        if c not in tx_df.columns:
                            tx_df[c] = 0
                    hist = tx_df[need_cols].copy()
                    stats['fallback_tx_used'] += 1
                else:
                    stats['fallback_tx_failed'] += 1
            except Exception:
                stats['fallback_tx_failed'] += 1

        if hist is None or len(hist) < 35:
            # 区分失败与长度不足
            if hist is None or len(hist) == 0:
                stats['hist_failed'] += 1
            else:
                stats['hist_too_short'] += 1
            continue

        close = hist['收盘'].astype(float)
        vol = hist['成交量'].astype(float)
        ma5 = close.rolling(5).mean().iloc[-1]
        ma10 = close.rolling(10).mean().iloc[-1]
        ma20 = close.rolling(20).mean().iloc[-1]
        vol5 = vol.rolling(5).mean().iloc[-1]
        last = close.iloc[-1]
        box_high = close.iloc[-11:-1].max()
        high20 = hist['最高'].astype(float).iloc[-20:].max()

        dif, dea = macd(close)
        rr = rsi(close, 14).iloc[-1]

        rows.append({
            **s,
            'current': float(last),
            'ma5': float(ma5),
            'ma10': float(ma10),
            'ma20': float(ma20),
            'high20': float(high20),
            'ma_bull': bool(ma5 > ma10 > ma20 and last > ma5),
            'breakout10': bool(last >= box_high * 0.995),
            'vol_ratio5': float(vol.iloc[-1] / vol5) if vol5 and vol5 > 0 else 0,
            'macd_ok': bool(dif.iloc[-1] > 0 and dif.iloc[-1] > dea.iloc[-1]),
            'rsi14': float(rr) if pd.notna(rr) else 0,
            'excess_vs_index': float(s['chg'] - idx_chg),
            'excess_vs_sector': float(s['chg'] - s['sector_chg']),
        })

    stats['indicator_ok'] = len(rows)
    return pd.DataFrame(rows), stats


def build_report(main, idx_chg, observe, confirm, attack, step_stats):
    dt = datetime.now().strftime('%Y-%m-%d %H:%M')
    lines = []
    lines.append(f"# 开盘前候选观察名单（放宽版）")
    lines.append("")
    lines.append(f"- 生成时间：{dt} (Asia/Shanghai)")
    lines.append(f"- 上证指数当下涨跌幅：{idx_chg:.2f}%")
    lines.append("- 用途：仅供盯盘复核，不作为直接下单建议")
    lines.append("")
    lines.append("## 主线板块（实时）")
    for s in main:
        lines.append(f"- {s['name']}：{s['chg']:.2f}%")

    lines.append("")
    lines.append("## 观察仓（放宽版）")
    if observe.empty:
        lines.append("- 今日暂无观察仓候选，建议空仓观察。")
    else:
        lines.append("| 代码 | 名称 | 板块 | 涨幅 | 换手 | 超额vs大盘 | 量比5日 | RSI | 理想买点(MA5) | 次优买点(MA10) | 止损位 | 目标位区间 |")
        lines.append("|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|")
        for _, r in observe.iterrows():
            ideal_buy = r['ma5']
            secondary_buy = r['ma10']
            stop_loss = min(r['ma20'], r['current'] * 0.96)
            target_1 = max(r['high20'], r['current'] * 1.05)
            target_2 = max(target_1 * 1.03, r['current'] * 1.10)
            lines.append(
                f"| {r['code']} | {r['name']} | {r['sector']} | {r['chg']:.2f}% | {r['turnover']:.2f}% | {r['excess_vs_index']:.2f}% | {r['vol_ratio5']:.2f} | {r['rsi14']:.1f} | {ideal_buy:.2f} | {secondary_buy:.2f} | {stop_loss:.2f} | {target_1:.2f}~{target_2:.2f} |"
            )

    lines.append("")
    lines.append("## 确认仓（1-2只）")
    if confirm.empty:
        lines.append("- 今日暂无确认仓标的（信号未达到确认阈值）。")
    else:
        lines.append("| 代码 | 名称 | 板块 | 涨幅 | 超额vs大盘 | 超额vs板块 | 量比5日 | RSI | 加仓理由 |")
        lines.append("|---|---|---|---:|---:|---:|---:|---:|---|")
        for _, r in confirm.head(2).iterrows():
            reason = "相对强度领先 + 技术面延续 + 流动性达标"
            lines.append(
                f"| {r['code']} | {r['name']} | {r['sector']} | {r['chg']:.2f}% | {r['excess_vs_index']:.2f}% | {r['excess_vs_sector']:.2f}% | {r['vol_ratio5']:.2f} | {r['rsi14']:.1f} | {reason} |"
            )

    lines.append("")
    lines.append("## 进攻仓（0-1只）")
    if attack.empty:
        lines.append("- 今日暂无进攻仓标的（高强度加速条件未满足）。")
    else:
        r = attack.iloc[0]
        lines.append("| 代码 | 名称 | 板块 | 涨幅 | 换手 | 满仓理由 | 风险提示 |")
        lines.append("|---|---|---|---:|---:|---|---|")
        lines.append(
            f"| {r['code']} | {r['name']} | {r['sector']} | {r['chg']:.2f}% | {r['turnover']:.2f}% | 强势加速且流动性匹配 | 波动加剧，严格止损 |"
        )

    lines.append("")
    lines.append("## 开盘复核清单（通过才可进入正式观察仓）")
    lines.append("- 5/10/20日均线仍多头，且价格站上MA5")
    lines.append("- 开盘30-60分钟不出现冲高回落放量转弱")
    lines.append("- 板块联动延续，不是单点脉冲")
    lines.append("- 不追高，分时回踩关键位再评估")

    lines.append("")
    lines.append("## 生成过程明细（数量追踪）")
    lines.append(f"1. 主线板块获取：{step_stats['sector_count']} 个")
    lines.append(
        f"2. 板块成分抓取：原始 {step_stats['raw_members']} 只，"
        f"剔除非主板 {step_stats['removed_non_mainboard']} 只，"
        f"剔除ST/退市 {step_stats['removed_st_delist']} 只，"
        f"保留 {step_stats['kept_pre_dedupe']} 只"
    )
    lines.append(
        f"3. 去重处理：去重后 {step_stats['kept_after_dedupe']} 只，"
        f"去重剔除 {step_stats['dedup_removed']} 只"
    )
    lines.append(
        f"4. 技术指标计算：输入 {step_stats['input_after_dedupe']} 只，"
        f"主源失败 {step_stats['hist_failed']} 只，"
        f"腾讯回退成功 {step_stats['fallback_tx_used']} 只，"
        f"腾讯回退失败 {step_stats['fallback_tx_failed']} 只，"
        f"历史长度不足 {step_stats['hist_too_short']} 只，"
        f"成功计算 {step_stats['indicator_ok']} 只"
    )
    lines.append(
        f"5. 放宽规则筛选：观察仓 {step_stats['final_candidates']} 只，"
        f"确认仓 {step_stats['confirm_count']} 只，"
        f"进攻仓 {step_stats['attack_count']} 只，"
        f"观察仓筛选剔除 {step_stats['filtered_out']} 只"
    )

    lines.append("")
    lines.append("## 生成过程（简版，便于跟踪调整）")
    lines.append("1. 拉取新浪行业板块实时涨幅，选取当下领涨主线板块")
    lines.append("2. 拉取主线板块成分股，限定沪深主板（60/00），剔除ST/退市")
    lines.append("3. 计算技术指标：MA5/10/20、5日量比、RSI、相对大盘超额")
    lines.append("4. 按放宽规则筛出候选观察名单（仅盯盘，不直接下单）")
    lines.append("5. 输出同一份Markdown作为聊天与邮件统一来源，避免口径漂移")

    return '\n'.join(lines)


def main():
    main_sectors = fetch_main_sectors()
    idx_chg = fetch_index_chg()
    stocks, stock_stats = fetch_sector_stocks(main_sectors)
    df, indicator_stats = enrich_indicators(stocks, idx_chg)

    # 三仓分层：观察 / 确认 / 进攻
    if df.empty:
        observe = df
        confirm = df
        attack = df
    else:
        observe = df[
            (df['chg'] >= 2.0)
            & (df['turnover'] >= 2.0)
            & (df['turnover'] <= 15.0)
            & (df['vol_ratio5'] >= 0.9)
            & (df['vol_ratio5'] <= 4.0)
            & (df['excess_vs_index'] >= 1.5)
        ].sort_values(['excess_vs_index', 'chg', 'turnover'], ascending=False).head(10)

        confirm = observe[
            (observe['excess_vs_index'] >= 3.0)
            & (observe['excess_vs_sector'] >= 2.0)
            & (observe['macd_ok'])
            & (observe['rsi14'] >= 55)
            & (observe['rsi14'] <= 85)
            & (observe['vol_ratio5'] >= 1.0)
        ].sort_values(['excess_vs_index', 'chg'], ascending=False).head(2)

        attack = confirm[
            (confirm['chg'] >= 7.0)
            & (confirm['turnover'] >= 5.0)
            & (confirm['turnover'] <= 15.0)
        ].sort_values(['chg', 'turnover'], ascending=False).head(1)

    step_stats = {
        **stock_stats,
        **indicator_stats,
        'final_candidates': int(len(observe)),
        'filtered_out': int(max(indicator_stats['indicator_ok'] - len(observe), 0)),
        'confirm_count': int(len(confirm)),
        'attack_count': int(len(attack)),
    }

    md = build_report(main_sectors, idx_chg, observe, confirm, attack, step_stats)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    d = datetime.now().strftime('%Y%m%d')
    out = OUT_DIR / f'preopen_watchlist_{d}.md'
    out.write_text(md, encoding='utf-8')
    print(str(out))


if __name__ == '__main__':
    main()
