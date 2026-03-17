#!/usr/bin/env python3
"""
A股每日复盘报告生成器
- 从腾讯财经获取实时指数数据
- 获取关键个股数据
- 生成 Markdown 格式报告
- 写入 Obsidian vault
- Git push 到 GitHub

Usage: python3 generate_daily_report.py [--date YYYY-MM-DD]
"""

import json
import re
import subprocess
import sys
import os
import argparse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

# === 配置 ===
OBSIDIAN_VAULT = "/root/.openclaw/workspace/obsidian"
REPORTS_DIR = f"{OBSIDIAN_VAULT}/04-Reviews"
FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK_URL", "")
QQ_MAIL_USER = os.environ.get("QQ_MAIL_USER", "")
QQ_MAIL_AUTH_CODE = os.environ.get("QQ_MAIL_AUTH_CODE", "")
QQ_MAIL_TO = os.environ.get("QQ_MAIL_TO", "")

# 指数代码 (腾讯财经)
INDICES = {
    "sh000001": "上证指数",
    "sz399001": "深证成指",
    "sz399006": "创业板指",
    "sh000688": "科创50",
}

# 关键个股
KEY_STOCKS = {
    "sh600519": "贵州茅台",
    "sh601318": "中国平安",
    "sz000858": "五粮液",
    "sz300750": "宁德时代",
    "sh688981": "中芯国际",
    "sh600036": "招商银行",
    "sz300059": "东方财富",
    "sh601012": "隆基绿能",
    "sz002594": "比亚迪",
    "sh601899": "紫金矿业",
}


def fetch_tencent_data(codes: list[str]) -> dict:
    """从腾讯财经获取实时行情数据"""
    import urllib.request
    
    codes_str = ",".join(codes)
    url = f"https://qt.gtimg.cn/q={codes_str}"
    
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0",
        "Accept": "*/*",
    })
    
    with urllib.request.urlopen(req, timeout=10) as resp:
        raw = resp.read().decode("gbk")
    
    results = {}
    for line in raw.strip().split(";"):
        line = line.strip()
        if not line:
            continue
        m = re.search(r'v_(\w+)="(.*)"', line)
        if not m:
            continue
        code = m.group(1)
        parts = m.group(2).split("~")
        if len(parts) < 50:
            continue
        
        results[code] = {
            "name": parts[1],
            "code": parts[2],
            "current": float(parts[3]) if parts[3] else 0,
            "prev_close": float(parts[4]) if parts[4] else 0,
            "open": float(parts[5]) if parts[5] else 0,
            "volume": int(parts[6]) if parts[6] else 0,  # 成交量(手)
            "high": float(parts[33]) if len(parts) > 33 and parts[33] else 0,
            "low": float(parts[34]) if len(parts) > 34 and parts[34] else 0,
            "change_amt": float(parts[31]) if len(parts) > 31 and parts[31] else 0,
            "change_pct": float(parts[32]) if len(parts) > 32 and parts[32] else 0,
            "amount_wan": float(parts[37]) if len(parts) > 37 and parts[37] else 0,  # 成交额(万)
            "time": parts[30] if len(parts) > 30 else "",
        }
    
    return results


def parse_prev_report(date_str: str) -> dict:
    """解析前一份报告的预测，用于复盘"""
    # 读取 reports 目录中最近的报告
    reports_dir = Path(REPORTS_DIR)
    if not reports_dir.exists():
        return {}
    
    # 找到最近的报告文件
    md_files = sorted(reports_dir.glob("*.md"), reverse=True)
    for f in md_files:
        if date_str not in f.name:
            content = f.read_text(encoding="utf-8")
            # 提取预判区间
            predictions = {}
            # 简单解析
            sh_match = re.search(r'\*\*上证\*\*.*?(\d{4})~(\d{4})', content)
            if sh_match:
                predictions["上证"] = {"low": int(sh_match.group(1)), "high": int(sh_match.group(2))}
            cy_match = re.search(r'\*\*创业板\*\*.*?(\d{4})~(\d{4})', content)
            if cy_match:
                predictions["创业板"] = {"low": int(cy_match.group(1)), "high": int(cy_match.group(2))}
            return predictions
    return {}


