#!/usr/bin/env python3
"""
每天扫描工作区文档更新，生成“是否同步到 Notion”的待询问提示。

用法:
  python3 check_doc_updates.py
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List

TZ = timezone(timedelta(hours=8))
WORKSPACE = Path('/root/.openclaw/workspace')
STATE_FILE = WORKSPACE / 'memory' / 'doc_update_state.json'
PROMPT_FILE = WORKSPACE / 'memory' / 'doc_update_prompt.md'
HISTORY_FILE = WORKSPACE / 'memory' / 'doc_update_history.jsonl'
LOG_FILE = WORKSPACE / 'memory' / 'doc_update_check.log'

INCLUDE_SUFFIX = {'.md', '.txt', '.rst', '.adoc', '.json', '.yaml', '.yml', '.csv'}
EXCLUDE_DIR_NAMES = {
    '.git', 'node_modules', '__pycache__', '.openclaw',
    'assets', 'stock_data', 'nce-data/data', 'memory'
}


@dataclass
class Doc:
    path: Path
    mtime: float


def now_ts() -> float:
    return datetime.now(TZ).timestamp()


def fmt_ts(ts: float) -> str:
    return datetime.fromtimestamp(ts, TZ).strftime('%Y-%m-%d %H:%M:%S GMT+8')


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"last_check_ts": 0.0, "initialized": False}
    try:
        s = json.loads(STATE_FILE.read_text(encoding='utf-8'))
        s.setdefault('initialized', True)
        s.setdefault('last_check_ts', 0.0)
        return s
    except Exception:
        return {"last_check_ts": 0.0, "initialized": False}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')


def should_exclude(path: Path) -> bool:
    rel = path.relative_to(WORKSPACE).as_posix()
    for ex in EXCLUDE_DIR_NAMES:
        if rel == ex or rel.startswith(ex + '/'):
            return True
    return False


def iter_docs() -> List[Doc]:
    docs: List[Doc] = []
    for p in WORKSPACE.rglob('*'):
        if not p.is_file():
            continue
        if should_exclude(p):
            continue
        if p.suffix.lower() not in INCLUDE_SUFFIX:
            continue
        try:
            st = p.stat()
        except FileNotFoundError:
            continue
        docs.append(Doc(path=p, mtime=st.st_mtime))
    return docs


def write_history(entry: dict) -> None:
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with HISTORY_FILE.open('a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')


def write_prompt(changed: List[Doc], since_ts: float, check_ts: float) -> None:
    lines = []
    lines.append('# 待确认：文档同步到 Notion')
    lines.append('')
    lines.append(f'- 检查时间：{fmt_ts(check_ts)}')
    lines.append(f'- 比较区间起点：{fmt_ts(since_ts) if since_ts else "首次检查"}')
    lines.append(f'- 检测到更新文档：{len(changed)} 个')
    lines.append('')
    lines.append('请确认：是否现在同步这些更新到 Notion？')
    lines.append('')
    lines.append('更新列表（最多展示前 20 个）：')
    for d in changed[:20]:
        rel = d.path.relative_to(WORKSPACE).as_posix()
        lines.append(f'- {rel}  （{fmt_ts(d.mtime)}）')

    PROMPT_FILE.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def append_log(msg: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open('a', encoding='utf-8') as f:
        f.write(msg + '\n')


def main() -> None:
    state = load_state()
    since_ts = float(state.get('last_check_ts', 0.0) or 0.0)
    check_ts = now_ts()

    # 首次运行仅建立基线，不打扰用户
    if not state.get('initialized', False):
        state['initialized'] = True
        state['last_check_ts'] = check_ts
        save_state(state)
        if PROMPT_FILE.exists():
            PROMPT_FILE.unlink()
        append_log(f"[{fmt_ts(check_ts)}] init baseline set")
        write_history({
            'time': fmt_ts(check_ts),
            'since_ts': since_ts,
            'check_ts': check_ts,
            'changed_count': 0,
            'changed_files': [],
            'note': 'initialized baseline',
        })
        return

    changed = [d for d in iter_docs() if d.mtime > since_ts]
    changed.sort(key=lambda x: x.mtime, reverse=True)

    entry = {
        'time': fmt_ts(check_ts),
        'since_ts': since_ts,
        'check_ts': check_ts,
        'changed_count': len(changed),
        'changed_files': [d.path.relative_to(WORKSPACE).as_posix() for d in changed[:50]],
    }
    write_history(entry)

    if changed:
        write_prompt(changed, since_ts, check_ts)
        append_log(f"[{fmt_ts(check_ts)}] changed={len(changed)} prompt_written={PROMPT_FILE}")
    else:
        if PROMPT_FILE.exists():
            PROMPT_FILE.unlink()
        append_log(f"[{fmt_ts(check_ts)}] changed=0")

    state['last_check_ts'] = check_ts
    save_state(state)


if __name__ == '__main__':
    main()
