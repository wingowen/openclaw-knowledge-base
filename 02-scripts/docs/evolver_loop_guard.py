#!/usr/bin/env python3
import datetime
import json
import pathlib
import subprocess
import time
import sys

BASE = pathlib.Path('/root/.openclaw/workspace/memory/evolution')
STATE = BASE / 'memory_graph_state.json'
SOLID = BASE / 'evolution_solidify_state.json'
GUARD_STATE = BASE / 'loop_guard_state.json'
EVOLVER_DIR = pathlib.Path('/root/.openclaw/workspace/skills/capability-evolver')
SELF_IMPROVING_ERRORS = pathlib.Path('/root/.openclaw/workspace/.learnings/ERRORS.md')

WARN_AGE_MIN = 25
AUTOHEAL_WARN_THRESHOLD = 2
AUTOHEAL_COOLDOWN_MIN = 45
AUTOHEAL_FAIL_THRESHOLD = 3
AUTOHEAL_PAUSE_HOURS = 6


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc)


def iso(dt):
    return dt.isoformat().replace('+00:00', 'Z')


def parse_iso(s):
    if not s:
        return None
    try:
        return datetime.datetime.fromisoformat(str(s).replace('Z', '+00:00'))
    except Exception:
        return None


def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def append_autoheal_learning(autoheal_result, reason, created_at, age_min):
    try:
        SELF_IMPROVING_ERRORS.parent.mkdir(parents=True, exist_ok=True)
        ts = iso(now_utc())
        day = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y%m%d')
        rid = f"ERR-{day}-AUTOHEAL"
        exit_code = autoheal_result.get('exit_code')
        duration_sec = autoheal_result.get('duration_sec')
        stderr_tail = (autoheal_result.get('stderr_tail') or '').strip()
        status_hint = 'success' if exit_code == 0 else 'failed'
        entry = f"""
## [{rid}] evolver-autoheal-{status_hint}

**Logged**: {ts}
**Priority**: medium
**Status**: pending
**Area**: infra

### Summary
Loop guard 触发自动自愈（连续 WARN），已执行 `node index.js run`。

### Error
```
reason={reason}
last_action_created_at={created_at}
last_action_age_min={age_min}
autoheal_exit_code={exit_code}
autoheal_duration_sec={duration_sec}
```

### Context
- Trigger: consecutive WARN >= {AUTOHEAL_WARN_THRESHOLD}
- Cooldown: {AUTOHEAL_COOLDOWN_MIN} min
- Circuit Breaker: {AUTOHEAL_FAIL_THRESHOLD} fails -> pause {AUTOHEAL_PAUSE_HOURS}h
- Script: scripts/evolver_loop_guard.py

### Suggested Fix
- 若频繁触发，优先排查 memory_graph_state/outcome 写入链路
- 若 exit_code 非 0，检查 capability-evolver 最近一次 stderr 输出

### Metadata
- Reproducible: unknown
- Related Files: memory/evolution/loop_guard_state.json, memory/evolution/loop-guard.log
- Autoheal Stderr Tail: {stderr_tail[:400] if stderr_tail else '(none)'}

---
"""
        with SELF_IMPROVING_ERRORS.open('a', encoding='utf-8') as f:
            f.write(entry)
    except Exception:
        pass


now = now_utc()
state = load_json(STATE, {}) or {}
last = (state.get('last_action') or {})
created_at = last.get('created_at')
outcome_recorded = bool(last.get('outcome_recorded', False))

age_min = None
if created_at:
    dt = parse_iso(created_at)
    if dt is not None:
        age_min = (now - dt).total_seconds() / 60.0

solid = load_json(SOLID, {}) or {}
last_solid = (solid.get('last_solidify') or {})
solid_status = ((last_solid.get('outcome') or {}).get('status'))
solid_score = ((last_solid.get('outcome') or {}).get('score'))

status = 'OK'
reason = 'loop healthy'
if not created_at:
    status = 'WARN'
    reason = 'no last_action in memory_graph_state'
elif (not outcome_recorded) and age_min is not None and age_min > WARN_AGE_MIN:
    status = 'WARN'
    reason = f'last_action outcome still false for {age_min:.1f}m (>{WARN_AGE_MIN}m)'

