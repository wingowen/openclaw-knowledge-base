#!/usr/bin/env python3
"""Markdown → HTML email converter (for A股复盘报告)"""
import re
import sys
import argparse


def md_to_html(md: str) -> str:
    html = md.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # Headers
    html = re.sub(r'^# (.+)$', r'<h1 style="color:#1a1a1a;border-bottom:3px solid #1a73e8;padding-bottom:8px">\1</h1>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2 style="color:#333;border-bottom:2px solid #eee;padding-bottom:6px;margin-top:24px">\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.+)$', r'<h3 style="color:#444;margin-top:16px">\1</h3>', html, flags=re.MULTILINE)

    # Bold
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)

    # Blockquotes
    html = re.sub(r'^&gt; (.+)$', r'<blockquote style="border-left:4px solid #ddd;margin:10px 0;padding:8px 16px;color:#666">\1</blockquote>', html, flags=re.MULTILINE)

    # Tables
    lines = html.split('\n')
    out = []
    in_table = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('|') and stripped.endswith('|'):
            if not in_table:
                out.append('<table style="border-collapse:collapse;margin:12px 0;width:100%">')
                in_table = True
            cells = [c.strip() for c in stripped.strip('|').split('|')]
            if all(set(c) <= set('- ') for c in cells):
                continue
            is_header = any(k in stripped for k in ['指数', '股票', '预判', '项目', '配置'])
            tag = 'th' if is_header else 'td'
            style = 'background:#f5f5f5;font-weight:bold' if is_header else ''
            row = ''.join(f'<{tag} style="border:1px solid #ddd;padding:8px 12px;text-align:left;{style}">{c}</{tag}>' for c in cells)
            out.append(f'<tr>{row}</tr>')
        else:
            if in_table:
                out.append('</table>')
                in_table = False
            out.append(line)
    if in_table:
        out.append('</table>')
    html = '\n'.join(out)

    # Lists
    html = re.sub(r'^- (.+)$', r'<li style="margin:4px 0">\1</li>', html, flags=re.MULTILINE)
    html = re.sub(r'^(\d+)\. (.+)$', r'<li style="margin:4px 0">\2</li>', html, flags=re.MULTILINE)

    # Horizontal rules
    html = re.sub(r'^---$', '<hr style="border:none;border-top:1px solid #eee;margin:20px 0">', html, flags=re.MULTILINE)

    # Paragraphs (double newline)
    html = re.sub(r'\n{2,}', '<br><br>', html)
    html = re.sub(r'\n', '<br>', html)

    return html


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs="?", help="Markdown file path")
    parser.add_argument("--stdin", action="store_true")
    args = parser.parse_args()

    if args.stdin:
        md = sys.stdin.read()
    elif args.file:
        with open(args.file, "r") as f:
            md = f.read()
    else:
        print("Usage: md2html.py <file.md> or --stdin", file=sys.stderr)
        sys.exit(1)

    body = md_to_html(md)
    full = f"""<html><body style="font-family:-apple-system,'Microsoft YaHei',sans-serif;font-size:14px;line-height:1.8;color:#333;max-width:800px;margin:0 auto;padding:20px">
{body}
<hr style="border:none;border-top:1px solid #eee;margin:20px 0">
<p style="color:#999;font-size:12px">由 OpenClaw 自动生成 · 数据来源：腾讯财经</p>
</body></html>"""
    print(full)


if __name__ == "__main__":
    main()
