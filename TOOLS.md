# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Notion

- **股票分析数据库**：`31f67b21-8207-8035-bd60-ea2d04be7798` (Openclaw 工作空间)
  - **market_analysis 页面**: `31f67b2182078136a0b4fc5b90700791` (子页面创建目标)
  - **prompt 模板页面**: `32067b21-8207-8023-a7e7-c2be162b84f1`
  - **Prompt blocks**:
    - Standard: `32067b21-8207-80cf-8fdf-c08f4d0f8595`
    - Simple: `32067b21-8207-80eb-9669-dfa794dfe792`
    - Advanced: `32067b21-8207-8061-bdca-ec8618855930`
  - **索引页面**:
    - 🧠 记忆仓库索引: `32067b21-8207-813d-be36-cd073e90b59c`
    - 🛠️ 工具技能与脚本索引: `32067b21-8207-8101-8942-d27e9c1234ec`
  - URL 示例: https://www.notion.so/Openclaw-31f67b2182078035bd60ea2d04be7798
  - 用途：A股复盘报告、记忆存储、工具索引
  - 注意：需确保 Integration 已共享到此工作空间

### SSH

（待补充）

### TTS

（待补充）

### Coding Agent

- **优先使用**：`opencode`（版本 1.2.17）
- **可用备选**：`codex`（gpt-5.3-codex）、`claude`（有 root 权限限制）
- **注意**：
  - `codex` 在 WSL2 中 git worktree 路径可能异常，不影响功能
  - `claude --dangerously-skip-permissions` 在 root 环境下被禁用，用 `--print --permission-mode bypassPermissions` 代替
  - `opencode` 用法：`opencode run 'prompt'`（PTY 模式推荐）
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.
