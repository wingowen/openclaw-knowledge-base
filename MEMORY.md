# 🧠 MEMORY.md - Your Long-Term Memory

This is your curated memory - the distilled essence of what's worth keeping long-term.

## 用户偏好

- 用户希望在不产生歧义的情况下，回答尽量用中文
- **子代理任务通知**：当开启子代理任务时，让子代理每完成一件子任务就发送通知，保持进度可见

---

## 📚 OpenClaw 记忆仓库

**创建时间**: 2026-02-12

### 目录结构

```
knowledge-base/
├── README.md              # 知识库索引
├── 01-persona/            # 身份与角色定义
├── 02-projects/           # 项目文档
├── 03-tasks/              # 任务追踪
├── 04-learnings/          # 学习与经验
└── 05-archive/            # 归档资料
```

### 与现有系统的关系

| 系统 | 用途 | 加载时机 |
|------|------|----------|
| `memory/YYYY-MM-DD.md` | 每日原始日志 | 每天开始时 |
| `MEMORY.md` | 长期精选记忆 | 主会话时 |
| `knowledge-base/` | **结构化知识库** | 特定任务时检索 |

### 已录入内容

- 英语学习平台项目文档
- GitHub 工具集配置指南

---

## 📈 股市分析自动化系统

**功能**: 自动化数据收集 → 人工分析 → Notion 同步

**核心脚本**:
- `prepare_market_report.py`: 获取实时数据 + 组装 prompt
- `market_data.py`: 腾讯财经 API 数据源
- `sync_to_notion_full.py`: Markdown → Notion 完整同步（支持表格）

**流程**:
1. 运行 `prepare_market_report.py --date YYYY-MM-DD`
2. 基于 prompt 数据人工撰写 8 章节报告
3. 保存为 `market_report_YYYY-MM-DD.md`
4. 运行 `sync_to_notion_full.py` 同步到 Notion

**Notion 目标页面**: `market_analysis` (31f67b2182078136a0b4fc5b90700791)

---

## 📊 A股周期股波段监控系统

**位置**: `/root/.openclaw/workspace/cycle_stock_monitor/`

**标的池**:
- 招商银行 (600036) - 银行
- 宁波银行 (002142) - 银行
- 紫金矿业 (601899) - 有色金属
- 江西铜业 (600362) - 有色金属
- 中国平安 (601318) - 保险

**用户配置**:
- 投资周期: 3-6 个月波段
- 风险偏好: 平衡型 (最大回撤 ≤15%)
- 仓位规划: 单只 ≤20%, 整体 ≤50%
- 持仓状态: 空仓

**核心规则**:
- **买入**: 3 档 based on 5 年估值分位 (PB/PE)
  - 档位 1: ≤20% (安全底仓 35%)
  - 档位 2: 20-40% (确认加仓 35%)
  - 档位 3: 40-60% (趋势加仓 30%)
- **止盈**: 3 档 based on 估值修复空间
  - 分批止盈: 60-70% (卖 30%)
  - 核心止盈: 70-90% (卖 40-50%)
  - 清仓止盈: ≥90% (卖 100%)
- **止损**: 刚性 9% (基于平衡型 15% 最大回撤)
- **强制卖出**: 行业景气度拐点、重大利空、估值泡沫

**监控频率**:
- 盘中: 每 5 分钟检查
- 收盘: 生成完整日报
- 触发: 即时飞书通知

**启动**:
```bash
cd /root/.openclaw/workspace/cycle_stock_monitor
pip install -r requirements.txt
python3 test_system.py        # 测试
python3 monitor_engine.py     # 持续监控
python3 monitor_engine.py --once   # 单次检查
python3 monitor_engine.py --report # 生成日报
```

**测试结果 (2026-03-12)**:
```
招商银行: 当前39.50 | 买入档31-36 | 止盈档41-51
宁波银行: 当前31.15 | 买入档23-28 | 止盈档32-38
紫金矿业: 当前37.24 | 买入档10-14 | 止盈档39-45 (⚠️估值97%已高估)
江西铜业: 当前52.08 | 买入档17-22 | 止盈档55-63 (⚠️估值96%已高估)
中国平安: 当前62.55 | 买入档41-50 | 止盈档63-42 (接近止盈)
```

**注意事项**:
- 飞书 webhook 需在 `config.py` 中配置
- 估值分位基于价格历史，应接入 PB/PE 基本面数据
- 行业景气度需集成问财/同花顺 API

