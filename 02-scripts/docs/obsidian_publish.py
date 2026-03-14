#!/usr/bin/env python3
"""
obsidian_publish.py

将 Obsidian 目录下的 Markdown 发布到 Notion（复用 sync_doc_to_notion.py）。
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

WORKSPACE = Path('/root/.openclaw/workspace')
OBSIDIAN = WORKSPACE / 'obsidian'
SYNC_SCRIPT = WORKSPACE / 'scripts' / 'sync_doc_to_notion.py'

ROUTE_MAP = {
    '04-Reviews': 'stock',
    '01-Daily': 'daily',
    '02-Projects': 'project',
    '03-Knowledge': 'memory',
    '00-Inbox': 'tool',
    '05-Archive': 'tool',
}


def infer_type(file_path: Path) -> str:
    rel = file_path.relative_to(OBSIDIAN)
    top = rel.parts[0] if rel.parts else ''
    return ROUTE_MAP.get(top, 'tool')


def main() -> None:
    p = argparse.ArgumentParser(description='发布 Obsidian 文档到 Notion')
    p.add_argument('--file', required=True, help='obsidian 内相对路径或绝对路径')
    p.add_argument('--type', default='', help='可手动覆盖路由类型')
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()

    f = Path(args.file)
    if not f.is_absolute():
        f = (OBSIDIAN / f).resolve()

    if not f.exists():
        raise FileNotFoundError(f'文件不存在: {f}')

    doc_type = args.type.strip() or infer_type(f)

    cmd = [
        'python3', str(SYNC_SCRIPT),
        '--file', str(f),
        '--type', doc_type,
    ]
    if args.dry_run:
        cmd.append('--dry-run')

    subprocess.run(cmd, check=True)


if __name__ == '__main__':
    main()
