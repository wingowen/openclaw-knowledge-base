# 多 Agent 架构方案：管理者 + 执行者

> 生成日期：2026-03-17
> 状态：📋 方案设计

---

## 一、当前架构评估

### 1.1 现状

| 项目 | 当前状态 |
|------|---------|
| Agent 数量 | 1 个（`main`） |
| 工作空间 | `~/.openclaw/workspace` |
| 模型 | `openrouter/hunter-alpha`（主）+ 多个免费回退 |
| 会话方式 | 所有任务在同一会话中处理 |
| 子代理 | 通过 `sessions_spawn` 临时创建，无持久化 |

### 1.2 现有痛点

| 痛点 | 影响 |
|------|------|
| 上下文膨胀 | 股票分析、英语学习、日常对话混在同一会话，token 消耗大 |
| 任务阻塞 | 长时间任务（如数据抓取）阻塞主对话 |
| 角色混乱 | 同一个 agent 既要理解需求又要执行代码，prompt 冲突 |
| 记忆污染 | 不同项目的历史混在一起，召回精度下降 |
| 无法并行 | 多个任务只能串行处理 |

---

## 二、目标架构设计

### 2.1 架构概览

```
                    ┌─────────────────────────────────────┐
                    │           Wingo (用户)               │
                    └──────────────┬──────────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────────────┐
                    │      🧠 管理者 Agent (Manager)       │
                    │                                     │
                    │  • 理解用户意图 & 任务拆解            │
                    │  • 分配任务给执行者                   │
                    │  • 聚合结果 & 反馈用户               │
                    │  • 维护长期记忆 & 知识库              │
                    │  • 对话 & 问答（不执行重活）           │
                    │                                     │
                    │  工作空间: ~/.openclaw/workspace      │
                    │  模型: hunter-alpha (高质量)           │
                    └──────────────┬──────────────────────┘
                                   │ sessions_spawn / sessions_send
                    ┌──────────────┼──────────────────────┐
                    │              │                       │
                    ▼              ▼                       ▼
        ┌───────────────┐ ┌───────────────┐ ┌───────────────────┐
        │ 💻 代码执行者  │ │ 📊 数据执行者  │ │ 🔍 研究执行者      │
        │ (Coder)       │ │ (Data)        │ │ (Researcher)      │
        │               │ │               │ │                   │
        │ • 写代码       │ │ • 股票数据抓取 │ │ • 网页搜索         │
        │ • 调试        │ │ • 数据清洗     │ │ • 信息提取         │
        │ • 部署        │ │ • 报告生成     │ │ • 总结归纳         │
        │ • Git 操作    │ │ • Notion 同步  │ │ • 翻译            │
        │               │ │               │ │                   │
        │ workspace:    │ │ workspace:    │ │ workspace:        │
        │ workspace-    │ │ workspace-    │ │ workspace-        │
        │ coder         │ │ data          │ │ researcher        │
        │               │ │               │ │                   │
        │ 模型:         │ │ 模型:         │ │ 模型:              │
        │ gpt-5.3-codex │ │ free 模型     │ │ free 模型          │
        │ (代码专用)     │ │ (成本优化)    │ │ (成本优化)         │
        └───────────────┘ └───────────────┘ └───────────────────┘
```

### 2.2 角色定义

#### 🧠 管理者 Agent (Manager)

| 属性 | 配置 |
|------|------|
| **ID** | `main` |
| **职责** | 用户交互、任务理解、拆解、分配、结果聚合、记忆管理 |
| **工作空间** | `~/.openclaw/workspace`（现有） |
| **模型** | `openrouter/hunter-alpha`（高质量对话） |
| **工具权限** | 全部（但把重活委托给执行者） |
| **记忆** | 完整的 MEMORY.md、memory/、knowledge-base/ |

**核心行为**：
- 收到复杂任务 → 拆解 → spawn 执行者 → 监控进度 → 汇总结果
- 日常对话、简单问答直接处理，不劳烦执行者
- 维护知识库和长期记忆
- 决定何时使用哪个执行者

#### 💻 代码执行者 (Coder)

| 属性 | 配置 |
|------|------|
| **ID** | `coder` |
| **职责** | 代码编写、调试、测试、Git 操作、项目构建 |
| **工作空间** | `~/.openclaw/workspace-coder` |
| **模型** | `openai/gpt-5.3-codex`（代码专用模型） |
| **工具权限** | exec, read, write, edit（无 browser、message 等） |
| **记忆** | 仅项目相关文件，无用户私人记忆 |

**触发条件**：
- 用户说"帮我写代码"、"修复 bug"、"重构"、"部署"
- 涉及 Git 操作、项目构建
- 需要运行测试或脚本

#### 📊 数据执行者 (Data)

| 属性 | 配置 |
|------|------|
| **ID** | `data` |
| **职责** | 数据抓取、清洗、分析、报告生成、Notion 同步 |
| **工作空间** | `~/.openclaw/workspace-data` |
| **模型** | 免费模型（stepfun/step-3.5-flash:free） |
| **工具权限** | exec, read, write, feishu_doc, web_fetch |
| **记忆** | 股票分析相关脚本和配置 |

