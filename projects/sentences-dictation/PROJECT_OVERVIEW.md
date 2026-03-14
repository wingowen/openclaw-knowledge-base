# Project Overview: Sentence Dictation Practice Tool

## 项目概述

**Sentence Dictation Practice Tool** 是一个交互式 Web 应用程序，旨在通过听写句子练习帮助用户提高听力和拼写技能。

### 核心功能列表
1. **多数据源支持**: 本地 JSON、Notion、新概念英语、Supabase 数据库
2. **语音合成**: 使用 Web Speech API 播放句子，支持语速调整
3. **音标显示**: 基于 CMU 发音词典显示单词音标
4. **逐词输入**: 支持单词级输入和实时验证
5. **即时反馈**: 答题正确/错误实时显示
6. **进度追踪**: 按数据源缓存练习进度
7. **闪卡模式**: 支持间隔重复算法的记忆卡片功能
8. **响应式设计**: 适配桌面和移动设备

---

## 技术栈

### 前端
- **React 19.2.0**: UI 框架
- **Vite 7.2.4**: 构建工具
- **Tailwind CSS**: 样式框架（通过 admin 目录配置）

### 后端/集成
- **Netlify Functions**: Serverless 函数托管
- **Supabase**: 数据库（在线课程数据）
- **Notion API**: 笔记集成
- **Web Speech API**: 语音合成

### 数据处理
- **Axios**: HTTP 客户端
- **Cheerio**: HTML 解析（网页抓取）
- **CMU Pronouncing Dictionary**: 音标生成

### 测试
- **Vitest**: 单元测试框架
- **Testing Library**: React 组件测试

---

## 目录结构说明

```
sentences-dictation/
├── src/
│   ├── components/          # React 组件
│   │   ├── practice/        # 练习页面组件
│   │   ├── ImmersiveSpelling.jsx  # 沉浸式拼写组件
│   │   ├── FlashcardApp.jsx       # 闪卡应用
│   │   └── ...
│   ├── services/            # 业务逻辑服务
│   │   ├── dataService.js        # 数据源管理
│   │   ├── speechService.js      # 语音合成
│   │   ├── pronunciationService.js # 音标处理
│   │   └── ...
│   ├── hooks/               # React Hooks
│   │   ├── useSentences.js       # 句子数据管理
│   │   ├── useSpeechPlayback.js  # 语音播放控制
│   │   └── ...
│   ├── contexts/            # React Context
│   │   └── AppContext.jsx       # 全局状态管理
│   ├── data/                # 本地数据文件
│   │   ├── 简单句.json
│   │   ├── 新概念一.json
│   │   └── new-concept-3.json
│   └── utils/               # 工具函数
│       ├── debounce.js
│       └── contractionMap.js
├── netlify/functions/       # Serverless 函数
│   ├── get-notion-sentences.js
│   ├── get-new-concept-3.js
│   ├── get-new-concept-3-lesson.js
│   └── get-supabase-content.js
├── admin/                   # 管理后台（独立应用）
└── .cache/                  # API 响应缓存
```

---

## 核心架构图（文字版）

```
[用户界面层]
    ├── DataSourceSelection (数据源选择)
    ├── PracticePage (练习页面)
    │   ├── ImmersiveSpelling (沉浸式拼写)
    │   ├── FlashcardApp (闪卡应用)
    │   └── StatsDrawer (统计抽屉)
    └── SettingsModal (设置弹窗)

[状态管理层]
    ├── AppContext (全局 Context)
    │   ├── usePracticeStats (练习统计)
    │   ├── usePracticeProgress (练习进度)
    │   ├── useSentences (句子数据)
    │   └── useSpeechPlayback (语音播放)
    └── localStorage (本地持久化)

[业务逻辑层]
    ├── dataService (数据源管理)
    ├── speechService (语音合成)
    ├── pronunciationService (音标处理)
    └── translationService (翻译服务)

[外部集成层]
    ├── Netlify Functions (Serverless)
    │   ├── Notion API
    │   ├── New Concept 3 抓取
    │   └── Supabase
    └── Web Speech API (浏览器原生)
```

