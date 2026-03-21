# NanoBOT FastAPI HTTP 接口实现文档

> 基于 NanoBOT v0.1.4 架构分析
> 生成时间: 2026-03-21

---

## 目录

1. [核心架构分析](#1-核心架构分析)
2. [接口设计规范](#2-接口设计规范)
3. [认证与安全](#3-认证与安全)
4. [部署配置](#4-部署配置)
5. [示例代码](#5-示例代码)
6. [文档生成](#6-文档生成)
7. [生产环境准备](#7-生产环境准备)
8. [项目结构说明](#8-项目结构说明)

---

## 1. 核心架构分析

### 1.1 系统架构概览

NanoBOT 采用 **事件驱动 + 消息总线** 架构，核心组件包括：

```
┌─────────────────────────────────────────────────────────────────┐
│                        NanoBOT 架构                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │   Channel    │     │    CLI       │     │   Cron       │    │
│  │  (Telegram,  │     │  (Interactive)│     │  Service     │    │
│  │  Discord...) │     │              │     │              │    │
│  └──────┬───────┘     └──────┬───────┘     └──────┬───────┘    │
│         │                    │                    │             │
│         └────────────────────┼────────────────────┘             │
│                              ▼                                   │
│                    ┌──────────────────┐                          │
│                    │   MessageBus     │                          │
│                    │  (asyncio.Queue) │                          │
│                    └────────┬─────────┘                          │
│                             │                                     │
│         ┌───────────────────┼───────────────────┐                │
│         ▼                   ▼                   ▼                │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │ AgentLoop   │    │   Memory    │    │   Tools     │         │
│  │ (Core)      │    │Consolidator│    │  Registry   │         │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘         │
│         │                  │                  │                 │
│         └───────────────────┼──────────────────┘                 │
│                             ▼                                    │
│                    ┌──────────────────┐                          │
│                    │   LLM Provider   │                          │
│                    │ (LiteLLM/自定义) │                          │
│                    └──────────────────┘                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 核心组件详解

#### 1.2.1 MessageBus (消息总线)

**文件**: `nanobot/bus/queue.py`

```python
class MessageBus:
    """Async message bus that decouples chat channels from the agent core."""
    
    def __init__(self):
        self.inbound: asyncio.Queue[InboundMessage] = asyncio.Queue()
        self.outbound: asyncio.Queue[OutboundMessage] = asyncio.Queue()
    
    async def publish_inbound(self, msg: InboundMessage) -> None
    async def consume_inbound(self) -> InboundMessage
    async def publish_outbound(self, msg: OutboundMessage) -> None
    async def consume_outbound(self) -> OutboundMessage
```

**关键特性**:
- 基于 `asyncio.Queue` 实现，天然支持异步
- 解耦消息生产者（Channels）和消费者（AgentLoop）
- 支持背压（Backpressure）

#### 1.2.2 AgentLoop (核心循环)

**文件**: `nanobot/agent/loop.py`

```python
class AgentLoop:
    """Main agent loop that processes messages from the bus."""
    
    def __init__(
        self,
        bus: MessageBus,
        provider: LLMProvider,
        workspace: Path,
        model: str,
        max_iterations: int = 40,
        context_window_tokens: int = 65_536,
        # ... 其他配置
    )
    
    async def run(self) -> None:
        """主循环：消费消息、处理、返回响应"""
        
    async def process_direct(
        self,
        content: str,
        session_key: str = "cli:direct",
        channel: str = "cli",
        chat_id: str = "direct",
        on_progress: Callable[[str], Awaitable[None]] | None = None,
    ) -> str:
        """直接处理消息，返回字符串响应"""
```

**核心流程**:
1. 消费 `inbound` 消息队列
2. 构建消息上下文（系统提示 + 历史）
3. 调用 LLM Provider 执行工具调用循环
4. 保存会话历史
5. 发布 `outbound` 响应

#### 1.2.3 SessionManager (会话管理)

**文件**: `nanobot/session/manager.py`

```python
@dataclass
class Session:
    key: str  # channel:chat_id
    messages: list[dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any]
    last_consolidated: int  # 已归档的消息数量

class SessionManager:
    def __init__(self, workspace: Path)
    def get_or_create(self, key: str) -> Session
    def save(self, session: Session) -> None
    def list_sessions(self) -> list[dict[str, Any]]
```

**存储格式**: JSONL (每行一个 JSON 对象)

```jsonl
{"_type": "metadata", "key": "telegram:12345", "created_at": "2026-03-21T10:00:00"}
{"role": "user", "content": "Hello", "timestamp": "2026-03-21T10:00:01"}
{"role": "assistant", "content": "Hi there!"}
```

#### 1.2.4 LLM Provider 系统

**文件**: `nanobot/providers/base.py`

```python
@dataclass
class LLMResponse:
    content: str | None
    tool_calls: list[ToolCallRequest]
    finish_reason: str
    usage: dict[str, int]
    reasoning_content: str | None
    thinking_blocks: list[dict] | None

class LLMProvider(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> LLMResponse
```

**支持的 Provider**:
| Provider | 标识 | 类型 |
|----------|------|------|
| OpenRouter | `openrouter` | Gateway |
| AiHubMix | `aihubmix` | Gateway |
| SiliconFlow | `siliconflow` | Gateway |
| Anthropic | `anthropic` | Direct |
| OpenAI | `openai` | Direct |
| DeepSeek | `deepseek` | Direct |
| Gemini | `gemini` | Direct |
| Ollama | `ollama` | Local |
| vLLM | `vllm` | Local |
| Azure OpenAI | `azure_openai` | Direct |

#### 1.2.5 ToolRegistry (工具系统)

**文件**: `nanobot/agent/tools/registry.py`

```python
class ToolRegistry:
    def register(self, tool: Tool) -> None
    def get(self, name: str) -> Tool | None
    def get_definitions(self) -> list[dict[str, Any]]  # OpenAI format
    async def execute(self, name: str, params: dict[str, Any]) -> str
```

**内置工具**:
- `filesystem`: 文件读写操作
- `shell`: 命令执行
- `spawn`: 子进程启动
- `web`: 网页获取
- `message`: 消息发送
- `mcp`: MCP 协议集成
- `cron`: 定时任务

### 1.3 FastAPI 集成切入点

基于现有架构，FastAPI 接口最佳集成方式是 **HTTP Channel**:

```python
# 新增 nanobot/channels/http.py
class HTTPChannel(BaseChannel):
    """HTTP/WebSocket channel for FastAPI integration."""
    
    name = "http"
    display_name = "HTTP API"
    
    async def start(self) -> None:
        """启动 FastAPI 应用（由外部管理）"""
        pass
    
    async def stop(self) -> None:
        pass
    
    async def send(self, msg: OutboundMessage) -> None:
        """通过 WebSocket 推送或 HTTP 回调"""
```

---

## 2. 接口设计规范

### 2.1 REST API 设计

#### 2.1.1 端点总览

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| POST | `/v1/chat/completions` | 发送消息并获取响应 | API Key |
| GET | `/v1/sessions` | 列出所有会话 | API Key |
| GET | `/v1/sessions/{id}` | 获取会话详情 | API Key |
| DELETE | `/v1/sessions/{id}` | 删除会话 | API Key |
| GET | `/v1/tools` | 列出可用工具 | API Key |
| GET | `/v1/health` | 健康检查 | 无 |
| GET | `/v1/models` | 列出可用模型 | API Key |

#### 2.1.2 请求/响应模型

**Chat Request**:
```python
from pydantic import BaseModel, Field
from typing import Optional

class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    name: Optional[str] = None

class ChatCompletionRequest(BaseModel):
    model: str = Field(default="anthropic/claude-opus-4-5")
    messages: list[ChatMessage]
    session_id: Optional[str] = None  # 不提供则创建新会话
    temperature: Optional[float] = Field(default=0.7, ge=0, le=2)
    max_tokens: Optional[int] = Field(default=4096, ge=1, le=32768)
    stream: bool = Field(default=False)
    tools: Optional[list[dict]] = None  # 覆盖默认工具
    
    class Config:
        json_schema_extra = {
            "example": {
                "model": "anthropic/claude-opus-4-5",
                "messages": [
                    {"role": "user", "content": "Hello, who are you?"}
                ],
                "session_id": None
            }
        }
```

**Chat Response**:
```python
class UsageInfo(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChatCompletionResponse(BaseModel):
    id: str
    object: Literal["chat.completion", "chat.completion.chunk"]
    created: int  # Unix timestamp
    model: str
    choices: list["Choice"]
    usage: Optional[UsageInfo] = None
    
class Choice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: Optional[str] = None
```

**Stream Response** (SSE):
```
event: chunk
data: {"id":"chatcmpl-xxx","object":"chat.completion.chunk","created":1677654321,"model":"claude","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}

event: done
data: {"id":"chatcmpl-xxx","object":"chat.completion.chunk","created":1677654321,"model":"claude","choices":[{"index":0,"delta":{},"finish_reason":"stop"}],"usage":{"prompt_tokens":10,"completion_tokens":5,"total_tokens":15}}
```

#### 2.1.3 OpenAI 兼容性

为了最大兼容性，实现 OpenAI Chat Completions API 格式：

```python
# /v1/chat/completions - OpenAI 兼容端点
@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest):
    """
    OpenAI Chat Completions API 兼容端点
    
    支持:
    - 标准 chat completions
    - Streaming (text/event-stream)
    - Function calling (tools)
    - 会话上下文
    """
```

### 2.2 WebSocket 接口

**端点**: `/v1/ws/{session_id}`

```python
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/v1/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """WebSocket 实时对话"""
    await websocket.accept()
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_json()
            
            # 处理并发送响应
            async for chunk in agent.process_stream(data["content"], session_id):
                await websocket.send_json(chunk)
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for session {}", session_id)
```

**消息格式**:
```python
# Client -> Server
{
    "type": "message",
    "content": "Hello!",
    "tools": ["filesystem", "web"]  # 可选：指定工具
}

# Server -> Client
{
    "type": "chunk",  # streaming token
    "content": "Hello"
}
{
    "type": "tool_call",
    "tool": "web_search",
    "params": {"query": "..."}
}
{
    "type": "done",
    "content": "Final response",
    "usage": {"prompt_tokens": 10, "completion_tokens": 5}
}
```

### 2.3 错误处理

**错误响应格式** (RFC 7807):
```python
class APIError(BaseModel):
    error: dict = Field(
        default_factory=lambda: {
            "message": "",
            "type": "invalid_request_error",
            "code": None,
            "param": None,
        }
    )

# HTTP 状态码
# 400 - 请求参数错误
# 401 - 认证失败
# 403 - 权限不足
# 404 - 资源不存在
# 429 - 请求频率超限
# 500 - 服务器内部错误
# 503 - 服务不可用 (LLM Provider 问题)
```

---

## 3. 认证与安全

### 3.1 API Key 认证

```python
from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

# Header 方案
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

class AuthenticatedUser(BaseModel):
    user_id: str
    scopes: list[str]
    rate_limit: int

async def verify_api_key(
    api_key: str | None = Security(api_key_header),
) -> AuthenticatedUser:
    """验证 API Key"""
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 移除 "Bearer " 前缀
    if api_key.startswith("Bearer "):
        api_key = api_key[7:]
    
    # 验证并获取用户信息
    user = await validate_key(api_key)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

# 使用依赖注入
@app.post("/v1/chat/completions")
async def chat(
    request: ChatCompletionRequest,
    user: AuthenticatedUser = Depends(verify_api_key),
):
    # 检查速率限制
    await check_rate_limit(user, request)
    # 处理请求...
```

### 3.2 多租户隔离

```python
class TenantContext(BaseModel):
    """租户上下文"""
    tenant_id: str
    workspace: Path
    config: Config
    rate_limit: dict  # 每分钟/小时请求数

# 中间件设置租户
@app.middleware("http")
async def set_tenant_context(request: Request, call_next):
    api_key = request.headers.get("Authorization", "").replace("Bearer ", "")
    tenant = await get_tenant_by_key(api_key)
    
    if tenant:
        request.state.tenant = tenant
    
    response = await call_next(request)
    return response

# 在请求处理器中获取
@app.post("/v1/chat/completions")
async def chat(request: ChatCompletionRequest, http_request: Request):
    tenant: TenantContext = http_request.state.tenant
    # 使用 tenant.workspace 和 tenant.config
```

### 3.3 安全配置

```yaml
# config.yaml
api:
  host: "0.0.0.0"
  port: 18791
  rate_limit:
    requests_per_minute: 60
    requests_per_hour: 1000
    burst: 10
  cors:
    allowed_origins:
      - "https://app.example.com"
    allowed_methods:
      - "GET"
      - "POST"
    allowed_headers:
      - "Authorization"
      - "Content-Type"
  ssl:
    enabled: true
    cert_file: "/path/to/cert.pem"
    key_file: "/path/to/key.pem"
```

### 3.4 请求验证

```python
from pydantic import validator
import re

class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    session_id: Optional[str] = None
    
    @validator('model')
    def validate_model(cls, v):
        allowed_prefixes = ('anthropic/', 'openai/', 'deepseek/', 
                          'gemini/', 'ollama/', 'openrouter/')
        if not any(v.startswith(p) for p in allowed_prefixes):
            raise ValueError(f"Model must start with one of: {allowed_prefixes}")
        return v
    
    @validator('messages')
    def validate_messages(cls, v):
        if not v:
            raise ValueError("messages cannot be empty")
        if len(v) > 100:
            raise ValueError("Maximum 100 messages per request")
        for msg in v:
            if len(msg.content) > 100000:
                raise ValueError("Message content exceeds 100KB limit")
        return v
```

---

## 4. 部署配置

### 4.1 环境变量

```bash
# .env 示例
# ============ API Server ============
NANOBOT_API_HOST=0.0.0.0
NANOBOT_API_PORT=18791
NANOBOT_API_KEY=sk-nanobot-xxxxx  # 主 API Key

# ============ LLM Provider ============
# 使用 OpenRouter
OPENROUTER_API_KEY=sk-or-v1-xxxxx
NANOBOT_PROVIDER=openrouter
NANOBOT_MODEL=anthropic/claude-opus-4-5

# 或使用 Anthropic Direct
ANTHROPIC_API_KEY=sk-ant-xxxxx
NANOBOT_PROVIDER=anthropic
NANOBOT_MODEL=claude-opus-4-5

# ============ Workspace ============
NANOBOT_WORKSPACE=/data/nanobot/workspace
NANOBOT_CONFIG=/data/nanobot/config.json

# ============ Security ============
NANOBOT_RATE_LIMIT_PER_MINUTE=60
NANOBOT_ALLOWED_ORIGINS=https://app.example.com

# ============ Logging ============
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### 4.2 Docker 部署

```dockerfile
# Dockerfile.api
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY pyproject.toml README.md LICENSE ./

# 安装依赖
RUN mkdir -p nanobot && touch nanobot/__init__.py && \
    uv pip install --system --no-cache .[all] && \
    uv pip install --system --no-cache "fastapi[standard]>=0.115.0" uvicorn[standard] && \
    rm -rf nanobot bridge

# 复制源码
COPY nanobot/ nanobot/
COPY api/ api/  # FastAPI 应用代码

# 创建配置目录
RUN mkdir -p /data/nanobot

# 暴露端口
EXPOSE 18791

# 启动命令
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "18791"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  nanobot-api:
    build:
      context: .
      dockerfile: Dockerfile.api
    container_name: nanobot-api
    restart: unless-stopped
    ports:
      - "18791:18791"
    volumes:
      - ./config:/data/nanobot
      - nanobot-workspace:/data/nanobot/workspace
    environment:
      - NANOBOT_WORKSPACE=/data/nanobot/workspace
      - NANOBOT_CONFIG=/data/nanobot/config.json
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:18791/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '0.5'
          memory: 1G

volumes:
  nanobot-workspace:
```

### 4.3 Kubernetes 部署

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nanobot-api
  labels:
    app: nanobot-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nanobot-api
  template:
    metadata:
      labels:
        app: nanobot-api
    spec:
      containers:
        - name: nanobot-api
          image: ghcr.io/hkuds/nanobot-api:latest
          ports:
            - containerPort: 18791
          env:
            - name: NANOBOT_WORKSPACE
              value: /data/nanobot/workspace
            - name: OPENROUTER_API_KEY
              valueFrom:
                secretKeyRef:
                  name: nanobot-secrets
                  key: api-key
          resources:
            requests:
              memory: "1Gi"
              cpu: "500m"
            limits:
              memory: "4Gi"
              cpu: "2000m"
          livenessProbe:
            httpGet:
              path: /v1/health
              port: 18791
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /v1/health
              port: 18791
            initialDelaySeconds: 5
            periodSeconds: 5
          volumeMounts:
            - name: workspace
              mountPath: /data/nanobot
      volumes:
        - name: workspace
          persistentVolumeClaim:
            claimName: nanobot-workspace

---
apiVersion: v1
kind: Service
metadata:
  name: nanobot-api
spec:
  selector:
    app: nanobot-api
  ports:
    - port: 80
      targetPort: 18791
  type: ClusterIP

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: nanobot-api
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
    - hosts:
        - api.example.com
      secretName: nanobot-api-tls
  rules:
    - host: api.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: nanobot-api
                port:
                  number: 80
```

---

## 5. 示例代码

### 5.1 完整 FastAPI 应用

```python
# api/main.py
"""
NanoBOT HTTP API Server

基于 FastAPI 的 HTTP 接口实现，复用 NanoBOT 核心组件。
"""

from __future__ import annotations

import asyncio
import json
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncGenerator

from fastapi import FastAPI, HTTPException, Request, Depends, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, validator
from typing_extensions import Literal

from nanobot.config.loader import load_config, set_config_path
from nanobot.config.schema import Config
from nanobot.bus.queue import MessageBus
from nanobot.bus.events import InboundMessage, OutboundMessage
from nanobot.agent.loop import AgentLoop
from nanobot.session.manager import SessionManager
from nanobot.cli.commands import _make_provider
from nanobot.utils.helpers import sync_workspace_templates


# ============ Pydantic Models ============

class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    name: str | None = None

class ChatCompletionRequest(BaseModel):
    model: str = Field(default="anthropic/claude-opus-4-5")
    messages: list[ChatMessage]
    session_id: str | None = None
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=4096, ge=1)
    stream: bool = Field(default=False)
    tools: list[dict[str, Any]] | None = None
    
    @validator('messages')
    def validate_messages(cls, v):
        if not v:
            raise ValueError("messages cannot be empty")
        if len(v) > 100:
            raise ValueError("Maximum 100 messages per request")
        return v

class UsageInfo(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str | None = None

class ChatCompletionResponse(BaseModel):
    id: str
    object: Literal["chat.completion", "chat.completion.chunk"] = "chat.completion"
    created: int
    model: str
    choices: list[ChatCompletionChoice]
    usage: UsageInfo | None = None

class ErrorDetail(BaseModel):
    message: str
    type: str
    code: str | None = None
    param: str | None = None

class ErrorResponse(BaseModel):
    error: ErrorDetail


# ============ Application State ============

class AppState:
    """应用全局状态"""
    config: Config
    bus: MessageBus
    agent: AgentLoop
    session_manager: SessionManager
    
    def __init__(self):
        self.config = None
        self.bus = None
        self.agent = None
        self.session_manager = None


state = AppState()


# ============ Lifespan ============

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理"""
    # 启动时初始化
    config_path = Path(os.getenv("NANOBOT_CONFIG", "~/.nanobot/config.json"))
    set_config_path(config_path.expanduser())
    
    state.config = load_config()
    state.bus = MessageBus()
    state.session_manager = SessionManager(state.config.workspace_path)
    
    # 初始化 Agent
    provider = _make_provider(state.config)
    state.agent = AgentLoop(
        bus=state.bus,
        provider=provider,
        workspace=state.config.workspace_path,
        model=state.config.agents.defaults.model,
        max_iterations=state.config.agents.defaults.max_tool_iterations,
        context_window_tokens=state.config.agents.defaults.context_window_tokens,
        web_search_config=state.config.tools.web.search,
        web_proxy=state.config.tools.web.proxy,
        exec_config=state.config.tools.exec,
        cron_service=None,  # API 模式不使用 cron
        restrict_to_workspace=state.config.tools.restrict_to_workspace,
        session_manager=state.session_manager,
        mcp_servers=state.config.tools.mcp_servers,
        channels_config=state.config.channels,
    )
    
    # 启动后台任务
    asyncio.create_task(state.agent.run())
    
    yield
    
    # 关闭时清理
    state.agent.stop()
    await state.agent.close_mcp()


# ============ FastAPI App ============

app = FastAPI(
    title="NanoBOT API",
    description="Personal AI Assistant HTTP API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ Middleware ============

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """添加请求处理时间"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# ============ Health Check ============

@app.get("/v1/health", tags=["System"])
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
    }


# ============ Chat Completions ============

@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(request: ChatCompletionRequest):
    """Chat Completions API (OpenAI 兼容)"""
    
    # 生成响应 ID
    response_id = f"chatcmpl-{int(time.time() * 1000)}"
    
    # 转换消息格式
    nanobot_messages = [
        {"role": m.role, "content": m.content, "name": m.name}
        for m in request.messages
    ]
    
    # 确定 session_id
    session_key = request.session_id or f"http:{response_id}"
    
    # 处理请求
    try:
        response_content = await state.agent.process_direct(
            content=request.messages[-1].content,
            session_key=session_key,
            channel="http",
            chat_id=response_id,
        )
        
        # 构建响应
        return ChatCompletionResponse(
            id=response_id,
            created=int(time.time()),
            model=request.model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(
                        role="assistant",
                        content=response_content,
                    ),
                    finish_reason="stop",
                )
            ],
            usage=UsageInfo(
                prompt_tokens=len(json.dumps(nanobot_messages)) // 4,  # 粗略估算
                completion_tokens=len(response_content) // 4,
                total_tokens=len(json.dumps(nanobot_messages)) // 4 + len(response_content) // 4,
            ),
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ Streaming Chat Completions ============

@app.post("/v1/chat/completions/stream")
async def chat_completions_stream(request: ChatCompletionRequest):
    """Streaming Chat Completions API"""
    
    response_id = f"chatcmpl-{int(time.time() * 1000)}"
    session_key = request.session_id or f"http:{response_id}"
    
    async def generate():
        content_parts = []
        
        async def on_progress(content: str):
            """进度回调"""
            content_parts.append(content)
            chunk = json.dumps({
                "id": response_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "delta": {"content": content},
                    "finish_reason": None,
                }],
            })
            yield f"data: {chunk}\n\n"
        
        try:
            response_content = await state.agent.process_direct(
                content=request.messages[-1].content,
                session_key=session_key,
                channel="http",
                chat_id=response_id,
                on_progress=on_progress,
            )
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"
            return
        
        # 发送完成
        final_chunk = json.dumps({
            "id": response_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": request.model,
            "choices": [{
                "index": 0,
                "delta": {},
                "finish_reason": "stop",
            }],
        })
        yield f"data: {final_chunk}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


# ============ Session Management ============

@app.get("/v1/sessions", tags=["Sessions"])
async def list_sessions():
    """列出所有会话"""
    sessions = state.session_manager.list_sessions()
    return {"sessions": sessions, "total": len(sessions)}


@app.get("/v1/sessions/{session_id}", tags=["Sessions"])
async def get_session(session_id: str):
    """获取会话详情"""
    session = state.session_manager.get_or_create(session_id)
    return {
        "key": session.key,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
        "message_count": len(session.messages),
        "metadata": session.metadata,
    }


@app.delete("/v1/sessions/{session_id}", tags=["Sessions"])
async def delete_session(session_id: str):
    """删除会话"""
    state.session_manager.invalidate(session_id)
    session_path = state.session_manager._get_session_path(session_id)
    if session_path.exists():
        session_path.unlink()
    return {"deleted": session_id}


# ============ Tools ============

@app.get("/v1/tools", tags=["Tools"])
async def list_tools():
    """列出可用工具"""
    tools = state.agent.tools.get_definitions()
    return {"tools": tools, "total": len(tools)}


# ============ WebSocket ============

@app.websocket("/v1/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """WebSocket 实时对话"""
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "message":
                content = data.get("content", "")
                
                async def on_progress(text: str, **kwargs):
                    await websocket.send_json({
                        "type": "chunk",
                        "content": text,
                    })
                
                response = await state.agent.process_direct(
                    content=content,
                    session_key=f"ws:{session_id}",
                    channel="websocket",
                    chat_id=session_id,
                    on_progress=on_progress,
                )
                
                await websocket.send_json({
                    "type": "done",
                    "content": response,
                })
                
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
    finally:
        try:
            await websocket.close()
        except:
            pass


# ============ Run ============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=18791,
        reload=False,
        workers=1,  # 多 worker 需要外部进程管理器
    )
```

### 5.2 客户端示例

**Python 客户端**:
```python
import httpx
import asyncio

class NanoBOTClient:
    """NanoBOT API Python 客户端"""
    
    def __init__(self, api_key: str, base_url: str = "http://localhost:18791"):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=120.0,
        )
    
    async def chat(
        self,
        message: str,
        session_id: str | None = None,
        model: str = "anthropic/claude-opus-4-5",
        stream: bool = False,
    ) -> dict:
        """发送消息并获取响应"""
        response = await self.client.post(
            f"{self.base_url}/v1/chat/completions",
            json={
                "model": model,
                "messages": [{"role": "user", "content": message}],
                "session_id": session_id,
                "stream": stream,
            },
        )
        response.raise_for_status()
        return response.json()
    
    async def chat_stream(self, message: str, session_id: str | None = None):
        """流式响应"""
        async with self.client.stream(
            "POST",
            f"{self.base_url}/v1/chat/completions",
            json={
                "model": "anthropic/claude-opus-4-5",
                "messages": [{"role": "user", "content": message}],
                "session_id": session_id,
            },
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    yield json.loads(data)
    
    async def list_sessions(self) -> list[dict]:
        """列出所有会话"""
        response = await self.client.get(f"{self.base_url}/v1/sessions")
        response.raise_for_status()
        return response.json()["sessions"]
    
    async def close(self):
        await self.client.aclose()


# 使用示例
async def main():
    client = NanoBOTClient(api_key="sk-nanobot-xxxxx")
    
    try:
        # 普通对话
        response = await client.chat("Hello, who are you?")
        print(f"Response: {response['choices'][0]['message']['content']}")
        
        # 流式对话
        async for chunk in client.chat_stream("Tell me a story"):
            if chunk.get("choices"):
                content = chunk["choices"][0].get("delta", {}).get("content", "")
                print(content, end="", flush=True)
        
    finally:
        await client.close()


asyncio.run(main())
```

**cURL 示例**:
```bash
# 健康检查
curl http://localhost:18791/v1/health

# 发送消息
curl -X POST http://localhost:18791/v1/chat/completions \
  -H "Authorization: Bearer sk-nanobot-xxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "anthropic/claude-opus-4-5",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# 流式响应
curl -X POST http://localhost:18791/v1/chat/completions \
  -H "Authorization: Bearer sk-nanobot-xxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "anthropic/claude-opus-4-5",
    "messages": [{"role": "user", "content": "Count to 5"}],
    "stream": true
  }'
```

---

## 6. 文档生成

### 6.1 OpenAPI/Swagger 文档

FastAPI 自动生成 OpenAPI 文档：

- **Swagger UI**: http://localhost:18791/docs
- **ReDoc**: http://localhost:18791/redoc
- **OpenAPI JSON**: http://localhost:18791/openapi.json

### 6.2 自定义文档生成

```python
# api/docs.py

def generate_markdown_docs():
    """生成 Markdown 格式 API 文档"""
    
    docs = """# NanoBOT API 文档

## 基础信息

- **API 版本**: v1
- **基础 URL**: `https://api.example.com`
- **认证方式**: Bearer Token

## 认证

所有请求需要包含 `Authorization` header：

```
Authorization: Bearer <your-api-key>
```

## 端点

### 健康检查

**GET** `/v1/health`

检查服务状态。

**响应**:
```json
{
  "status": "healthy",
  "timestamp": "2026-03-21T10:00:00Z",
  "version": "1.0.0"
}
```

### 发送消息

**POST** `/v1/chat/completions`

发送消息并获取 AI 响应。

**请求体**:
```json
{
  "model": "anthropic/claude-opus-4-5",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "session_id": null,
  "temperature": 0.7,
  "max_tokens": 4096,
  "stream": false
}
```

**响应**:
```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1677654321,
  "model": "anthropic/claude-opus-4-5",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 8,
    "total_tokens": 18
  }
}
```

### 错误响应

所有错误遵循 RFC 7807 格式：

```json
{
  "error": {
    "message": "Invalid API key",
    "type": "authentication_error",
    "code": "invalid_key",
    "param": null
  }
}
```

**状态码**:
- `400` - 请求参数错误
- `401` - 认证失败
- `403` - 权限不足
- `404` - 资源不存在
- `429` - 请求频率超限
- `500` - 服务器内部错误
- `503` - LLM 服务不可用

## 示例代码

### Python

```python
import httpx

client = httpx.Client(
    headers={"Authorization": "Bearer sk-nanobot-xxxxx"}
)

response = client.post(
    "https://api.example.com/v1/chat/completions",
    json={
        "model": "anthropic/claude-opus-4-5",
        "messages": [{"role": "user", "content": "Hello!"}]
    }
)

print(response.json()["choices"][0]["message"]["content"])
```

### JavaScript

```javascript
const response = await fetch('https://api.example.com/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer sk-nanobot-xxxxx',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'anthropic/claude-opus-4-5',
    messages: [{ role: 'user', content: 'Hello!' }]
  })
});

const data = await response.json();
console.log(data.choices[0].message.content);
```

### cURL

```bash
curl -X POST https://api.example.com/v1/chat/completions \\
  -H "Authorization: Bearer sk-nanobot-xxxxx" \\
  -H "Content-Type: application/json" \\
  -d '{"model":"anthropic/claude-opus-4-5","messages":[{"role":"user","content":"Hello!"}]}'
```
"""
    return docs


@app.get("/docs/markdown", include_in_schema=False)
async def get_markdown_docs():
    """返回 Markdown 格式文档"""
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(generate_markdown_docs())
```

---

## 7. 生产环境准备

### 7.1 性能优化

```python
# api/performance.py

from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio

# 连接池配置
app = FastAPI(
    title="NanoBOT API",
    # ... 
)

# 异步任务队列
task_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)


async def background_process(message: dict):
    """后台处理请求"""
    await task_queue.put(message)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """简单速率限制"""
    client_ip = request.client.host
    
    # 使用 Redis 实现分布式限流
    key = f"rate_limit:{client_ip}"
    current = await redis.get(key)
    
    if current and int(current) > 60:  # 60 req/min
        return JSONResponse(
            status_code=429,
            content={"error": {"message": "Rate limit exceeded"}},
        )
    
    await redis.incr(key)
    await redis.expire(key, 60)
    
    return await call_next(request)


# Gunicorn + Uvicorn Workers
# gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:18791
```

### 7.2 监控配置

```python
# api/monitoring.py

from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Response

# 指标定义
REQUEST_COUNT = Counter(
    'nanobot_requests_total',
    'Total request count',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'nanobot_request_latency_seconds',
    'Request latency',
    ['method', 'endpoint']
)

TOKEN_USAGE = Counter(
    'nanobot_tokens_total',
    'Total token usage',
    ['model']
)


@app.get("/metrics")
async def metrics():
    """Prometheus 指标端点"""
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )
```

### 7.3 日志配置

```python
# api/logging.py

import logging
import json
from loguru import logger
from fastapi import Request


class JSONFormatter:
    """JSON 格式日志"""
    
    def __call__(self, record):
        log_obj = {
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name,
            "message": record["message"],
            "module": record["module"],
            "function": record["function"],
            "line": record["line"],
        }
        
        if record["exception"]:
            log_obj["exception"] = str(record["exception"])
        
        return json.dumps(log_obj)


def setup_logging(log_level: str = "INFO"):
    """配置日志"""
    logger.remove()
    logger.add(
        "logs/api.log",
        rotation="00:00",
        retention="30 days",
        level=log_level,
        format=JSONFormatter(),
    )
    logger.add(
        "logs/access.log",
        rotation="00:00",
        retention="30 days",
        level=logging.INFO,
        format="{time:YYYY-MM-DD HH:mm:ss} - {message}",
    )


@app.middleware("http")
async def structured_logging(request: Request, call_next):
    """结构化日志中间件"""
    logger.info(
        "request",
        method=request.method,
        path=request.url.path,
        client=request.client.host,
    )
    
    response = await call_next(request)
    
    logger.info(
        "response",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
    )
    
    return response
```

### 7.4 安全检查清单

- [ ] API Key 存储在安全的地方（环境变量/密钥管理服务）
- [ ] 启用 HTTPS/TLS
- [ ] 配置 CORS 白名单
- [ ] 实现请求频率限制
- [ ] 添加 Rate Limit 响应头（X-RateLimit-*）
- [ ] 日志中脱敏敏感信息
- [ ] 定期轮换 API Key
- [ ] 配置告警阈值
- [ ] 启用访问日志审计
- [ ] 定期备份会话数据

### 7.5 高可用部署

```yaml
# docker-compose.ha.yml
version: '3.8'

services:
  nanobot-api-1:
    build: .
    deploy:
      replicas: 3
    depends_on:
      - redis
      - postgres
  
  nanobot-api-2:
    build: .
    deploy:
      replicas: 3
    depends_on:
      - redis
      - postgres

  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data
  
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: nanobot
      POSTGRES_USER: nanobot
    volumes:
      - postgres-data:/var/lib/postgresql/data

  nginx:
    image: nginx:alpine
    ports:
      - "18791:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - nanobot-api-1
      - nanobot-api-2

volumes:
  redis-data:
  postgres-data:
```

---

## 8. 项目结构说明

### 8.1 现有项目结构

```
nanobot/
├── nanobot/
│   ├── __init__.py          # 包初始化
│   ├── __main__.py          # CLI 入口
│   ├── agent/
│   │   ├── loop.py          # Agent 主循环 ⭐
│   │   ├── context.py       # 上下文构建器
│   │   ├── memory.py        # 记忆系统
│   │   ├── skills.py        # 技能加载器
│   │   ├── subagent.py      # 子代理
│   │   └── tools/
│   │       ├── base.py      # 工具基类 ⭐
│   │       ├── registry.py  # 工具注册表 ⭐
│   │       ├── filesystem.py
│   │       ├── shell.py
│   │       ├── web.py
│   │       ├── message.py
│   │       ├── mcp.py
│   │       └── cron.py
│   ├── bus/
│   │   ├── queue.py         # 消息队列 ⭐
│   │   └── events.py        # 事件类型 ⭐
│   ├── channels/
│   │   ├── base.py          # Channel 基类 ⭐
│   │   ├── manager.py       # Channel 管理器 ⭐
│   │   ├── telegram.py
│   │   ├── discord.py
│   │   ├── slack.py
│   │   └── ...              # 更多 Channel
│   ├── config/
│   │   ├── schema.py        # 配置模型 ⭐
│   │   ├── loader.py        # 配置加载 ⭐
│   │   └── paths.py         # 路径工具
│   ├── providers/
│   │   ├── base.py          # Provider 基类 ⭐
│   │   ├── registry.py      # Provider 注册表 ⭐
│   │   ├── litellm_provider.py
│   │   ├── azure_openai_provider.py
│   │   └── custom_provider.py
│   ├── session/
│   │   └── manager.py       # 会话管理 ⭐
│   ├── heartbeat/
│   │   └── service.py       # 心跳服务
│   ├── cron/
│   │   └── service.py       # 定时任务服务
│   ├── security/
│   │   └── network.py       # 网络安全 ⭐
│   ├── cli/
│   │   └── commands.py      # CLI 命令
│   └── utils/
│       ├── helpers.py
│       └── evaluator.py
├── tests/
│   └── test_*.py            # 测试文件
├── pyproject.toml           # 项目配置
├── Dockerfile               # Docker 镜像
└── docker-compose.yml       # Docker 编排
```

### 8.2 新增 FastAPI 结构

```
api/
├── main.py                  # FastAPI 应用入口
├── models.py                # Pydantic 模型
├── routers/
│   ├── chat.py              # Chat completions 路由
│   ├── sessions.py          # Session 管理路由
│   ├── tools.py             # Tools 路由
│   └── websocket.py          # WebSocket 路由
├── middleware/
│   ├── auth.py              # 认证中间件
│   ├── rate_limit.py        # 限流中间件
│   │   └── logging.py        # 日志中间件
├── services/
│   ├── agent_service.py     # Agent 服务封装
│   └── session_service.py    # Session 服务封装
├── docs.py                  # 文档生成
└── monitoring.py            # 监控指标
```

### 8.3 关键文件说明

| 文件 | 说明 | 复用度 |
|------|------|--------|
| `agent/loop.py` | 核心 Agent 循环 | ⭐⭐⭐ 直接复用 |
| `bus/queue.py` | 消息队列 | ⭐⭐⭐ 直接复用 |
| `bus/events.py` | 事件定义 | ⭐⭐⭐ 直接复用 |
| `session/manager.py` | 会话管理 | ⭐⭐ 直接复用 |
| `providers/base.py` | LLM Provider 基类 | ⭐⭐⭐ 直接复用 |
| `config/schema.py` | 配置模型 | ⭐⭐ 复用配置逻辑 |
| `channels/base.py` | Channel 基类 | ⭐ 参考模式 |
| `agent/tools/registry.py` | 工具注册表 | ⭐⭐ 复用工具系统 |

---

## 附录

### A. 配置示例

```json
{
  "agents": {
    "defaults": {
      "workspace": "~/.nanobot/workspace",
      "model": "anthropic/claude-opus-4-5",
      "provider": "openrouter",
      "maxTokens": 8192,
      "contextWindowTokens": 65536,
      "temperature": 0.1,
      "maxToolIterations": 40
    }
  },
  "providers": {
    "openrouter": {
      "apiKey": "sk-or-v1-xxxxx"
    }
  },
  "gateway": {
    "host": "0.0.0.0",
    "port": 18791
  }
}
```

### B. 依赖添加

```bash
# 添加 FastAPI 相关依赖
uv add fastapi "uvicorn[standard]" httpx pydantic

# 可选依赖
uv add python-jose[cryptography]  # JWT 支持
uv add redis[hiredis]              # Redis 缓存
uv add prometheus-client            # 监控
uv add opentelemetry-api           # 链路追踪
```

### C. 环境变量速查

```bash
# NanoBOT 核心
NANOBOT_WORKSPACE=~/.nanobot/workspace
NANOBOT_CONFIG=~/.nanobot/config.json

# API Server
NANOBOT_API_HOST=0.0.0.0
NANOBOT_API_PORT=18791
NANOBOT_API_KEY=sk-nanobot-xxxxx

# LLM Provider
OPENROUTER_API_KEY=sk-or-v1-xxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

---

*文档生成时间: 2026-03-21*
*基于 NanoBOT v0.1.4*