**触发条件**：
- 股票数据抓取、市场报告生成
- Notion/飞书文档同步
- 批量数据处理

#### 🔍 研究执行者 (Researcher)

| 属性 | 配置 |
|------|------|
| **ID** | `researcher` |
| **职责** | 网页搜索、信息提取、内容总结、翻译 |
| **工作空间** | `~/.openclaw/workspace-researcher` |
| **模型** | 免费模型（成本优化） |
| **工具权限** | web_search, web_fetch, read, write |
| **记忆** | 无长期记忆（临时任务） |

**触发条件**：
- "帮我查一下..."、"搜索..."、"总结这个网页"
- 翻译任务
- 信息调研

---

## 三、配置方案

### 3.1 openclaw.json 配置

```json5
{
  agents: {
    list: [
      {
        id: "main",
        default: true,
        name: "管理者",
        workspace: "~/.openclaw/workspace",
        // 管理者使用高质量模型
        model: "openrouter/hunter-alpha",
      },
      {
        id: "coder",
        name: "代码执行者",
        workspace: "~/.openclaw/workspace-coder",
        // 代码专用模型
        model: "openai/gpt-5.3-codex",
        // 限制工具权限
        tools: {
          allow: [
            "read", "write", "edit", "exec",
            "sessions_send", "session_status"
          ],
          deny: ["browser", "message", "tts", "feishu_doc", "feishu_wiki"]
        },
        // 沙箱模式（可选）
        sandbox: {
          mode: "off"  // coder 需要完整系统访问
        }
      },
      {
        id: "data",
        name: "数据执行者",
        workspace: "~/.openclaw/workspace-data",
        // 免费模型，成本优化
        model: "stepfun/step-3.5-flash:free",
        tools: {
          allow: [
            "read", "write", "edit", "exec",
            "feishu_doc", "feishu_drive", "web_fetch",
            "sessions_send", "session_status"
          ],
          deny: ["browser", "message", "tts"]
        }
      },
      {
        id: "researcher",
        name: "研究执行者",
        workspace: "~/.openclaw/workspace-researcher",
        model: "qwen/qwen3-next-80b-a3b-instruct:free",
        tools: {
          allow: [
            "read", "write", "web_search", "web_fetch",
            "sessions_send", "session_status"
          ],
          deny: ["exec", "browser", "message", "tts", "feishu_doc"]
        }
      }
    ]
  },
  
  // 子代理配置（管理者 spawn 执行者时使用）
  subagents: {
    allow: ["coder", "data", "researcher"]
  },
  
  // Agent 间通信（可选）
  tools: {
    agentToAgent: {
      enabled: true,
      allow: ["main", "coder", "data", "researcher"]
    }
  }
}
```

### 3.2 工作空间初始化

```bash
# 创建各执行者的工作空间
openclaw agents add coder
openclaw agents add data
openclaw agents add researcher

# 或手动创建
mkdir -p ~/.openclaw/workspace-coder
mkdir -p ~/.openclaw/workspace-data
mkdir -p ~/.openclaw/workspace-researcher

# 为每个执行者创建基础文件
for agent in coder data researcher; do
  workspace=~/.openclaw/workspace-$agent
  
  # AGENTS.md - 执行者专用
  cat > $workspace/AGENTS.md << 'EOF'
# 执行者 Agent

你是专门的执行者。你的职责是：
1. 接收管理者分配的任务
2. 高效执行
3. 返回结构化结果

不要与用户直接对话。所有结果通过 sessions_send 返回给管理者。
EOF

  # SOUL.md - 最小化
  cat > $workspace/SOUL.md << 'EOF'
# SOUL.md

你是高效的执行者。专注任务，不说废话。
完成后返回清晰的结果摘要。
EOF

  # IDENTITY.md
  echo "# IDENTITY.md\n- Name: $agent\n- Role: 执行者" > $workspace/IDENTITY.md
done
```

---

## 四、操作指南

### 4.1 管理者如何分配任务

#### 方式一：sessions_spawn（推荐，一次性任务）

```python
# 管理者的 internal thought：
# 用户要求写一个股票数据抓取脚本 → 分配给 coder

sessions_spawn(
  task="写一个 Python 脚本，从腾讯财经 API 抓取 A 股实时数据，保存为 JSON。要求：\n1. 支持传入股票代码列表\n2. 输出包含价格、涨跌幅、成交量\n3. 保存到 /root/.openclaw/workspace/data/ 目录",
  runtime="subagent",
  label="stock-fetcher",
  model="openai/gpt-5.3-codex"  # 覆盖为代码模型
)
```

#### 方式二：sessions_send（持久会话，多轮交互）

```python
# 适用于需要多轮对话的复杂任务
sessions_send(
  sessionKey="agent:data:stock-analysis",
  message="开始今日 A 股数据抓取，完成后通知我"
)
```