# rolling guard state
roll = load_json(
    GUARD_STATE,
    {
        'consecutive_warn': 0,
        'consecutive_autoheal_fail': 0,
        'autoheal_paused_until': None,
        'last_status': None,
        'last_checked_at': None,
        'last_autoheal_at': None,
        'last_autoheal_result': None,
    },
)

# backward compatibility for old state files
roll.setdefault('consecutive_autoheal_fail', 0)
roll.setdefault('autoheal_paused_until', None)

if status == 'WARN':
    roll['consecutive_warn'] = int(roll.get('consecutive_warn') or 0) + 1
else:
    roll['consecutive_warn'] = 0

roll['last_status'] = status
roll['last_checked_at'] = iso(now)

# auto-heal: consecutive WARN >= threshold and cooldown passed
last_autoheal_at = parse_iso(roll.get('last_autoheal_at'))
cooldown_ok = (
    last_autoheal_at is None
    or ((now - last_autoheal_at).total_seconds() / 60.0) >= AUTOHEAL_COOLDOWN_MIN
)

paused_until = parse_iso(roll.get('autoheal_paused_until'))
paused = paused_until is not None and now < paused_until

autoheal = {
    'triggered': False,
    'reason': None,
    'exit_code': None,
    'duration_sec': None,
    'paused': paused,
    'paused_until': iso(paused_until) if paused_until else None,
}

if status == 'WARN' and int(roll.get('consecutive_warn') or 0) >= AUTOHEAL_WARN_THRESHOLD and cooldown_ok and not paused:
    autoheal['triggered'] = True
    autoheal['reason'] = f"consecutive_warn>={AUTOHEAL_WARN_THRESHOLD}"
    t0 = time.time()
    try:
        proc = subprocess.run(
            ['/usr/bin/node', 'index.js', 'run'],
            cwd=str(EVOLVER_DIR),
            capture_output=True,
            text=True,
            timeout=240,
        )
        autoheal['exit_code'] = int(proc.returncode)
        autoheal['duration_sec'] = round(time.time() - t0, 2)
        autoheal['stdout_tail'] = (proc.stdout or '')[-800:]
        autoheal['stderr_tail'] = (proc.stderr or '')[-800:]
        roll['last_autoheal_result'] = {
            'at': iso(now_utc()),
            'exit_code': autoheal['exit_code'],
            'duration_sec': autoheal['duration_sec'],
        }
    except Exception as e:
        autoheal['exit_code'] = 999
        autoheal['duration_sec'] = round(time.time() - t0, 2)
        autoheal['stderr_tail'] = str(e)
        roll['last_autoheal_result'] = {
            'at': iso(now_utc()),
            'exit_code': 999,
            'duration_sec': autoheal['duration_sec'],
            'error': str(e),
        }
    roll['last_autoheal_at'] = iso(now_utc())

    # failure accounting + circuit breaker
    if autoheal.get('exit_code') == 0:
        roll['consecutive_autoheal_fail'] = 0
    else:
        roll['consecutive_autoheal_fail'] = int(roll.get('consecutive_autoheal_fail') or 0) + 1
        if int(roll.get('consecutive_autoheal_fail') or 0) >= AUTOHEAL_FAIL_THRESHOLD:
            pause_until = now_utc() + datetime.timedelta(hours=AUTOHEAL_PAUSE_HOURS)
            roll['autoheal_paused_until'] = iso(pause_until)
            autoheal['paused'] = True
            autoheal['paused_until'] = iso(pause_until)
            autoheal['reason'] = f"{autoheal.get('reason')} + circuit_breaker({AUTOHEAL_FAIL_THRESHOLD} fails)"

    append_autoheal_learning(autoheal, reason, created_at, round(age_min, 2) if age_min is not None else None)

elif paused:
    autoheal['reason'] = 'autoheal paused by circuit breaker'

line = {
    'ts': iso(now),
    'status': status,
    'reason': reason,
    'last_action_created_at': created_at,
    'last_action_age_min': round(age_min, 2) if age_min is not None else None,
    'outcome_recorded': outcome_recorded,
    'last_solidify_status': solid_status,
    'last_solidify_score': solid_score,
    'consecutive_warn': int(roll.get('consecutive_warn') or 0),
    'consecutive_autoheal_fail': int(roll.get('consecutive_autoheal_fail') or 0),
    'autoheal': autoheal,
}

write_json(GUARD_STATE, roll)
print(json.dumps(line, ensure_ascii=False))

sys.exit(0 if status == 'OK' else 2)


