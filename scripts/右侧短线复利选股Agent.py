#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
右侧短线复利选股Agent（V1.1）
- 读取 daily_stock_analysis 报告
- 生成 5 段式右侧选股报告（市场判断/观察仓/确认仓/进攻仓/交易计划）
- 支持三档参数预设：aggressive / balanced / conservative

用法:
  python3 scripts/右侧短线复利选股Agent.py --date 20260319 --preset balanced
"""

from __future__ import annotations

import argparse
import math
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


WORKSPACE = Path("/root/.openclaw/workspace")
REPORT_DIR = WORKSPACE / "daily_stock_analysis" / "reports"
OUTPUT_DIR = WORKSPACE / "reports"
DB_PATH = WORKSPACE / "data" / "watchlist_tracker.db"


PRESETS: Dict[str, dict] = {
    "aggressive": {
        "observe_min": 68,
        "confirm_min": 78,
        "attack_min": 86,
        "stop_loss": 0.05,
        "take_profit": (0.07, 0.15),
        "observe_ratio": 0.30,
        "confirm_ratio": 0.40,
        "attack_ratio": 0.30,
    },
    "balanced": {
        "observe_min": 70,
        "confirm_min": 80,
        "attack_min": 88,
        "stop_loss": 0.04,
        "take_profit": (0.05, 0.12),
        "observe_ratio": 0.30,
        "confirm_ratio": 0.40,
        "attack_ratio": 0.30,
    },
    "conservative": {
        "observe_min": 72,
        "confirm_min": 83,
        "attack_min": 90,
        "stop_loss": 0.03,
        "take_profit": (0.05, 0.10),
        "observe_ratio": 0.40,
        "confirm_ratio": 0.35,
        "attack_ratio": 0.25,
    },
}


@dataclass
class StockSnapshot:
    code: str
    name: str
    decision: str
    trend: str
    current: float
    volume_ratio: float
    turnover: float
    trend_strength: int
    ma_bull: bool
    industry_hint: str = ""


def _safe_float(text: str, default: float = 0.0) -> float:
    try:
        return float(text)
    except Exception:
        return default


def parse_dashboard_counts(md: str) -> Tuple[int, int, int]:
    m = re.search(r"买入:(\d+).*?观望:(\d+).*?卖出:(\d+)", md)
    if not m:
        return 0, 0, 0
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def infer_market_mood(md: str) -> Tuple[str, str, str]:
    buy, watch, sell = parse_dashboard_counts(md)
    score = buy * 2 + watch - sell * 2

    if score >= 2 and buy >= sell:
        mood = "强"
        action = "确认/进攻"
    elif score <= -2 or sell > buy:
        mood = "弱"
        action = "观察/空仓"
    else:
        mood = "中"
        action = "观察/确认"

    # 主线板块：从文中常见关键词粗提取（无则回退）
    sectors = []
    for kw in [
        "煤炭",
        "航运",
        "银行",
        "石油",
        "化工",
        "有色",
        "保险",
        "水泥",
        "半导体",
        "AI",
    ]:
        if kw in md:
            sectors.append(kw)
    mainline = (
        "、".join(list(dict.fromkeys(sectors))[:3]) if sectors else "主线分化，防御优先"
    )

    return mood, mainline, action


def parse_stock_sections(md: str) -> List[StockSnapshot]:
    blocks = re.findall(
        r"##\s+[🟢🟡🔴⚪]\s*([^\n]+?)\s*\((\d{6})\)(.*?)(?=\n##\s+[🟢🟡🔴⚪]\s*[^\n]+\(\d{6}\)|\Z)",
        md,
        flags=re.S,
    )
    results: List[StockSnapshot] = []

    for name, code, body in blocks:
        decision_m = re.search(r"\*\*[🟢🟡🔴⚪]\s*([^*]+)\*\*\s*\|\s*([^\n]+)", body)
        decision = decision_m.group(1).strip() if decision_m else "观望"
        trend = decision_m.group(2).strip() if decision_m else "震荡"

        current_m = re.search(r"\|\s*当前价\s*\|\s*([\d.]+)\s*\|", body)
        volume_m = re.search(r"量比\s*([\d.]+)", body)
        turnover_m = re.search(r"换手率\s*([\d.]+)%", body)
        strength_m = re.search(r"趋势强度[:：]\s*(\d{1,3})/100", body)
        ma_bull = bool(
            re.search(r"多头排列[:：]\s*✅", body) or re.search(r"MA5>MA10>MA20", body)
        )

        # 轻量行业提示：从板块字样反推
        industry_hint = ""
        ind_m = re.search(r"\*\*行业\*\*\s*\|\s*([^\n|]+)", body)
        if ind_m:
            industry_hint = ind_m.group(1).strip()

        snap = StockSnapshot(
            code=code,
            name=name.strip(),
            decision=decision,
            trend=trend,
            current=_safe_float(current_m.group(1), 0.0) if current_m else 0.0,
            volume_ratio=_safe_float(volume_m.group(1), 1.0) if volume_m else 1.0,
            turnover=_safe_float(turnover_m.group(1), 0.0) if turnover_m else 0.0,
            trend_strength=int(strength_m.group(1)) if strength_m else 50,
            ma_bull=ma_bull,
            industry_hint=industry_hint,
        )
        results.append(snap)

    return results


def score_stock(s: StockSnapshot, mood: str) -> int:
    """综合评分 0-100"""
    score = s.trend_strength
    if s.ma_bull:
        score += 10
    if s.volume_ratio >= 1.5:
        score += 5
    if mood == "强":
        score += 5
    elif mood == "弱":
        score -= 10
    return max(0, min(100, score))


def to_winrate(score: int) -> str:
    """评分转胜率（简化估算）"""
    if score >= 90:
        return "65-75"
    elif score >= 80:
        return "55-65"
    elif score >= 70:
        return "45-55"
    else:
        return "<45"


def build_lists(stocks: List[StockSnapshot], mood: str, preset: dict):
    ranked = []
    for s in stocks:
        sc = score_stock(s, mood)
        ranked.append((sc, s))
    ranked.sort(key=lambda x: x[0], reverse=True)

    observe = [
        (sc, s) for sc, s in ranked if sc >= preset["observe_min"] and s.ma_bull
    ][:5]
    confirm = [
        (sc, s)
        for sc, s in observe
        if sc >= preset["confirm_min"] and s.volume_ratio >= 1.2
    ][:2]

    attack = []
    if mood == "强":
        attack = [
            (sc, s)
            for sc, s in confirm
            if sc >= preset["attack_min"] and (s.turnover == 0 or 5 <= s.turnover <= 15)
        ][:1]

    return observe, confirm, attack


def fmt_price(v: float) -> str:
    return f"{v:.2f}"


def build_report(
    date_str: str,
    mood: str,
    mainline: str,
    action: str,
    observe,
    confirm,
    attack,
    preset_name: str,
    preset: dict,
) -> str:
    tp_min, tp_max = preset["take_profit"]
    sl = preset["stop_loss"]

    lines: List[str] = []
    lines.append(f"# 右侧短线复利选股日报 - {date_str}")
    lines.append("")
    lines.append(
        f"> 参数预设：`{preset_name}` | 止损：{int(sl * 100)}% | 止盈：{int(tp_min * 100)}%-{int(tp_max * 100)}%"
    )
    lines.append("")

    # 1) 市场判断
    lines.append("## 1. 市场判断")
    lines.append(f"- 市场情绪：{mood}")
    lines.append(f"- 主线板块：{mainline}")
    lines.append(f"- 操作建议：{action}")
    lines.append("- 说明：当前依据为日报中的买/观望/卖出结构与趋势强度综合评分。")
    lines.append("")

    # 2) 观察仓
    lines.append("## 2. 观察仓清单（3-5只）")
    if observe:
        for i, (sc, s) in enumerate(observe[:5], 1):
            stop = s.current * (1 - sl)
            t_low = s.current * (1 + tp_min)
            t_high = s.current * (1 + tp_max)
            reason = f"趋势强度{sc}/100，均线多头，量比{s.volume_ratio:.2f}" + (
                f"，{s.industry_hint}" if s.industry_hint else ""
            )
            lines.append(f"{i}) {s.code} {s.name}")
            lines.append(f"   - 入选理由：{reason}")
            lines.append(f"   - 胜率评估：{to_winrate(sc)}%")
            lines.append(f"   - 止损位：{fmt_price(stop)}")
            lines.append(f"   - 目标价：{fmt_price(t_low)} ~ {fmt_price(t_high)}")
    else:
        lines.append("- 今日无满足条件的观察仓标的，建议空仓等待。")
    lines.append("")

    # 3) 确认仓
    lines.append("## 3. 确认仓清单（1-2只）")
    if confirm:
        for i, (sc, s) in enumerate(confirm[:2], 1):
            alloc = "20%-25%" if i == 1 else "15%-20%"
            lines.append(f"{i}) {s.code} {s.name}")
            lines.append(f"   - 加仓理由：评分{sc}，放量/趋势信号优于观察仓平均")
            lines.append(f"   - 资金分配建议：{alloc}")
            lines.append(
                f"   - 止盈区间：+{int(tp_min * 100)}% ~ +{int(tp_max * 100)}%"
            )
    else:
        lines.append("- 今日无确认仓标的（信号未达到确认阈值）。")
    lines.append("")

    # 4) 进攻仓
    lines.append("## 4. 进攻仓标的（0-1只）")
    if attack:
        sc, s = attack[0]
        lines.append(f"- 标的：{s.code} {s.name}")
        lines.append(f"- 满仓理由：评分{sc}，处于高分段且市场情绪=强")
        lines.append("- 风险提示：高位波动可能放大，严格执行止损，不补仓。")
        lines.append("- 最佳入场时机：分时回踩关键位不破后再上车。")
    else:
        lines.append("- 标的：无")
        lines.append("- 满仓理由：当前不满足进攻仓阈值或市场情绪非强。")
        lines.append("- 风险提示：宁缺毋滥，避免情绪化追高。")
        lines.append("- 最佳入场时机：等待确认仓出现加速信号再评估。")
    lines.append("")

    # 5) 交易计划
    lines.append("## 5. 交易计划")
    lines.append(
        f"- 分仓比例：观察仓{int(preset['observe_ratio'] * 100)}% / 确认仓{int(preset['confirm_ratio'] * 100)}% / 进攻仓{int(preset['attack_ratio'] * 100)}%"
    )
    lines.append("- 入场时机：优先回踩不破关键均线后介入，避免脉冲追高。")
    lines.append("- 持仓周期：3-5天")
    lines.append("- 卖出条件：")
    lines.append(f"  1. 止盈达到 +{int(tp_min * 100)}%~+{int(tp_max * 100)}% 分批止盈")
    lines.append(f"  2. 止损触发 -{int(sl * 100)}% 无条件卖出")
    lines.append("  3. 超过5天趋势转弱则退出")
    lines.append("")

    return "\n".join(lines)


def resolve_input_report(date_str: str) -> Path:
    p = REPORT_DIR / f"report_{date_str}.md"
    if p.exists():
        return p
    candidates = sorted(REPORT_DIR.glob("report_*.md"), reverse=True)
    if not candidates:
        raise FileNotFoundError("未找到 daily_stock_analysis 报告文件")
    return candidates[0]


def ingest_to_db(report_date: str, observe, confirm, attack, preset: dict):
    """将选股结果写入 watchlist_tracker.db"""
    if not DB_PATH.exists():
        print(f"⚠️ 数据库不存在，跳过入库: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    sl = preset["stop_loss"]
    tp_min, tp_max = preset["take_profit"]

    def upsert_stock(bucket: str, score: int, stock):
        stop_loss = round(stock.current * (1 - sl), 2)
        target_low = round(stock.current * (1 + tp_min), 2)
        target_high = round(stock.current * (1 + tp_max), 2)
        target_range = f"{target_low} ~ {target_high}"

        cur.execute(
            """
            INSERT INTO watchlist_records
            (report_date, bucket, code, name, sector, chg_pct, turnover_pct, rsi14,
             ideal_buy, secondary_buy, stop_loss, target_range, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '待观察')
            ON CONFLICT(report_date, bucket, code) DO UPDATE SET
                name=excluded.name,
                sector=excluded.sector,
                chg_pct=excluded.chg_pct,
                turnover_pct=excluded.turnover_pct,
                rsi14=excluded.rsi14,
                ideal_buy=excluded.ideal_buy,
                secondary_buy=excluded.secondary_buy,
                stop_loss=excluded.stop_loss,
                target_range=excluded.target_range
        """,
            (
                report_date,
                bucket,
                stock.code,
                stock.name,
                stock.industry_hint,
                None,
                stock.turnover,
                None,
                stock.current,
                stock.current * 0.98,
                stop_loss,
                target_range,
            ),
        )

    # 写入观察仓
    for sc, s in observe[:5]:
        upsert_stock("观察", sc, s)

    # 写入确认仓
    for sc, s in confirm[:2]:
        upsert_stock("确认", sc, s)

    # 写入进攻仓
    for sc, s in attack[:1]:
        upsert_stock("进攻", sc, s)

    conn.commit()
    conn.close()
    print(
        f"✅ 入库完成: 观察={len(observe[:5])} 确认={len(confirm[:2])} 进攻={len(attack[:1])}"
    )


def main():
    parser = argparse.ArgumentParser(description="右侧短线复利选股Agent")
    parser.add_argument("--date", help="报告日期 YYYYMMDD，默认取最新报告")
    parser.add_argument("--preset", choices=list(PRESETS.keys()), default="balanced")
    args = parser.parse_args()

    if args.date:
        date_str = args.date
    else:
        date_str = datetime.now().strftime("%Y%m%d")

    report_path = resolve_input_report(date_str)
    md = report_path.read_text(encoding="utf-8")

    mood, mainline, action = infer_market_mood(md)
    stocks = parse_stock_sections(md)
    if not stocks:
        raise RuntimeError("未解析到个股分段，请检查输入报告格式")

    preset = PRESETS[args.preset]
    observe, confirm, attack = build_lists(stocks, mood, preset)

    out_date = re.search(r"(\d{8})", report_path.name)
    out_date_str = out_date.group(1) if out_date else date_str

    out_md = build_report(
        date_str=out_date_str,
        mood=mood,
        mainline=mainline,
        action=action,
        observe=observe,
        confirm=confirm,
        attack=attack,
        preset_name=args.preset,
        preset=preset,
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"right_compound_selection_{out_date_str}.md"
    out_path.write_text(out_md, encoding="utf-8")

    print(f"✅ 生成完成: {out_path}")

    # 双写 DB
    ingest_to_db(out_date_str, observe, confirm, attack, preset)


if __name__ == "__main__":
    main()
