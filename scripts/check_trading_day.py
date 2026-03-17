#!/usr/bin/env python3
"""
检查今天是否为A股交易日
- 使用 akshare 获取交易日历
- 缓存到本地避免重复请求
- Exit 0 = 交易日, Exit 1 = 非交易日

Usage: python3 check_trading_day.py [--date YYYY-MM-DD] [--quiet]
"""

import sys
import json
import os
import argparse
from datetime import datetime, date
from pathlib import Path

CACHE_DIR = Path("/root/.openclaw/workspace/data")
CACHE_FILE = CACHE_DIR / "trading_calendar.json"


def fetch_trading_calendar() -> list[str]:
    """从 akshare 获取交易日历"""
    try:
        import akshare as ak
        df = ak.tool_trade_date_hist_sina()
        # 返回日期字符串列表
        return [d.strftime("%Y-%m-%d") for d in df["trade_date"].tolist()]
    except Exception as e:
        print(f"Warning: akshare fetch failed: {e}", file=sys.stderr)
        return []


def load_cached_calendar() -> list[str]:
    """加载本地缓存的日历"""
    if CACHE_FILE.exists():
        try:
            data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            return data.get("trading_days", [])
        except Exception:
            pass
    return []


def save_calendar_cache(trading_days: list[str]):
    """保存日历到本地缓存"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(
        json.dumps({
            "updated": datetime.now().isoformat(),
            "trading_days": trading_days
        }, ensure_ascii=False),
        encoding="utf-8"
    )


def refresh_if_needed():
    """如果缓存过期（>7天）或不存在，刷新"""
    needs_refresh = True
    
    if CACHE_FILE.exists():
        try:
            data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            updated = datetime.fromisoformat(data["updated"])
            # 每周一或缓存超过7天刷新
            if (datetime.now() - updated).days < 7:
                needs_refresh = False
        except Exception:
            pass
    
    if needs_refresh:
        trading_days = fetch_trading_calendar()
        if trading_days:
            save_calendar_cache(trading_days)


def is_trading_day(check_date: str = None) -> bool:
    """检查指定日期是否为交易日"""
    if check_date is None:
        check_date = date.today().strftime("%Y-%m-%d")
    
    # 先尝试缓存
    trading_days = load_cached_calendar()
    
    # 如果缓存为空，尝试刷新
    if not trading_days:
        trading_days = fetch_trading_calendar()
        if trading_days:
            save_calendar_cache(trading_days)
    
    if not trading_days:
        # fallback: 简单判断是否为周末
        d = datetime.strptime(check_date, "%Y-%m-%d")
        return d.weekday() < 5  # 0-4 = 周一到周五
    
    return check_date in trading_days


def get_next_trading_day(check_date: str = None) -> str:
    """获取下一个交易日"""
    if check_date is None:
        check_date = date.today().strftime("%Y-%m-%d")
    
    trading_days = load_cached_calendar()
    if not trading_days:
        trading_days = fetch_trading_calendar()
    
    for td in sorted(trading_days):
        if td > check_date:
            return td
    
    return "unknown"


def main():
    parser = argparse.ArgumentParser(description="检查A股交易日")
    parser.add_argument("--date", default=None, help="检查日期 YYYY-MM-DD (默认今天)")
    parser.add_argument("--quiet", action="store_true", help="静默模式，只返回退出码")
    parser.add_argument("--refresh", action="store_true", help="强制刷新缓存")
    parser.add_argument("--next", action="store_true", help="显示下一个交易日")
    args = parser.parse_args()
    
    if args.refresh:
        trading_days = fetch_trading_calendar()
        if trading_days:
            save_calendar_cache(trading_days)
            if not args.quiet:
                print(f"✅ 已刷新交易日历，共 {len(trading_days)} 个交易日")
        else:
            print("❌ 获取交易日历失败", file=sys.stderr)
            sys.exit(2)
    
    check_date = args.date or date.today().strftime("%Y-%m-%d")
    
    if args.next:
        next_day = get_next_trading_day(check_date)
        print(next_day)
        return
    
    # 确保缓存存在
    refresh_if_needed()
    
    trading = is_trading_day(check_date)
    
    if not args.quiet:
        if trading:
            print(f"📈 {check_date} 是A股交易日")
        else:
            print(f"🏖️ {check_date} 非A股交易日（周末或节假日）")
    
    sys.exit(0 if trading else 1)


if __name__ == "__main__":
    main()