---

## 📚 新概念英语静态数据仓库

**位置**: `/root/.openclaw/workspace/nce-data/`

**设计**: 纯静态 JSON，无需数据库，可版本控制

**目录**:
```
nce-data/
├── data/
│   ├── book1/  (96课)
│   ├── book2/  (96课)
│   ├── book3/  (60课)
│   └── book4/  (96课)
└── scripts/fetch.py
```

**数据格式**:
```json
{
  "lesson_id": "3-001",
  "title": "A puma at large",
  "english_sentences": [...],
  "chinese_sentences": [...],
  "english_raw": "...",
  "chinese_raw": "..."
}
```

**命令**:
```bash
python3 scripts/fetch.py fetch 3-001    # 抓取单课
python3 scripts/fetch.py batch 3 1 60  # 批量抓取第三册
python3 scripts/fetch.py list 3        # 列出已有
```

**当前进度**: 第三册已完成 10 课 (3-001 ~ 3-010)，含 B.C. 缩写修复

---

## ⚙️ 技术基础设施

### MCP 服务器配置

**mcp_query_table**: pip 全局包，但硬编码 Windows Chrome 路径，WSL2 不可用

**自定义 MCP 服务器** (`scripts/mcp_market_data_server.py`):
- 封装 `market_data.py` 为 SSE 接口
- 运行: `python3 scripts/mcp_market_data_server.py --transport sse --port 8000`
- Endpoint: `http://127.0.0.1:8000/sse`
- 依赖: `fastmcp`

### GitHub 工具集

**已安装**:
- `gh` (GitHub CLI) 2.86.0
- `hub` 2.14.2

**脚本**:
- `github_repo_creator.sh` - 交互式创建仓库
- `README_github_tools.md` - 使用指南

**用法**: `gh auth login` → `gh repo create my-repo --public`

### OpenRouter 免费模型限流处理 (2026-03-10)

**问题**: 所有免费模型返回 "API rate limit reached"

**解决**:
1. `freeride auto` - 自动配置最佳模型 + 5 个回退
2. 重启 Gateway
3. `freeride-watcher --daemon` - 后台监控轮换
4. `freeride-watcher --rotate` - 手动触发

**当前主模型**: `stepfun/step-3.5-flash:free` ✅

**经验**: 多模型回退 + 自动轮换可缓解限流；集体限流时等待几分钟即可恢复

---

## 📋 标准流程与模板

### 股市分析报告结构 (8 章节)

1. **昨日预测复盘** - 验证预判准确性 (✅/⚠️/❌)
2. 今日核心行情总览 (指数、量能、涨跌分布)
3. 盘面结构深度拆解 (主线、支线、领跌)
4. 资金与情绪面分析 (北向、主力、情绪周期)
5. 核心风险与机会点 (🔴 风险 + 🟢 机会)
6. 明日行情预判 (指数支撑/压力、板块延续性)
7. 实操策略 (仓位、方向、情景预案)
8. 总结与关注要点

**原则**: 数据驱动，核心结论加粗，包含风险提示

### Notion 同步规范

**触发**: 所有股市、行情、复盘、预判类分析

**目标**: `market_analysis` 父页面下创建子页面

**命名**: `YYYY-MM-DD A股深度复盘与N+1预判`

**内容**: 完整 8 章节报告 (Markdown → Notion blocks)

**工具**: `sync_to_notion_full.py` (支持表格、标题、列表、粗体)

---

## 🎯 用户偏好总结

- 回答尽量用中文 (无歧义时)
- 子代理任务: 每完成一件子任务发送通知
- 汇率查询: 同时显示 USD/CNY/JPY/EUR/HKD 中间价
- 天气: 简洁模式 (默认)
- 格式: 表格渲染、标题层级、列表格式需完整
- 不自动调用 LLM 生成分析报告 (人工/助理手动撰写)
- **文档同步偏好**：以后所有生成的文档默认同步到 Notion（除非用户明确说不同步）
- **模型使用偏好**：可按任务难度切换免费模型执行（简单任务优先免费模型，复杂任务可用更强模型）

---

## 📋 Todo List

### 新概念英语第三册录入任务

**状态**: ✅ 数据问题已修复（2026-02-11）

**数据源**: https://newconceptenglish.com/index.php?id=nce-3

