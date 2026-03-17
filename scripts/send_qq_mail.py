#!/usr/bin/env python3
"""
QQ 邮件发送工具 - 支持 PDF 附件或 HTML 正文
Usage: 
  python3 send_qq_mail.py --subject "标题" --pdf report.pdf
  python3 send_qq_mail.py --subject "标题" --html report.html
  python3 send_qq_mail.py --subject "标题" --md report.md  (自动转PDF)
"""
import argparse
import os
import smtplib
import ssl
import sys
import subprocess
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

QQ_MAIL_USER = os.environ.get("QQ_MAIL_USER", "1318263468@qq.com")
QQ_MAIL_AUTH_CODE = os.environ.get("QQ_MAIL_AUTH_CODE", "")
QQ_MAIL_TO = os.environ.get("QQ_MAIL_TO", QQ_MAIL_USER)


def md_to_pdf(md_path: str, pdf_path: str) -> bool:
    """Markdown → HTML → PDF"""
    try:
        import markdown
        import weasyprint

        with open(md_path, "r") as f:
            md_content = f.read()

        # Replace emoji with text equivalents for PDF compatibility
        emoji_map = {
            '🔴': '[风险]',
            '🟢': '[机会]',
            '🔥': '[关注]',
            '⚠️': '[注意]',
            '✅': '[OK]',
            '❌': '[X]',
            '📊': '',
            '📈': '',
            '📉': '',
            '💹': '',
            '🎯': '',
            '💡': '',
            '📝': '',
            '🚀': '',
            '💰': '',
            '🏦': '',
            '📱': '',
            '📧': '',
        }
        for emoji, replacement in emoji_map.items():
            md_content = md_content.replace(emoji, replacement)

        # Markdown → HTML
        html_body = markdown.markdown(md_content, extensions=["tables", "fenced_code"])

        full_html = f"""<html><head><meta charset="utf-8">
<style>
@page {{ size: A4; margin: 2cm; }}
body {{ font-family: -apple-system, 'Microsoft YaHei', 'PingFang SC', sans-serif; 
       font-size: 11pt; line-height: 1.7; color: #333; }}
h1 {{ color: #1a1a1a; border-bottom: 3px solid #1a73e8; padding-bottom: 8px; font-size: 18pt; }}
h2 {{ color: #333; border-bottom: 2px solid #eee; padding-bottom: 6px; margin-top: 24px; font-size: 14pt; }}
h3 {{ color: #444; margin-top: 16px; font-size: 12pt; }}
table {{ border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 10pt; }}
th, td {{ border: 1px solid #ddd; padding: 6px 10px; text-align: left; }}
th {{ background: #f5f5f5; font-weight: bold; }}
blockquote {{ border-left: 4px solid #ddd; margin: 10px 0; padding: 8px 16px; color: #666; background: #fafafa; }}
hr {{ border: none; border-top: 1px solid #eee; margin: 20px 0; }}
strong {{ color: #1a1a1a; }}
.footer {{ color: #999; font-size: 9pt; margin-top: 30px; text-align: center; }}
</style></head><body>
{html_body}
<div class="footer">由 OpenClaw 自动生成 · 数据来源：腾讯财经</div>
</body></html>"""

        weasyprint.HTML(string=full_html).write_pdf(pdf_path)
        return True
    except Exception as e:
        print(f"PDF generation failed: {e}", file=sys.stderr)
        return False


def send_mail(subject: str, body_html: str = None, pdf_path: str = None, to: str = None) -> bool:
    to = to or QQ_MAIL_TO
    if not QQ_MAIL_AUTH_CODE:
        print("ERROR: QQ_MAIL_AUTH_CODE not set", file=sys.stderr)
        return False

    if pdf_path and os.path.exists(pdf_path):
        # Email with PDF attachment (simple body)
        msg = MIMEMultipart()
        msg["From"] = QQ_MAIL_USER
        msg["To"] = to
        msg["Subject"] = subject
        
        body_text = f"📊 {subject}\n\n详细报告见附件 PDF。\n\n---\n由 OpenClaw 自动生成"
        msg.attach(MIMEText(body_text, "plain", "utf-8"))
        
        with open(pdf_path, "rb") as f:
            part = MIMEBase("application", "pdf")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", "attachment", filename=os.path.basename(pdf_path))
            msg.attach(part)
    elif body_html:
        # HTML in body
        msg = MIMEText(body_html, "html", "utf-8")
        msg["From"] = QQ_MAIL_USER
        msg["To"] = to
        msg["Subject"] = subject
    else:
        print("ERROR: need pdf_path or body_html", file=sys.stderr)
        return False

    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.qq.com", 465, context=ctx) as server:
        server.login(QQ_MAIL_USER, QQ_MAIL_AUTH_CODE)
        server.send_message(msg)
    print(f"✅ Sent to {to}" + (f" (PDF: {os.path.basename(pdf_path)})" if pdf_path else ""))
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", required=True)
    parser.add_argument("--pdf", help="PDF file to attach")
    parser.add_argument("--html", help="HTML file for email body")
    parser.add_argument("--md", help="Markdown file, will convert to PDF")
    parser.add_argument("--to", default=None)
    args = parser.parse_args()

    if args.md:
        # Convert MD → PDF
        pdf_path = args.md.replace(".md", ".pdf")
        print(f"Converting {args.md} → {pdf_path}...")
        if md_to_pdf(args.md, pdf_path):
            send_mail(args.subject, pdf_path=pdf_path, to=args.to)
        else:
            sys.exit(1)
    elif args.pdf:
        send_mail(args.subject, pdf_path=args.pdf, to=args.to)
    elif args.html:
        with open(args.html) as f:
            send_mail(args.subject, body_html=f.read(), to=args.to)
    else:
        print("Need --md, --pdf, or --html", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
