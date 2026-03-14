# Learnings

Corrections, insights, and knowledge gaps captured during development.

**Categories**: correction | insight | knowledge_gap | best_practice
**Areas**: frontend | backend | infra | tests | docs | config
**Statuses**: pending | in_progress | resolved | wont_fix | promoted | promoted_to_skill

## Status Definitions

| Status | Meaning |
|--------|---------|
| `pending` | Not yet addressed |
| `in_progress` | Actively being worked on |
| `resolved` | Issue fixed or knowledge integrated |
| `wont_fix` | Decided not to address (reason in Resolution) |
| `promoted` | Elevated to CLAUDE.md, AGENTS.md, or copilot-instructions.md |
| `promoted_to_skill` | Extracted as a reusable skill |

## Skill Extraction Fields

When a learning is promoted to a skill, add these fields:

```markdown
**Status**: promoted_to_skill
**Skill-Path**: skills/skill-name
```

Example:
```markdown
## [LRN-20250115-001] best_practice

**Logged**: 2025-01-15T10:00:00Z
**Priority**: high
**Status**: promoted_to_skill
**Skill-Path**: skills/docker-m1-fixes
**Area**: infra

### Summary
Docker build fails on Apple Silicon due to platform mismatch
...
```

---


## [LRN-20260314-001] best_practice

**Logged**: 2026-03-14T07:51:04.577698+08:00
**Priority**: medium
**Status**: pending
**Area**: infra

### Summary
针对长期记忆/历史上下文问题，先做短查询 memory_search，再给出结论。

### Details
在长问题或自动召回为空时，直接回答容易遗漏历史事实。先用 2-5 关键词执行 memory_search，可显著降低上下文缺失和误判风险。

### Suggested Action
把“先 memory_search(短查询)”作为历史相关问题的固定前置步骤。

### Metadata
- Source: conversation
- Related Files: none
- Tags: memory, workflow, reliability

---
