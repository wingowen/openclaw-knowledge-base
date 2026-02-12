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
| 3-004 The double life of Alfred Bloggs | 10 | 14 |
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

**WSL2 运行配置** → 详见 `coding-agent` 技能的 Learnings 部分

**Endpoint**：http://127.0.0.1:8000/sse

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

---

## 工具安装 (2026-02-12)

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