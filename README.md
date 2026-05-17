# 图书馆智能服务系统

基于 FastAPI + Vue 3 + LangChain 的高校图书馆智能服务系统，集成 AI 智能问答、座位预约、馆藏检索、读者画像等功能。

## 功能特性

- **AI 智能问答** — 多 Agent 协作，意图识别 + RAG 检索 + 自动化操作
- **座位置位图** — 楼层可视化座位网格，Redis 分布式锁防并发
- **馆藏检索** — BM25 + ChromaDB Dense + RRF 融合 + Cross-Encoder 重排
- **预约管理** — 预约/取消/历史查询，Celery 超时自动释放
- **读者画像** — 预约统计、行为标签、个性化推荐
- **知识库管理** — 图书/政策文档的增删改查（管理员）
- **MCP Server** — 开放 5 个 Tool，支持外部 AI 客户端接入
- **全链路追踪** — OpenTelemetry + Jaeger 集成

## 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| 后端框架 | FastAPI | RESTful API + SSE 流式 |
| 数据库 | PostgreSQL 15 | 主业务数据 |
| 缓存/锁 | Redis 7 | 分布式锁 + Celery Broker |
| 向量数据库 | ChromaDB | RAG 文档嵌入与检索 |
| Agent | LangChain | 意图识别 + 多 Agent 调度 |
| 检索引擎 | BM25 + Dense + RRF + Rerank | 四路召回精排 |
| 异步任务 | Celery | 预约提醒/超时释放 |
| 可观测性 | OpenTelemetry + Jaeger | 全链路追踪 |
| 评估 | Ragas | RAG 质量量化指标 |
| 前端 | Vue 3 + Element Plus | 管理后台 + 用户交互 |
| 构建工具 | Vite | 前端工程化 |

## 快速开始

### 前置要求

- Python 3.10+
- Node.js 18+
- PostgreSQL 15
- Redis 7

### 1. 启动基础设施

```bash
docker-compose up -d
```

启动 PostgreSQL 15、Redis 7、Jaeger（可选）。

### 2. 后端启动

```bash
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 填入数据库连接和 LLM API Key
uvicorn app.main:app --reload --port 8000
```

API 文档访问 `http://localhost:8000/docs`

### 3. 前端启动

```bash
cd web-frontend
npm install
npm run dev
```

访问 `http://localhost:5173`

### 4. 数据初始化

```bash
python -c "from app.core.database import SessionLocal; from app.retrieval.ingestion import IngestionPipeline; db = SessionLocal(); IngestionPipeline(db).build_all(); db.close()"
```

## 项目结构

```
smart-library-ai-agent/
├── app/                          # FastAPI 后端
│   ├── main.py                   # 应用入口
│   ├── config.py                 # 配置管理
│   ├── api/v1/                   # RESTful API
│   ├── agents/                   # Agent 层（5 个 Agent）
│   ├── services/                 # 业务服务层
│   ├── models/                   # SQLAlchemy 实体
│   ├── repositories/             # 数据访问层
│   ├── retrieval/                # RAG 检索引擎
│   ├── core/                     # 基础设施
│   ├── mcp_server/               # MCP 开放接口
│   ├── evaluation/               # Ragas 评估
│   ├── observability/            # 链路追踪
│   └── tasks/                    # Celery 任务
├── web-frontend/                 # Vue 3 + Element Plus
│   ├── src/views/                # 9 个页面
│   ├── src/api/                  # Axios 封装
│   ├── src/stores/               # Pinia 状态管理
│   └── src/router/               # 路由配置
├── docker-compose.yml
└── requirements.txt
```

## API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/auth/register` | 用户注册 |
| POST | `/api/v1/auth/login` | 用户登录 |
| GET | `/api/v1/auth/me` | 当前用户信息 |
| GET | `/api/v1/books/` | 馆藏检索 |
| GET | `/api/v1/books/{id}` | 图书详情 |
| GET | `/api/v1/seats/` | 座位列表 |
| GET | `/api/v1/seats/available` | 空闲座位 |
| POST | `/api/v1/seats/book` | 预约座位 |
| GET | `/api/v1/appointments/` | 我的预约 |
| POST | `/api/v1/appointments/{id}/cancel` | 取消预约 |
| POST | `/api/v1/chat/` | AI 问答 |
| GET | `/api/v1/chat/stream` | SSE 流式问答 |

## 亮点设计

### 并发预约控制

Redis 分布式锁（`SET NX EX`）+ PostgreSQL 乐观锁双重保障，防止座位超卖。

### 混合检索

四路召回：BM25 关键词 + ChromaDB 向量 + RRF 融合 + Cross-Encoder 重排。

### 多 Agent 架构

意图识别 → 路由分发 → 领域 Agent 处理，支持 9 种用户意图。
