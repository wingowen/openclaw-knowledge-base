#!/usr/bin/env python3
"""
sync_doc_to_notion.py

读取本地 Markdown 文档，按 config/notion_sync_rules.yaml 路由并同步到 Notion。
- 同标题查重：存在则 append 更新块
- 不存在则创建子页面并写入全文
- 支持 --dry-run
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib import request, error

import yaml

WORKSPACE = Path('/root/.openclaw/workspace')
DEFAULT_RULES = WORKSPACE / 'config' / 'notion_sync_rules.yaml'


def load_notion_key() -> str:
    env_key = os.getenv('NOTION_KEY') or os.getenv('NOTION_API_KEY')
    if env_key and env_key.strip():
        return env_key.strip()

    key_file = Path.home() / '.config' / 'notion' / 'api_key'
    if key_file.exists():
        line = key_file.read_text(encoding='utf-8').splitlines()
        if line and line[0].strip():
            return line[0].strip()

    raise RuntimeError('缺少 Notion API Key（NOTION_KEY/NOTION_API_KEY 或 ~/.config/notion/api_key）')


def notion_request(method: str, path: str, body: Optional[dict] = None, notion_version: str = '2025-09-03') -> dict:
    key = load_notion_key()
    url = f'https://api.notion.com/v1{path}'
    data = json.dumps(body).encode('utf-8') if body is not None else None

    req = request.Request(url=url, data=data, method=method)
    req.add_header('Authorization', f'Bearer {key}')
    req.add_header('Notion-Version', notion_version)
    req.add_header('Content-Type', 'application/json')

    try:
        with request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode('utf-8')
            return json.loads(raw) if raw else {}
    except error.HTTPError as e:
        text = e.read().decode('utf-8', errors='ignore')
        raise RuntimeError(f'Notion API HTTP {e.code}: {text}') from e


def normalize_page_id(pid: str) -> str:
    x = pid.strip()
    if '-' in x and len(x) == 36:
        return x
    x = x.replace('-', '')
    if len(x) != 32:
        raise ValueError(f'非法 page id: {pid}')
    return f'{x[0:8]}-{x[8:12]}-{x[12:16]}-{x[16:20]}-{x[20:32]}'


def infer_doc_type(title: str, content: str, routes: Dict[str, dict]) -> str:
    text = f"{title}\n{content}".lower()
    best = ('unknown', -1)
    for name, conf in routes.items():
        kws = conf.get('keywords', []) or []
        score = 0
        for kw in kws:
            if str(kw).lower() in text:
                score += 1
        if score > best[1]:
            best = (name, score)
    return best[0] if best[1] > 0 else 'unknown'


def list_child_pages(parent_page_id: str) -> List[dict]:
    parent_page_id = normalize_page_id(parent_page_id)
    out = notion_request('GET', f'/blocks/{parent_page_id}/children?page_size=100')
    rows = []
    for b in out.get('results', []):
        if b.get('type') == 'child_page':
            rows.append({'id': b.get('id'), 'title': b.get('child_page', {}).get('title', '')})
    return rows


def find_existing_page(parent_page_id: str, title: str) -> Optional[dict]:
    title_n = title.strip()
    for p in list_child_pages(parent_page_id):
        if p['title'].strip() == title_n:
            return p
    return None


def create_child_page(parent_page_id: str, title: str) -> dict:
    parent_page_id = normalize_page_id(parent_page_id)
    payload = {
        'parent': {'page_id': parent_page_id},
        'properties': {
            'title': {
                'title': [
                    {'type': 'text', 'text': {'content': title}}
                ]
            }
        }
    }
    return notion_request('POST', '/pages', payload)


def plain_rich_text(
    text: str,
    bold: bool = False,
    italic: bool = False,
    code: bool = False,
    strikethrough: bool = False,
    link: str = ''
) -> List[dict]:
    text = text if text else ' '
    chunks = [text[i:i+1800] for i in range(0, len(text), 1800)] or [' ']
    out = []
    for c in chunks:
        node = {'type': 'text', 'text': {'content': c}}
        if link:
            node['text']['link'] = {'url': link}

        ann = {}
        if bold:
            ann['bold'] = True
        if italic:
            ann['italic'] = True
        if code:
            ann['code'] = True
        if strikethrough:
            ann['strikethrough'] = True
        if ann:
            node['annotations'] = ann

        out.append(node)
    return out


def rich_text(text: str) -> List[dict]:
    """支持常见内联 markdown：**bold**、*italic*、`code`、~~del~~、[text](url)"""
    text = text if text else ' '

    token_re = re.compile(
        r'(\[[^\]]+\]\(https?://[^)\s]+\)'
        r'|\*\*[^*]+\*\*'
        r'|__[^_]+__'
        r'|\*[^*\n]+\*'
        r'|_[^_\n]+_'
        r'|`[^`]+`'
        r'|~~[^~]+~~)'
    )

    parts = token_re.split(text)
    out: List[dict] = []

    for p in parts:
        if not p:
            continue

        # link
        m = re.fullmatch(r'\[([^\]]+)\]\((https?://[^)\s]+)\)', p)
        if m:
            label, url = m.group(1), m.group(2)
            out.extend(plain_rich_text(label, link=url))
            continue

        # bold
        if (p.startswith('**') and p.endswith('**') and len(p) >= 4) or (p.startswith('__') and p.endswith('__') and len(p) >= 4):
            out.extend(plain_rich_text(p[2:-2], bold=True))
            continue

        # italic
        if (p.startswith('*') and p.endswith('*') and len(p) >= 3) or (p.startswith('_') and p.endswith('_') and len(p) >= 3):
            out.extend(plain_rich_text(p[1:-1], italic=True))
            continue

        # inline code
        if p.startswith('`') and p.endswith('`') and len(p) >= 3:
            out.extend(plain_rich_text(p[1:-1], code=True))
            continue

        # strike
        if p.startswith('~~') and p.endswith('~~') and len(p) >= 5:
            out.extend(plain_rich_text(p[2:-2], strikethrough=True))
            continue

        out.extend(plain_rich_text(p))

    return out or plain_rich_text(' ')


def md_to_blocks(md: str) -> List[dict]:
    lines = md.splitlines()
    blocks: List[dict] = []

    for line in lines:
        s = line.rstrip('\n')
        if not s.strip():
            continue

        if s.startswith('### '):
            blocks.append({'object': 'block', 'type': 'heading_3', 'heading_3': {'rich_text': rich_text(s[4:].strip())}})
        elif s.startswith('## '):
            blocks.append({'object': 'block', 'type': 'heading_2', 'heading_2': {'rich_text': rich_text(s[3:].strip())}})
        elif s.startswith('# '):
            blocks.append({'object': 'block', 'type': 'heading_1', 'heading_1': {'rich_text': rich_text(s[2:].strip())}})
        elif re.match(r'^\s*[-*]\s+', s):
            txt = re.sub(r'^\s*[-*]\s+', '', s)
            blocks.append({'object': 'block', 'type': 'bulleted_list_item', 'bulleted_list_item': {'rich_text': rich_text(txt)}})
        elif re.match(r'^\s*\d+[\.)]\s+', s):
            txt = re.sub(r'^\s*\d+[\.)]\s+', '', s)
            blocks.append({'object': 'block', 'type': 'numbered_list_item', 'numbered_list_item': {'rich_text': rich_text(txt)}})
        elif s.strip() in ('---', '***', '___'):
            blocks.append({'object': 'block', 'type': 'divider', 'divider': {}})
        else:
            blocks.append({'object': 'block', 'type': 'paragraph', 'paragraph': {'rich_text': rich_text(s.strip())}})

    return blocks


def append_blocks(block_id: str, blocks: List[dict], chunk_size: int = 80):
    block_id = normalize_page_id(block_id)
    for i in range(0, len(blocks), chunk_size):
        chunk = blocks[i:i+chunk_size]
        notion_request('PATCH', f'/blocks/{block_id}/children', {'children': chunk})


def now_cn() -> Tuple[str, str]:
    t = dt.datetime.now(dt.timezone(dt.timedelta(hours=8)))
    return t.strftime('%Y-%m-%dT%H:%M:%S%z'), t.strftime('%H:%M')


def append_journal(path: Path, obj: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(obj, ensure_ascii=False) + '\n')


def guess_title_from_file(file_path: Path) -> str:
    # 页面标题直接使用文件名（不含后缀）
    return file_path.stem.strip()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description='将 Markdown 文档同步到 Notion')
    p.add_argument('--file', required=True, help='本地 markdown 文件路径')
    p.add_argument('--title', default='', help='文档标题（默认用文件名）')
    p.add_argument('--type', default='', help='路由类型：stock/daily/tool/memory/project/todo')
    p.add_argument('--rules', default=str(DEFAULT_RULES), help='规则文件路径')
    p.add_argument('--dry-run', action='store_true', help='只显示计划，不实际写入')
    return p.parse_args()


def strip_leading_title(md: str, title: str) -> str:
    """如果文档首行是一级标题，则去掉它，避免 Notion 页面内重复标题。"""
    lines = md.splitlines()
    if not lines:
        return md

    first = lines[0].strip()
    if first.startswith('# '):
        rest = lines[1:]
        # 去掉紧随的空行
        while rest and not rest[0].strip():
            rest = rest[1:]
        return '\n'.join(rest)

    return md


def main():
    args = parse_args()
    file_path = Path(args.file).expanduser().resolve()
    rules_path = Path(args.rules).expanduser().resolve()

    if not file_path.exists():
        raise FileNotFoundError(f'文件不存在: {file_path}')
    if not rules_path.exists():
        raise FileNotFoundError(f'规则文件不存在: {rules_path}')

    rules = yaml.safe_load(rules_path.read_text(encoding='utf-8'))
    routes = rules.get('routes', {})

    md = file_path.read_text(encoding='utf-8')
    title = args.title.strip() or guess_title_from_file(file_path)
    md = strip_leading_title(md, title)

    doc_type = args.type.strip() or infer_doc_type(title, md, routes)
    route = routes.get(doc_type, {})
    parent_page_id = route.get('parent_page_id') or rules['notion']['default_parent_page_id']

    iso_now, hhmm = now_cn()

    # 查重
    existing = find_existing_page(parent_page_id, title)
    action = 'append_update' if existing else 'create'

    if args.dry_run:
        print(json.dumps({
            'dry_run': True,
            'file': str(file_path),
            'title': title,
            'doc_type': doc_type,
            'parent_page_id': parent_page_id,
            'existing': existing,
            'action': action,
        }, ensure_ascii=False, indent=2))
        return

    if existing:
        target_page_id = existing['id']
        heading = rules.get('sync_policy', {}).get('append_update', {}).get('heading_template', 'Update @{time}')
        heading = heading.replace('{time}', hhmm)
        payload_md = f"## {heading}\n\n{md}"
        blocks = md_to_blocks(payload_md)
        append_blocks(target_page_id, blocks, chunk_size=rules.get('sync_policy', {}).get('write', {}).get('max_blocks_per_request', 80))
        notion_url = f"https://www.notion.so/{target_page_id.replace('-', '')}"
    else:
        created = create_child_page(parent_page_id, title)
        target_page_id = created['id']
        blocks = md_to_blocks(md)
        append_blocks(target_page_id, blocks, chunk_size=rules.get('sync_policy', {}).get('write', {}).get('max_blocks_per_request', 80))
        notion_url = created.get('url', f"https://www.notion.so/{target_page_id.replace('-', '')}")

    journal_path = Path(rules.get('logging', {}).get('journal_file', str(WORKSPACE / 'memory' / 'notion_sync_journal.jsonl')))
    append_journal(journal_path, {
        'time': iso_now,
        'title': title,
        'file': str(file_path),
        'doc_type': doc_type,
        'action': action,
        'parent_page_id': parent_page_id,
        'target_page_id': target_page_id,
        'notion_url': notion_url,
    })

    print(json.dumps({
        'ok': True,
        'action': action,
        'title': title,
        'doc_type': doc_type,
        'parent_page_id': parent_page_id,
        'target_page_id': target_page_id,
        'notion_url': notion_url,
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'ERROR: {e}', file=sys.stderr)
        sys.exit(1)