---

## 数据源与集成

### 1. Supabase 数据库
**用途**: 在线课程数据存储
**集成方式**: Netlify Functions 代理访问
**端点**:
- `/.netlify/functions/get-supabase-content?action=tags` - 获取标签列表
- `/.netlify/functions/get-supabase-content?tag_id={id}` - 按标签获取文章
- `/.netlify/functions/get-supabase-content?action=sentences&article_id={id}` - 获取文章句子

**推断的数据库结构**:
- **tags** 表: 课程分类
  - `id`: 主键
  - `name`: 标签名称
- **articles** 表: 课程文章
  - `id`: 主键
  - `title`: 文章标题
  - `tag_id`: 外键关联标签
  - `content`: 文章内容（Markdown 格式）
- **sentences** 表: 句子数据（可能通过视图或函数生成）
  - `article_id`: 关联文章
  - `sentence_text`: 句子文本

### 2. Notion 集成
**用途**: 从 Notion 页面动态获取句子
**集成方式**: Netlify Functions + Notion API
**环境变量**:
- `NOTION_API_KEY`: Notion API 密钥
- `NOTION_PAGE_ID`: Notion 页面 ID

### 3. New Concept English 3
**用途**: 网页抓取新概念英语第三册内容
**集成方式**: Cheerio + Axios 爬虫
**数据源**: 本地 JSON 缓存 (`src/data/new-concept-3.json`)

### 4. 本地数据源
**用途**: 离线练习
**文件**:
- `简单句.json`: 基础句子
- `新概念一.json`: 新概念英语第一册

### 5. 闪卡系统
**用途**: 单词/句子记忆
**存储**: LocalStorage + 数据库（Supabase）

---

## 组件层级与职责

### 主要组件树
```
App
├── DataSourceSelection (数据源选择页)
├── PracticePage (练习页面)
│   ├── ImmersiveSpelling (沉浸式拼写)
│   ├── WordInputs (单词输入)
│   ├── PhoneticsSection (音标显示)
│   ├── PracticeStats (统计显示)
│   └── ResultModal (结果弹窗)
├── FlashcardApp (闪卡应用)
│   ├── FlashcardManager (闪卡管理)
│   ├── FlashcardLearner (闪卡学习)
│   └── FlashcardStats (闪卡统计)
└── SettingsModal (设置)
```

### 组件职责
- **App**: 核心状态管理、数据加载、路由逻辑
- **PracticePage**: 练习页面布局、导航、统计抽屉
- **ImmersiveSpelling**: 沉浸式拼写输入、验证、自动跳转
- **DataSourceSelection**: 数据源选择界面
- **FlashcardApp**: 闪卡功能入口和子视图切换

---

## 状态管理与数据流

### 状态管理策略
1. **Context API**: 全局状态（练习统计、进度、设置）
2. **Local State**: 组件级状态（输入框、UI 状态）
3. **LocalStorage**: 持久化（练习统计、进度）

### 数据流图
```
用户操作 → 事件处理 → 状态更新 → UI 重渲染
     ↓
[LocalStorage] ← 持久化练习状态
     ↓
[Netlify Functions] ← 获取外部数据
     ↓
[Supabase/Notion] ← 数据源
```

### 关键 Hooks
- **useSentences**: 管理句子数据加载和切换
- **usePracticeStats**: 练习统计（正确率、连续正确等）
- **usePracticeProgress**: 练习进度追踪
- **useSpeechPlayback**: 语音播放控制

---

## 数据库结构（Supabase 实际结构）

### 实际表结构（从项目历史记录确认）