### 4.2 任务分配决策树

```
用户请求
    │
    ├─ 简单问答/聊天 ──────────→ 管理者直接回答
    │
    ├─ 需要写代码？
    │   ├─ 是 ─────────────────→ spawn coder
    │   └─ 否 ↓
    │
    ├─ 需要抓取/处理数据？
    │   ├─ 是 ─────────────────→ spawn data
    │   └─ 否 ↓
    │
    ├─ 需要搜索/调研？
    │   ├─ 是 ─────────────────→ spawn researcher
    │   └─ 否 ↓
    │
    └─ 复杂多步骤任务 ──────────→ 拆解 → 多个 spawn
```

### 4.3 执行者返回结果格式

执行者应返回结构化结果，方便管理者聚合：

```markdown
## 任务完成 ✅

**任务**: [任务描述]
**状态**: 成功 | 失败 | 部分完成

### 结果
- [具体产出 1]
- [具体产出 2]

### 产出文件
- `/path/to/file1.py`
- `/path/to/file2.json`

### 注意事项
- [如有问题或建议]
```

### 4.4 成本优化策略

| Agent | 模型 | 原因 |
|-------|------|------|
| 管理者 | hunter-alpha | 用户交互需要高质量 |
| 代码执行者 | gpt-5.3-codex | 代码任务需要强推理 |
| 数据执行者 | 免费模型 | 数据抓取是确定性任务 |
| 研究执行者 | 免费模型 | 搜索总结不需要最强模型 |

**预估节省**：60-70% 的 token 消耗从高价模型转移到免费模型

---

## 五、实施步骤

### Phase 1：基础搭建（Day 1）

- [ ] 创建 `coder`、`data`、`researcher` 三个 agent
- [ ] 初始化各工作空间和基础文件
- [ ] 更新 `openclaw.json` 配置
- [ ] 测试 `sessions_spawn` 到各执行者

### Phase 2：工作流适配（Day 2-3）

- [ ] 将现有脚本迁移到对应执行者工作空间
  - 股票相关 → `workspace-data`
  - NCE 相关 → `workspace-data`
  - 代码项目 → `workspace-coder`
- [ ] 为管理者编写任务分配 prompt 模板
- [ ] 设置执行者的基础 AGENTS.md

### Phase 3：优化迭代（Week 2）

- [ ] 监控各执行者的 token 使用和成本
- [ ] 根据实际效果调整模型分配
- [ ] 添加更多专项执行者（如 `feishu`、`notion`）
- [ ] 优化管理者任务拆解逻辑

---

## 六、注意事项

### 6.1 安全边界

| 风险 | 缓解措施 |
|------|---------|
| 执行者访问用户私人数据 | 执行者工作空间不含 MEMORY.md、USER.md |
| 执行者发送外部消息 | deny message 工具，只能通过管理者发送 |
| 成本失控 | 执行者优先使用免费模型 |
| 任务无限循环 | 设置 `runTimeoutSeconds` |

### 6.2 记忆隔离

```
~/.openclaw/workspace/           # 管理者：完整记忆
├── MEMORY.md                     # ✅ 长期记忆
├── memory/                       # ✅ 每日记录
├── knowledge-base/               # ✅ 知识库
└── ...

~/.openclaw/workspace-coder/     # 代码执行者：无用户记忆
├── AGENTS.md                     # 任务指南
└── projects/                     # 代码项目

~/.openclaw/workspace-data/      # 数据执行者：无用户记忆
├── AGENTS.md
└── scripts/                      # 数据脚本

~/.openclaw/workspace-researcher/ # 研究执行者：无用户记忆
├── AGENTS.md
└── cache/                        # 临时搜索缓存
```

### 6.3 回退机制

如果执行者失败，管理者应：
1. 捕获错误信息
2. 尝试用其他模型重试
3. 或直接自己处理（简单任务）
4. 记录失败原因到 memory

---

## 七、监控与调试

### 查看所有 Agent

```bash
openclaw agents list --bindings
```

### 查看执行者会话

```bash
# 在管理者中
sessions_list(kinds=["subagent"], activeMinutes=60)
```

### 查看子代理历史

```bash
sessions_history(sessionKey="agent:coder:xxx", limit=20)
```

### 成本追踪

```bash
# 各 agent 的使用情况
session_status(sessionKey="agent:main:xxx")
session_status(sessionKey="agent:coder:xxx")
```

---

## 八、总结

| 维度 | 当前（单 Agent） | 目标（管理者 + 执行者） |
|------|-----------------|----------------------|
| 角色 | 一人饰多角 | 专注分工 |
| 成本 | 全用高价模型 | 按需分配模型 |
| 并行 | 串行 | 可并行 |
| 记忆 | 混杂 | 隔离清晰 |
| 扩展 | 困难 | 添加新执行者即可 |

**核心原则**：管理者负责「思考」，执行者负责「干活」。