def generate_report(indices: dict, stocks: dict, date_str: str, prev_predictions: dict) -> str:
    """生成 Markdown 报告"""
    
    # 计算成交额
    total_amount = sum(s.get("amount_wan", 0) for s in stocks.values()) / 10000  # 亿
    
    # 上证成交额 (从指数数据估算)
    sh_amount_yi = indices.get("sh000001", {}).get("amount_wan", 0) / 10000
    sz_amount_yi = indices.get("sz399001", {}).get("amount_wan", 0) / 10000
    total_market_amount = sh_amount_yi + sz_amount_yi
    
    # 预测复盘
    review_section = ""
    sh_idx = indices.get("sh000001", {})
    cy_idx = indices.get("sz399001", {})
    gem_idx = indices.get("sz399006", {})
    
    if prev_predictions:
        review_lines = []
        for name, pred in prev_predictions.items():
            if name == "上证":
                actual = sh_idx.get("current", 0)
                if pred["low"] <= actual <= pred["high"]:
                    review_lines.append(f"| 上证指数 | {pred['low']}~{pred['high']} | {actual:.2f} | ✅ 在区间内 |")
                else:
                    review_lines.append(f"| 上证指数 | {pred['low']}~{pred['high']} | {actual:.2f} | ❌ 超出区间 |")
            elif name == "创业板":
                actual = gem_idx.get("current", 0)
                if pred["low"] <= actual <= pred["high"]:
                    review_lines.append(f"| 创业板指 | {pred['low']}~{pred['high']} | {actual:.2f} | ✅ 在区间内 |")
                else:
                    review_lines.append(f"| 创业板指 | {pred['low']}~{pred['high']} | {actual:.2f} | ⚠️ 超出区间 |")
        
        if review_lines:
            review_section = f"""## 0) 昨日预测复盘

| 预判项 | 预判区间 | 实际结果 | 评价 |
|--------|----------|----------|------|
{chr(10).join(review_lines)}

"""

    # 下一个交易日
    next_day = (datetime.strptime(date_str, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    
    # 预判区间 (基于今日波动)
    sh_current = sh_idx.get("current", 4000)
    sh_high = sh_idx.get("high", sh_current)
    sh_low = sh_idx.get("low", sh_current)
    sh_range = sh_high - sh_low
    sh_pred_low = max(int(sh_low - sh_range * 0.3), int(sh_current - 30))
    sh_pred_high = min(int(sh_high + sh_range * 0.3), int(sh_current + 30))
    
    gem_current = gem_idx.get("current", 3300)
    gem_high = gem_idx.get("high", gem_current)
    gem_low = gem_idx.get("low", gem_current)
    gem_range = gem_high - gem_low
    gem_pred_low = max(int(gem_low - gem_range * 0.3), int(gem_current - 25))
    gem_pred_high = min(int(gem_high + gem_range * 0.3), int(gem_current + 25))

    # 分类涨跌股
    gainers = [(s["name"], s["change_pct"], s["amount_wan"]/10000) for s in stocks.values() if s["change_pct"] > 0]
    losers = [(s["name"], s["change_pct"], s["amount_wan"]/10000) for s in stocks.values() if s["change_pct"] < 0]
    gainers.sort(key=lambda x: -x[1])
    losers.sort(key=lambda x: x[1])
    
    # 市场结构判断
    if len(gainers) > len(losers):
        structure = "**市场整体偏强**，上涨个股占优"
    elif len(gainers) < len(losers):
        structure = "**市场整体偏弱**，下跌个股占优"
    else:
        structure = "**市场分化**，涨跌参半"
    
    # 风格判断
    growth_stocks = ["比亚迪", "宁德时代", "中芯国际", "东方财富"]
    value_stocks = ["贵州茅台", "五粮液", "中国平安", "招商银行"]
    cycle_stocks = ["紫金矿业", "隆基绿能"]
    
    growth_avg = sum(s.get("change_pct", 0) for s in stocks.values() if s["name"] in growth_stocks) / max(len(growth_stocks), 1)
    value_avg = sum(s.get("change_pct", 0) for s in stocks.values() if s["name"] in value_stocks) / max(len(value_stocks), 1)
    cycle_avg = sum(s.get("change_pct", 0) for s in stocks.values() if s["name"] in cycle_stocks) / max(len(cycle_stocks), 1)
    
    if growth_avg > value_avg:
        style = "成长>价值"
    else:
        style = "价值>成长"
    
    # 生成报告
    report = f"""# {date_str} A股深度复盘与{next_day[:5]}预判

> 数据来源：腾讯财经实时API | 报告时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}

{review_section}## 1) 今日核心行情总览（{date_str} 收盘）

### 指数表现

| 指数 | 收盘 | 涨跌幅 | 振幅 | 最高 | 最低 |
|------|------|--------|------|------|------|
| **上证指数** | {sh_idx.get('current', 0):.2f} | **{sh_idx.get('change_pct', 0):+.2f}%** | {((sh_idx.get('high',0)-sh_idx.get('low',0))/sh_idx.get('prev_close',1)*100):.2f}% | {sh_idx.get('high',0):.2f} | {sh_idx.get('low',0):.2f} |
| **深证成指** | {cy_idx.get('current', 0):.2f} | **{cy_idx.get('change_pct', 0):+.2f}%** | {((cy_idx.get('high',0)-cy_idx.get('low',0))/cy_idx.get('prev_close',1)*100):.2f}% | {cy_idx.get('high',0):.2f} | {cy_idx.get('low',0):.2f} |
| **创业板指** | {gem_idx.get('current', 0):.2f} | **{gem_idx.get('change_pct', 0):+.2f}%** | {((gem_idx.get('high',0)-gem_idx.get('low',0))/gem_idx.get('prev_close',1)*100):.2f}% | {gem_idx.get('high',0):.2f} | {gem_idx.get('low',0):.2f} |
| **科创50** | {indices.get('sh000688', {}).get('current', 0):.2f} | **{indices.get('sh000688', {}).get('change_pct', 0):+.2f}%** | {((indices.get('sh000688',{}).get('high',0)-indices.get('sh000688',{}).get('low',0))/max(indices.get('sh000688',{}).get('prev_close',1),1)*100):.2f}% | {indices.get('sh000688', {}).get('high', 0):.2f} | {indices.get('sh000688', {}).get('low', 0):.2f} |

### 成交数据

- **两市成交额**：约 **{total_market_amount/10000:.2f} 万亿**（沪 {sh_amount_yi/10000:.2f} 万亿 + 深 {sz_amount_yi/10000:.2f} 万亿）
- **量能定位**：{'高成交维持，资金活跃' if total_market_amount > 20000 else '量能适中' if total_market_amount > 15000 else '成交偏淡'}

---

## 2) 关键个股表现

### 今日涨跌

| 股票 | 收盘 | 涨跌幅 | 成交额 |
|------|------|--------|--------|
{chr(10).join(f'| **{s["name"]}** | {s["current"]:.2f} | **{s["change_pct"]:+.2f}%** | {s["amount_wan"]/10000:.1f}亿 |' for s in sorted(stocks.values(), key=lambda x: -x["change_pct"]))}

### 结构判断

{structure}，风格偏向 **{style}**。

---

## 3) {next_day[:5]}（下个交易日）预判

### 指数预判

| 指数 | 区间预判 | 情景分析 |
|------|----------|----------|
| **上证** | **{sh_pred_low}~{sh_pred_high}** | 收回 {int(sh_current)+20} = 短线转强；跌破 {sh_pred_low} = 转弱 |
| **创业板** | **{gem_pred_low}~{gem_pred_high}** | 站稳 {int(gem_current)+10} 可看 {int(gem_current)+40}；失守 {gem_pred_low} 回调 |

### 核心预判逻辑

1. 上证{'震荡整理' if abs(sh_idx.get('change_pct', 0)) < 1 else '方向选择'}
2. 关键观察：早盘30分钟量能、板块联动性、涨跌停家数

---

## 4) 实操策略

### 仓位建议
- 建议总仓 **4~6 成**

### 方向配置
- **进攻方向**：关注今日强势板块延续性
- **回避方向**：高位放量下跌个股

### 风控
- 单笔止损 **3%~5%**
- 若跌停家数超 20 家，暂停开新仓

---

> ⚠️ **风险提示**：以上分析基于公开市场数据，仅供参考，不构成投资建议。市场有风险，投资需谨慎。
"""
    return report


def save_to_obsidian(report: str, date_str: str) -> str:
    """保存报告到 Obsidian vault"""
    filename = f"{date_str}-A股深度复盘与{(datetime.strptime(date_str, '%Y-%m-%d') + timedelta(days=1)).strftime('%m%d')}预判.md"
    filepath = Path(REPORTS_DIR) / filename
    
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(report, encoding="utf-8")
    
    return str(filepath)


def send_qq_mail(report: str, date_str: str) -> bool:
    """通过 QQ 邮箱发送复盘报告"""
    if not QQ_MAIL_USER or not QQ_MAIL_AUTH_CODE or not QQ_MAIL_TO:
        print("  ⚠️ QQ邮箱未配置（QQ_MAIL_USER/QQ_MAIL_AUTH_CODE/QQ_MAIL_TO），跳过邮件发送")
        return False
    
    try:
        import smtplib
        import ssl
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.base import MIMEBase
        from email import encoders
    except ImportError as e:
        print(f"  ❌ 邮件模块导入失败: {e}")
        return False
    
    try:
        msg = MIMEMultipart()
        msg["From"] = QQ_MAIL_USER
        msg["To"] = QQ_MAIL_TO
        msg["Subject"] = f"📊 {date_str} A股复盘报告"
        
        # 正文：完整报告内容（Markdown → HTML 简单转换）
        html_body = report.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        # 加粗
        html_body = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_body)
        # 标题
        html_body = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html_body, flags=re.MULTILINE)
        html_body = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html_body, flags=re.MULTILINE)
        html_body = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html_body, flags=re.MULTILINE)
        # 表格行 → 简单缩进
        html_lines = []
        for line in html_body.split("\n"):
            if line.startswith("|") and line.endswith("|"):
                cells = [c.strip() for c in line.strip("|").split("|")]
                html_lines.append("　" + " | ".join(cells))
            elif line.startswith("---"):
                continue
            else:
                html_lines.append(line)
        html_body = "<br>".join(html_lines)
        
        html = f"""<html><body style="font-family: -apple-system, sans-serif; font-size: 14px; line-height: 1.6; color: #333;">
{html_body}
<hr style="border:none;border-top:1px solid #eee;margin:20px 0;">
<p style="color:#999;font-size:12px;">由 OpenClaw 自动生成 · 数据来源：腾讯财经</p>
</body></html>"""
        
        msg.attach(MIMEText(html, "html", "utf-8"))
        
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.qq.com", 465, context=ctx) as server:
            server.login(QQ_MAIL_USER, QQ_MAIL_AUTH_CODE)
            server.send_message(msg)
        
        print(f"  ✅ QQ邮件发送成功 → {QQ_MAIL_TO}")
        return True
        
    except Exception as e:
        print(f"  ❌ QQ邮件发送失败: {e}")
        return False