| 表名 | 用途 | 关键字段 |
|------|------|----------|
| `articles` | 文章 | id, title, description, source_url, total_sentences |
| `sentences` | 句子 | id, article_id, content, sequence_order, is_active |
| `tags` | 标签 | id, name, color |
| `article_tags` | 文章-标签关联 | article_id, tag_id |
| `sentence_audios` | 句子音频 | id, sentence_id, audio_url, speaker, speed |

**关系说明**:
- `articles` ↔ `tags` 通过 `article_tags` 多对多关联
- `sentences` 通过 `article_id` 关联 `articles`
- `sentence_audios` 通过 `sentence_id` 关联 `sentences`
- `sentences.extensions` 字段存储 JSON 扩展数据（如 `translation` 中文翻译）

**已知标签**:
- id=6: 新概念英语第三册 (#00247D)
- id=7: 新概念英语第二册

**文章统计**:
- 新概念第一册: 144 课
- 新概念第二册: 96 课
- 新概念第三册: 已录入 10 课 (3-001 ~ 3-010)

**API 操作示例**:
```bash
# 查询文章（只读 anon key）
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

### IPv6 兼容性
- 当前运行环境（WSL2）**不支持 IPv6**
- Supabase 通过 Cloudflare CDN 同时支持 IPv4 和 IPv6
- 所有请求需强制 IPv4：curl 用 `-4`，Node.js 设置 dns 模块优先 IPv4

---

## 部署与运行

### 开发环境
```bash
# 安装依赖
npm install

# 启动开发服务器（Vite + Netlify Functions）
npm run netlify-dev

# 访问地址
http://localhost:8888
```

### 生产构建
```bash
# 构建
npm run build

# 预览
npm run preview
```

### Netlify 部署
配置文件: `netlify.toml`
- 构建命令: `npm run build`
- 函数目录: `netlify/functions`
- 发布目录: `dist`

### 环境变量
```env
# Notion 集成
NOTION_API_KEY=your_notion_api_key
NOTION_PAGE_ID=your_notion_page_id

# Supabase（通过 Netlify Functions 配置）
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
```

---

## 已知问题与优化点

### 已知问题（来自 OPTIMIZATION_REPORT.md）
1. **Bundle 过大**: `data` chunk 接近 4MB（cmu-pronouncing-dictionary + Notion SDK）
2. **语音延迟**: 首次播放语音延迟 300-800ms
3. **数据源切换**: 新概念三数据源加载依赖本地 JSON，未实现实时抓取

### 优化建议
1. **字典懒加载**: 动态导入 `cmu-pronouncing-dictionary`
2. **Notion SDK 按需引入**: 只引入需要的模块
3. **服务端渲染预取**: 预加载下一句音频或数据
4. **监控埋点**: 使用 PerformanceObserver 收集真实用户数据

### 已完成优化
- ✅ ImmersiveSpelling 防抖 + 可访问性优化
- ✅ useSpeechPlayback 预加载优化
- ✅ 单元测试覆盖核心组件
- ✅ Bundle 分割检查

---

## 关键代码位置索引

| 功能 | 文件 | 行号范围 |
|------|------|----------|
| 数据源管理 | `src/services/dataService.js` | 1-399 |
| 语音合成 | `src/services/speechService.js` | 1-176 |
| 音标处理 | `src/services/pronunciationService.js` | - |
| 练习页面 | `src/components/practice/PracticePage.jsx` | 1-554 |
| 沉浸式拼写 | `src/components/ImmersiveSpelling.jsx` | - |
| 闪卡应用 | `src/components/FlashcardApp.jsx` | 1-94 |
| 全局状态 | `src/contexts/AppContext.jsx` | 1-249 |
| 句子 Hook | `src/hooks/useSentences.js` | 1-91 |
| 语音播放 Hook | `src/hooks/useSpeechPlayback.js` | - |
| Netlify 函数 | `netlify/functions/get-supabase-content.js` | - |
| 构建配置 | `vite.config.js` | 1-85 |

---

*文档生成时间: 2026-03-14*
*项目路径: /root/.openclaw/workspace/sentences-dictation/*