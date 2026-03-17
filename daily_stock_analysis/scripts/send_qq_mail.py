#!/usr/bin/env python3
"""QQ邮箱发送工具 - 支持 Markdown 转 HTML 邮件 + PDF 附件"""
import os
import sys
import smtplib
import argparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from pathlib import Path

def md_to_html(md_text: str) -> str:
    """Markdown → HTML 转换（使用 markdown 库 + tables 扩展）"""
    import markdown
    return markdown.markdown(
        md_text,
        extensions=['tables', 'fenced_code', 'nl2br', 'sane_lists'],
        output_format='html5'
    )

def send_mail(to_addr: str, subject: str, md_content: str, 
              pdf_path: str = None, dry_run: bool = False):
    smtp_host = os.environ.get('SMTP_HOST', 'smtp.qq.com')
    smtp_port = int(os.environ.get('SMTP_PORT', '465'))
    from_addr = os.environ.get('QQ_MAIL', '')
    auth_code = os.environ.get('QQ_SMTP_AUTH_CODE', '')
    
    if not from_addr or not auth_code:
        print("缺少 QQ_MAIL 或 QQ_SMTP_AUTH_CODE 环境变量")
        return False
    
    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg['Subject'] = subject
    
    html_body = f"""<html><head><meta charset="utf-8"><style>
        body {{ font-family: -apple-system, 'Microsoft YaHei', 'PingFang SC', sans-serif; max-width: 960px; margin: 0 auto; padding: 16px; color: #333; line-height: 1.6; }}
        h1 {{ color: #1a73e8; border-bottom: 3px solid #1a73e8; padding-bottom: 10px; margin-top: 24px; }}
        h2 {{ color: #333; border-bottom: 1px solid #e0e0e0; padding-bottom: 6px; margin-top: 28px; }}
        h3 {{ color: #555; margin-top: 20px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 14px 0; font-size: 14px; }}
        th {{ background: #f0f4f8; font-weight: 600; color: #1a73e8; }}
        td, th {{ border: 1px solid #d0d7de; padding: 8px 12px; text-align: left; }}
        tr:nth-child(even) {{ background: #f9fafb; }}
        blockquote {{ border-left: 4px solid #1a73e8; margin: 12px 0; padding: 8px 16px; background: #f0f7ff; color: #555; }}
        ul, ol {{ padding-left: 24px; }}
        li {{ margin: 4px 0; }}
        hr {{ border: none; border-top: 2px solid #e0e0e0; margin: 20px 0; }}
        strong {{ color: #222; }}
        code {{ background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-size: 13px; }}
        p {{ margin: 8px 0; }}
    </style></head><body>{md_to_html(md_content)}</body></html>"""
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))
    
    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, 'rb') as f:
            pdf = MIMEApplication(f.read(), _subtype='pdf')
            pdf.add_header('Content-Disposition', 'attachment', 
                          filename=os.path.basename(pdf_path))
            msg.attach(pdf)
    
    if dry_run:
        print(f"[DRY RUN] 将发送到 {to_addr}, 主题: {subject}")
        return True
    
    try:
        import ssl
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
            server.login(from_addr, auth_code)
            server.sendmail(from_addr, [to_addr], msg.as_string())
        print(f"邮件已发送到 {to_addr}")
        return True
    except Exception as e:
        print(f"发送失败: {e}")
        return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='QQ邮箱发送工具')
    parser.add_argument('--to', default='1318263468@qq.com', help='收件人')
    parser.add_argument('--subject', required=True, help='邮件主题')
    parser.add_argument('--file', help='Markdown 报告文件路径')
    parser.add_argument('--pdf', help='PDF 附件路径')
    parser.add_argument('--dry-run', action='store_true', help='试运行')
    args = parser.parse_args()
    
    md_content = ''
    if args.file:
        md_content = Path(args.file).read_text(encoding='utf-8')
    
    send_mail(args.to, args.subject, md_content, args.pdf, args.dry_run)