def send_feishu_notification(report: str, date_str: str, indices: dict) -> bool:
    """发送飞书 webhook 通知（报告摘要）"""
    if not FEISHU_WEBHOOK:
        print("  ⚠️ FEISHU_WEBHOOK_URL 未配置，跳过飞书通知")
        return False
    
    sh = indices.get("sh000001", {})
    gem = indices.get("sz399006", {})
    
    # 提取关键行（明日预判部分）
    pred_lines = []
    in_pred = False
    for line in report.split("\n"):
        if "下个交易日" in line or "预判" in line:
            in_pred = True
        if in_pred:
            if line.startswith("### "):
                break
            pred_lines.append(line)
    
    pred_text = "\n".join(pred_lines[:15]).strip()
    
    text = f"""📊 {date_str} A股复盘

上证 {sh.get('current', 0):.2f} ({sh.get('change_pct', 0):+.2f}%) | 创业板 {gem.get('current', 0):.2f} ({gem.get('change_pct', 0):+.2f}%)

{pred_text}

openclaw 已自动保存至 Obsidian 并推送至 GitHub"""
    
    payload = json.dumps({
        "msg_type": "text",
        "content": {"text": text}
    }, ensure_ascii=False).encode("utf-8")
    
    try:
        req = urllib.request.Request(
            FEISHU_WEBHOOK,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            if result.get("code") == 0 or result.get("StatusCode") == 0:
                print("  ✅ 飞书通知发送成功")
                return True
            else:
                print(f"  ⚠️ 飞书通知返回异常: {result}")
                return False
    except Exception as e:
        print(f"  ❌ 飞书通知发送失败: {e}")
        return False


def git_push(date_str: str) -> bool:
    """Git add + commit + push"""
    try:
        os.chdir(OBSIDIAN_VAULT)
        
        # Configure git if needed
        subprocess.run(["git", "config", "user.email", "openclaw@local"], check=False)
        subprocess.run(["git", "config", "user.name", "OpenClaw"], check=False)
        
        # Add all changes
        subprocess.run(["git", "add", "-A"], check=True)
        
        # Commit
        result = subprocess.run(
            ["git", "commit", "-m", f"📊 {date_str} A股复盘报告"],
            capture_output=True, text=True
        )
        
        if "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
            print("No changes to commit")
            return True
        
        # Push
        result = subprocess.run(
            ["git", "push", "origin", "master"],
            capture_output=True, text=True, timeout=60
        )
        
        if result.returncode == 0:
            print("✅ Git push successful")
            return True
        else:
            print(f"❌ Git push failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Git error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="A股每日复盘报告生成器")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"), help="报告日期 YYYY-MM-DD")
    args = parser.parse_args()
    
    date_str = args.date
    print(f"📊 生成 {date_str} A股复盘报告...")
    
    # 1. 获取指数数据
    print("  📈 获取指数数据...")
    indices = fetch_tencent_data(list(INDICES.keys()))
    
    # 2. 获取个股数据
    print("  📊 获取个股数据...")
    stocks = fetch_tencent_data(list(KEY_STOCKS.keys()))
    
    if not indices:
        print("❌ 获取指数数据失败")
        sys.exit(1)
    
    # 3. 解析前一份报告的预测
    prev_predictions = parse_prev_report(date_str)
    
    # 4. 生成报告
    print("  📝 生成报告...")
    report = generate_report(indices, stocks, date_str, prev_predictions)
    
    # 5. 保存到 Obsidian
    print("  💾 保存到 Obsidian...")
    filepath = save_to_obsidian(report, date_str)
    print(f"  ✅ 已保存: {filepath}")
    
    # 6. Git push
    print("  🚀 Git push...")
    git_push(date_str)
    
    # 7. QQ邮件通知
    print("  📧 发送QQ邮件...")
    send_qq_mail(report, date_str)
    
    # 8. 输出报告内容
    print("\n" + "="*60)
    print(report)
    print("="*60)
    
    return filepath, report


if __name__ == "__main__":
    main()