**已创建资源**:
- 标签: `新概念英语第三册` (id=6, color=#00247D)

**已修复的问题** (2026-02-11):

1. ✅ **删除重复文章**：id=17~24 已删除（保留了 id=7~16）

2. ✅ **修复 B.C. 切分逻辑**：
   - 修改了 `fetch_nce3_lesson.py` 的 `split_sentences()` 函数
   - 使用占位符保护缩写（B.C., A.D., Mr., Mrs., Dr. 等）
   - 智能区分 "B.C. until"（句中）和 "B.C. Its"（句子边界）

3. ✅ **重新录入 3-003 ~ 3-010**：删除旧句子，重新抓取录入

**录入进度**:
- 3-001 ~ 3-010: ✅ 已完成（id=7~16）
- 3-011 ~ 3-060: 待录入

**当前文章列表**:
| 课程 | 文章ID | 句子数 |
|------|--------|--------|
| 3-001 A puma at large | 7 | 13 |
| 3-002 Thirteen equals one | 8 | 14 |
| 3-003 An unknown goddess | 9 | 17 |
| 3-004 The double life of Alfred Blogds | 10 | 14 |
| 3-005 The facts | 11 | 12 |
| 3-006 Smash-and-grab | 12 | 16 |
| 3-007 Mutilated ladies | 13 | 16 |
| 3-008 A famous monastery | 14 | 15 |
| 3-009 Flying cats | 15 | 19 |
| 3-010 The loss of the Titanic | 16 | 14 |

**录入脚本位置**:
- 抓取+切分: `/root/.openclaw/workspace/scripts/fetch_nce3_lesson.py`
- 录入数据库: `/root/.openclaw/workspace/scripts/insert_lesson.py`
- 临时数据: `/root/.openclaw/workspace/scripts/lesson_*.json`

**执行命令** (继续时使用):
```bash
# 1. 抓取单课
python3 scripts/fetch_nce3_lesson.py 3-002

# 2. 创建文章+关联标签 (需要手动改脚本或curl)
# 3. 录入句子
python3 scripts/insert_lesson.py lesson_3-002.json <article_id>
```

**数据结构**:
- 每课 = 1篇文章 (articles表)
- 文章关联到标签 (article_tags表)
- 句子包含中英文 (sentences表, extensions.translation字段)

**网站课程列表** (共60课):
```
3-001 A puma at large ✅
3-002 Thirteen equals one
3-003 An unknown goddess
... (省略)
3-060 Too early and too late
```

---

## MCP Server 配置

### mcp_query_table (金融表格查询)

**位置**：pip 全局包 `/usr/local/lib/python3.11/dist-packages/mcp_query_table/`

**状态**：⚠️ 该工具硬编码 Windows Chrome 路径，在 WSL2 环境下不可用

**替代方案**：直接使用 `scripts/market_data.py`（腾讯财经 API）获取实时数据

### mcp_market_data_server.py (自定义 MCP 服务器)

**位置**：`/root/.openclaw/workspace/scripts/mcp_market_data_server.py`

**用途**：将 `market_data.py` 封装为 MCP 接口（可选）

**运行**：
```bash
python3 scripts/mcp_market_data_server.py --transport sse --port 8000
```

**依赖**：`fastmcp`

**Endpoint**（运行后）：`http://127.0.0.1:8000/sse`

---

## 项目：英语学习平台 (Supabase)

### 已修复的问题

**2026-02-11**: 沉浸式模式句子自动切换失败
- 原因: `ImmersiveSpelling.jsx` 的 useEffect 依赖 `isCompleted` 导致定时器被清除
- 修复: 使用 `useRef(isCompletedRef)` 追踪完成状态
- 文件: `/home/wingo/code/sentences-dictation/src/components/ImmersiveSpelling.jsx`

### 项目概述
一个英语句子学习平台，使用 Supabase 作为后端数据库。

### 数据库结构
| 表名 | 用途 | 关键字段 |
|------|------|----------|
| `articles` | 文章 | id, title, description, source_url, total_sentences |
| `sentences` | 句子 | id, article_id, content, sequence_order, is_active |
| `tags` | 标签 | id, name, color |
| `article_tags` | 文章-标签关联 | article_id, tag_id |
| `sentence_audios` | 句子音频 | id, sentence_id, audio_url, speaker, speed |

### 现有文章
- id=1: 简单句练习
- id=2: 新概念英语第一册
- id=7: 3-001 A puma at large (新概念英语第三册)

### 现有标签
- id=6: 新概念英语第三册 (#00247D)

### 本地开发服务
| 服务 | 地址 | 说明 |
|------|------|------|
| Netlify Dev | http://localhost:8888 | 主应用（用户端） |
| Admin Vite | http://localhost:3000 | 管理后台 |

项目路径: `/home/wingo/code/sentences-dictation/`

### 环境配置
配置文件位置: `.env.supabase`
```
SUPABASE_URL=https://gtcnjqeloworstrimcsr.supabase.co
SUPABASE_SERVICE_ROLE_KEY=...  # Admin 权限，用于添加/修改数据
SUPABASE_ANON_KEY=...          # 只读权限，用于查询
MCP_API_KEY=...                # MCP 服务使用
```

### 技术要点

#### IPv6 兼容性
- 当前运行环境（WSL2）**不支持 IPv6**
- Supabase 通过 Cloudflare CDN 同时支持 IPv4 和 IPv6
- 解决方案：请求时强制使用 IPv4
  - curl: `curl -4 ...`
  - Node.js: 设置 `dns` 模块优先 IPv4

#### API 操作示例
```bash
# 查询文章
curl -4 "$SUPABASE_URL/rest/v1/articles?select=id,title" \
  -H "apikey: $SUPABASE_ANON_KEY"

# 添加句子（需要 service_role_key）
curl -4 -X POST "$SUPABASE_URL/rest/v1/sentences" \
  -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -H "Prefer: return=representation" \
  -d '{"article_id": 7, "content": "句子内容", "sequence_order": 1, "extensions": {"translation": "中文翻译"}}'
```

### 自动化测试方式

#### 启动本地服务
```bash
cd /home/wingo/code/sentences-dictation
netlify dev --port 8888
```

#### Playwright 自动化测试脚本
测试脚本目录: `/root/.openclaw/workspace/`

**关键发现：**
- 标签选择是 `<select>` 下拉框，不是按钮
- 文章选择也是 `<select>` 下拉框
- 练习页面的输入框：**每个输入框对应一个单词**

**完整测试流程：**
```javascript
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  // 1. 打开首页
  await page.goto('http://localhost:8888', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);

  // 2. 点击"在线课程"
  await page.locator('button:has-text("在线课程")').click();
  await page.waitForTimeout(3000);

  // 3. 选择标签（select 下拉框）
  await page.locator('select').first().selectOption({ label: '新概念英语第三册' });
  await page.waitForTimeout(2000);

  // 4. 选择文章（第二个 select 下拉框）
  const selects = await page.locator('select').all();
  await selects[1].selectOption({ label: '3-001 A puma at large (13句)' });
  await page.waitForTimeout(2000);

  // 5. 点击开始练习
  await page.locator('button:has-text("开始练习")').click();
  await page.waitForTimeout(3000);

  // 6. 输入答案（每个输入框一个单词）
  const sentence = 'Pumas are large, cat-like animals which are found in America.';
  const words = sentence.split(/\s+/);  // 按空格拆分
  const inputs = await page.locator('input[type=text]').all();

  for (let i = 0; i < Math.min(words.length, inputs.length); i++) {
    await inputs[i].fill(words[i]);
    await page.waitForTimeout(300);
  }

  // 7. 截图
  await page.screenshot({ path: 'result.png', fullPage: true });

  await browser.close();
})();
```

**注意事项：**
- 服务器需要先启动：`netlify dev --port 8888`
- 截图需要安装中文字体：`apt-get install fonts-noto-cjk`
- 飞书发送图片需要先上传获取 image_key

### 🚨 OpenRouter 免费模型限流事件 (2026-03-10)

**问题**：连续遇到 "API rate limit reached" 错误，所有免费模型均无法使用。

**已采取的措施**:
1. ✅ 运行 `freeride auto` 自动配置最佳免费模型 + 5个回退
2. ✅ 重启 Gateway 使配置生效
3. ✅ 启动 `freeride-watcher --daemon` 自动监控轮换
4. ✅ 手动触发轮换：`freeride-watcher --rotate`

**轮换历史**:
- 从 nvidia/nemotron-3-nano-30b-a3b:free 开始
- 第一次轮换到 qwen/qwen3-vl-30b-a3b-thinking
- 当前主模型：**stepfun/step-3.5-flash:free** ✅

**解决结果**：
- 自动轮换成功找到可用模型，限流问题已解决！
- watcher 继续运行，未来遇到限流会自动切换

**经验总结**：
- OpenRouter 免费模型确实存在限流，但通过多模型回退 + 自动轮换可以缓解
- 遇到集体限流时，手动 `--rotate` 或等待几分钟即可恢复
- 如需更高稳定性，考虑付费模型或自托管本地模型


### GitHub 仓库创建工具安装

**状态**: ✅ 完成 (11:22-11:33 GMT+8)

**已安装工具**:
1. **GitHub CLI (gh)** - 版本 2.86.0
   - 安装路径: `/usr/local/bin/gh`
   - 功能: GitHub 官方命令行工具

2. **hub** - 版本 2.14.2
   - 安装路径: `/usr/local/bin/hub`
   - 功能: GitHub 的增强命令行工具

3. **curl** - 版本 7.88.1 (已预装)
   - 功能: 用于直接调用 GitHub API

**创建的文件**:
- `github_repo_creator.sh` - 交互式脚本，支持多种方式创建 GitHub 仓库
- `README_github_tools.md` - 详细使用说明和配置指南
- `test_github_tools.sh` - 快速测试脚本
- `github_examples.md` - 使用示例和最佳实践

**使用方法**:
```bash
# 首次使用
gh auth login

# 创建仓库
gh repo create my-repo --public

# 或使用交互式脚本
./github_repo_creator.sh
```

**注意事项**:
- 首次使用前必须进行 GitHub 身份验证 (`gh auth login`)
- 仓库名称限制: 只能包含字母、数字、下划线和连字符
- 创建私有仓库可能需要付费账户

---

---

## 📈 股市分析生成策略（2026-03-11 更新）

### 核心原则
**不自动调用 LLM** → 由助理（我）手动完成报告生成。脚本只负责数据准备。

### 工作流程

```
┌─────────────────────────────────────┐
│  1. 数据收集（自动化脚本）             │
│  python3 scripts/prepare_market_report.py │
│     - 从腾讯财经获取实时指数           │
│     - 读取 Notion prompt 模板         │
│     - 填充动态变量 + 格式化数据        │
│     - 输出完整 prompt 到 stdout 或文件  │
└───────────────┬─────────────────────┘
                │ 生成 prompt.txt
                ▼
┌─────────────────────────────────────┐
│  2. 报告生成（人工/助理）             │
│  我拿到 prompt 后：                   │
│     - 基于真实数据进行分析             │
│     - 补充量能、资金等估算信息         │
│     - 撰写 7 章节完整报告              │
│     - 手动调用 Notion API 或直接粘贴   │
└───────────────┬─────────────────────┘
                │ 生成报告内容
                ▼
┌─────────────────────────────────────┐
│  3. 同步到 Notion                    │
│  创建子页面：                        │
│  {YYYY-MM-DD} A股深度复盘与{N+日}预判 │
│  位置：market_analysis 父页面下       │
└─────────────────────────────────────┘
```

### 报告结构（8章节标准格式）

1. **昨日预测复盘** - 验证前一天的预判准确性（自2026-03-12起强制包含）
2. 今日核心行情总览
3. 盘面结构深度拆解
4. 资金与情绪面分析
5. 核心风险与机会点
6. 明日行情预判
7. 实操策略
8. 总结与关注要点

**复盘原则**：
- ✅ 正确：预判与实际吻合
- ⚠️ 部分正确：方向对但细节偏差
- ❌ 错误：预判与实际相反
- 连续复盘形成预测准确率统计

### 脚本清单（均不自动调用 LLM）

| 脚本 | 用途 | 状态 | LLM？ |
|------|------|------|-------|
| `prepare_market_report.py` | 收集数据 + 组装 prompt（为人工报告生成准备） | ✅ 启用 | ❌ |
| `market_data.py` | 真实市场数据源（腾讯财经接口） | ✅ 启用 | ❌ |
| `sync_memory_to_notion.py` | 每日记忆自动同步到 Notion | ✅ 启用（cron 23:59） | ❌ |
| `mcp_market_data_server.py` | 将 market_data 封装为 MCP 服务器（可选） | ✅ 完成 | ❌ |
| `batch_insert_nce3.py` | 批量录入新概念英语到 Supabase | ✅ 就绪 | ❌ |
| `fetch_nce3_lesson.py` | 抓取新概念英语单课数据 | ✅ 就绪 | ❌ |
| `insert_lesson.py` | 将句子录入数据库 | ✅ 就绪 | ❌ |
| `query_wencai*.py` | 问财股票查询（多版本实现） | ⚠️ 待测试 | ❌ |
| `run_with_env.sh` | 为 cron 提供环境变量 wrapper | ✅ 启用 | ❌ |

**已废弃/归档**：
- `generate_market_report.py`（原自动调用 LLM，不符合新策略）

---

### MCP 工具可用性

| 工具 | 来源 | 状态 | 用途 |
|------|------|------|------|
| `mcp_query_table` | pip 全局包 | ⚠️ Windows 路径硬编码（WSL2 不兼容） | 网页表格查询 |
| `fastmcp` | pip | ✅ 已安装 | MCP 服务器框架 |
| `mcp` | pip | ✅ 已安装 | MCP 核心库 |
| `mcp-server-yahoo-finance` | 可选安装 | ❌ 未安装 | 雅虎财经数据（可考虑） |

**当前方案**：使用 `market_data.py` 直接获取数据，不依赖 MCP。

---

### 环境变量

```bash
# Notion API（用于读写）
NOTION_API_KEY=ntn_xxxx... (已脱敏)

# OpenRouter API（备用，当前不自动调用）
OPENROUTER_API_KEY=sk-or-v1-...
```

已保存到 `scripts/run_with_env.sh` 供 cron 使用。

---

### Cron 自动任务

```bash
59 23 * * * /bin/bash /root/.openclaw/workspace/scripts/run_with_env.sh /usr/bin/python3 /root/.openclaw/workspace/scripts/sync_memory_to_notion.py
```

作用：每天 23:59 自动同步当日记忆到 Notion。

**未配置**：市场报告生成 prompt（可按需添加）

---

## 项目：新概念英语静态数据仓库（2026-03-12）

**位置**: `/root/.openclaw/workspace/nce-data/`

**设计原则**:
- 纯静态 JSON 存储，无需数据库
- 单一职责：只管理课程文本数据
- 可版本控制、离线备份
- 支持四册课程扩展

**目录结构**:
```
nce-data/
├── data/
│   ├── book1/  (96课)
│   ├── book2/  (96课)
│   ├── book3/  (60课)
│   └── book4/  (96课)
├── scripts/
│   └── fetch.py   # 抓取与管理工具
└── README.md
```

**数据格式**:
```json
{
  "lesson_id": "3-001",
  "title": "A puma at large",
  "manual": false,
  "english_sentences": [...],
  "chinese_sentences": [...],
  "english_raw": "...",
  "chinese_raw": "..."
}
```

**使用命令**:
```bash
# 抓取单课
python3 scripts/fetch.py fetch 3-001

# 批量抓取整册
python3 scripts/fetch.py batch 2 1 96

# 列出已有数据
python3 scripts/fetch.py list 3

# 验证文件
python3 scripts/fetch.py validate data/book3/3-001.json
```

**当前状态**:
- ✅ 第三册完成 10 课（3-001 ~ 3-010），包含修复后的 B.C. 句子切分
- ⚠️  网站第二册内容尚未发布（页面返回"文章还没有上线"）
- ⬜ 第一册、第四册待网站发布后抓取

**技术实现**:
- curl 请求 + HTML 正则解析
- 缩写保护列表（B.C., Mr., Dr. 等）
- 智能句子边界识别
- 自动按册分类存储

**下一步**:
- 等待网站发布更多第三册课程（目标 60 课）
- 视网站发布情况补充第二/一/四册
- 如需单词解析，可扩展新字段

---

### 天气技能变量

- `WEATHER_SKILL_BEHAVIOR`: `concise` (默认)
- `WEATHER_SKILL_SHOW_SOURCE`: `true` (默认)

---

### 子代理通知偏好

- 用户希望子代理每完成一件子任务就发送进度通知（已记录）
- 保持进度可见，避免长时间无反馈

---

### 汇率查询偏好

- 用户希望使用 `rate` 或 `汇率` 触发时，在结果中同时显示主流货币（USD/CNY/JPY/EUR/HKD）的中间价或参考价
- 显示来源（中国外汇交易中心）
- 保持简洁：1-2行即可
