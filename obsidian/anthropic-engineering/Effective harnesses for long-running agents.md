#agent-infrastructure #system-design

> [!info] 基本信息
> 来源: [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
> 发布: 2025-11-26 | 难度: 🟣 进阶 | 状态: ⬜ 未开始 | 约 45 分钟

## 章节概括

### 核心问题
Agent 需要跨多个上下文窗口工作（每个新窗口无记忆）。"换班失忆"问题——下一个 Agent 不知道上一个做了什么。

### 两大失败模式
1. **一口气做完**：Agent 试图在一个窗口完成所有事情 → 上下文耗尽 → 下个 Agent 面对半成品
2. **过早宣布完成**：看到已有进展就认为任务完成了

### 解决方案：Initializer + Coding Agent

#### Initializer Agent（首次运行）
- 创建 `feature_list.json`：列出所有功能需求，初始标记为 failing
- 创建 `claude-progress.txt`：进度日志
- 创建 `init.sh`：启动开发服务器和基本测试
- 初始 git commit

#### Coding Agent（每次后续运行）
1. `pwd` 确认目录
2. 读 git log + progress 文件了解状态
3. 读 feature list，选择最高优先级未完成功能
4. **一次只做一个功能**
5. 测试验证（用浏览器自动化如 Puppeteer）
6. commit + 更新 progress 文件

### 关键设计
- **JSON 格式的 feature list**：模型不容易随意修改 JSON（比 Markdown 好）
- **git commit 粒度**：每个功能一个 commit，可回滚
- **端到端测试**：prompt 要求像人类用户一样测试，不用 curl 单元测试
- **启动前先验证**：先跑基本功能测试，确认上次没留 bug

### 失败模式与解决方案对照表

| 问题 | Initializer 行为 | Coding Agent 行为 |
|------|------------------|-------------------|
| 过早完成 | 设 feature list | 每次读 feature list，选一个未完成功能 |
| 留下 bug | 设 git repo + progress 文件 | 读 progress → 跑基本测试 → 修 bug → 再开发 |
| 上下文混乱 | 写 init.sh | 启动服务器 → 验证功能 → 有条理地工作 |

## 学习笔记
（待阅读后补充）

---

#agent-infrastructure #system-design
