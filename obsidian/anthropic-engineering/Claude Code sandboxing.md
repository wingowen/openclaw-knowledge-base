#security #sandboxing

> [!info] 基本信息
> 来源: [Beyond permission prompts](https://www.anthropic.com/engineering/claude-code-sandboxing)
> 发布: 2025-10-20 | 难度: 🟣 进阶 | 状态: ⬜ 未开始 | 约 35 分钟

## 章节概括

### 问题：权限弹窗疲劳
Claude Code 默认只读，每次修改/运行命令都需要批准 → 用户开始不看就点 → 更不安全。

### 解决方案：Sandboxing
用操作系统级沙箱预定义边界，Agent 在边界内自由工作。

### 两层隔离
- **文件系统隔离**：只能访问/修改指定目录（防止修改系统文件）
- **网络隔离**：只能连接批准的服务器（防止数据泄露/下载恶意软件）
- **两者缺一不可**：无网络隔离 → 可泄露 SSH key；无文件隔离 → 可逃逸沙箱

### 实现细节
- Linux：基于 [bubblewrap](https://github.com/containers/bubblewrap)
- macOS：基于 seatbelt
- 沙箱内命令通过 unix socket 代理访问网络
- 用户可配置允许的域名/路径

### 效果
- 权限弹窗减少 **84%**
- 即使 prompt 注入成功也无法突破沙箱
- 已开源：[sandbox-runtime](https://github.com/anthropic-experimental/sandbox-runtime)

### Claude Code on the Web
- 云端隔离沙箱运行
- Git 凭据不在沙箱内，通过 proxy 代理
- Proxy 验证：分支名、仓库目标、认证 token

## 学习笔记
（待阅读后补充）

---

#security #sandboxing
