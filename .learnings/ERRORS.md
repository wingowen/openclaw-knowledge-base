# Errors Log

Command failures, exceptions, and unexpected behaviors.

---

## [ERR-20260314-001] missing-rg-binary

**Logged**: 2026-03-14T07:51:04.577698+08:00
**Priority**: low
**Status**: pending
**Area**: infra

### Summary
执行代码检索时使用 `rg` 失败，当前环境未安装 ripgrep。

### Error
```
/bin/bash: line 1: rg: command not found
```

### Context
- Operation: 检索 capability-evolver/self-improving-agent 代码路径
- Fallback: 改用 `grep -RIn` 完成检索

### Suggested Fix
在需要高性能检索时优先检测 `rg` 可用性，不可用则自动回退 `grep -RIn`。

### Metadata
- Reproducible: yes
- Related Files: none

---
