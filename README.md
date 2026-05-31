# 🚀 企业级RAG系统 - 大模型实习生学习系统

一个基于**检索增强生成(RAG)** 技术的企业级智能问答系统，采用原生 Ollama 框架开发，零绑定 LangChain，具有清晰的逻辑架构和高度的可定制性。

## 📋 项目概览

本项目实现了一个完整的工业级 RAG 流水线，核心特性包括：

- **🔍 多路检索**：多查询策略扩展检索覆盖面
- **📚 父子文档架构**：保留文档完整性，精确检索
- **🎯 CrossEncoder 重排**：精准匹配相关文档
- **💬 聊天对话**：支持多轮对话记忆
- **🎨 Streamlit UI**：友好的网页交互界面
- **🔗 原生框架**：零 LangChain 依赖，逻辑清晰

## 🏗️ 系统架构

### 三阶段 RAG 流程

```
┌─────────────────────────────────────────────────────────────────┐
│                   离线阶段（Indexing - 索引构建）                 │
│  文档收集 → 解析 → 分块(Chunking) → 向量化(Embedding) → 入库     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   在线阶段（Retrieval - 检索）                    │
│  Query → 理解 → 多路检索 → 重排序(Rerank) → 筛选Top-K            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   生成阶段（Generation - 生成）                   │
│  Prompt组装 → LLM生成 → 流式返回 → 后处理                        │
└─────────────────────────────────────────────────────────────────┘
```

### 核心工作流程

```
用户输入
    ↓
[APP.PY 前端] - 构造 chat_history
    ↓
[CHAIN.PY] stream_answer()
    ├─ 1️⃣ 问题独立化 (_contextualize_question)
    │   └─ 消除对话历史中的指代歧义，生成独立问题
    │
    ├─ 2️⃣ 多路检索 (retriever.retrieve_context)
    │   ├─ 多查询：生成 3 个查询变体
    │   ├─ 向量检索：从 ChromaDB 查询相关文档
    │   ├─ 父子组装：从 docstore.json 拿完整父文档
    │   └─ CrossEncoder 重排：精确排序文档
    │
    ├─ 3️⃣ Prompt 组装
    │   └─ System + Context + History + Query
    │
    └─ 4️⃣ LLM 流式生成
        └─ 返回带思考过程的结构化回答
```

## 🗂️ 项目结构

```
RAG/
├── README.md                  # 本文件
├── requirements.txt           # 项目依赖
├── RAG_WORKFLOW.md           # 详细工作流程文档
│
├── src/                       # 核心源代码
│   ├── __init__.py
│   ├── app.py                # Streamlit 前端应用
│   ├── chain.py              # RAG 链条核心逻辑
│   ├── retriever.py          # 检索引擎（多查询+重排）
│   ├── ingest.py             # 文档摄入与索引构建
│   ├── config.py             # 全局配置
│   ├── evaluate.py           # 评估工具
│   ├── rewrite_app.py        # 备用应用程序
│   └── test_*.py             # 测试文件
│
├── docs/                      # 文档与数据
│   ├── 小林面试指南.txt       # 示例知识库文档
│   ├── eval_dataset.json     # 评估数据集
│   ├── keyword.md/.txt       # 关键词索引
│   └── Rag_Introduction.md   # RAG 概念介绍
│
├── chroma_db/                # Chroma 向量数据库（持久化）
│   ├── chroma.sqlite3
│   └── [嵌入向量集合]
│
└── store_db/                 # 文档存储库
    └── docstore.json         # 完整文档映射表
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Ollama（本地 LLM 服务）
- CUDA（可选，加速向量计算）

### 1️⃣ 环境安装

**安装 Ollama**（如未安装）

访问 [ollama.ai](https://ollama.ai) 下载并安装 Ollama。

**下载所需模型**

```bash
# 下载 LLM 模型（约 5.5GB）
ollama pull deepseek-r1:8b

# 下载向量模型（约 274MB）
ollama pull nomic-embed-text
```

启动 Ollama 服务：
```bash
ollama serve
```

### 2️⃣ 项目安装

```bash
# 克隆或进入项目目录
cd RAG

# 创建虚拟环境（可选）
python -m venv venv
source venv/Scripts/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 3️⃣ 加载知识库

```bash
cd src

# 摄入文档构建索引
python -c "
from ingest import setup_ingestion_pipeline
setup_ingestion_pipeline('../docs')
"
```

### 4️⃣ 启动应用

```bash
cd src
streamlit run app.py
```

应用将在 `http://localhost:8501` 启动。

## 📝 核心功能说明

### 1. 聊天模块 (💬 Chat Module)

**路径**: [src/app.py](src/app.py)

- ✅ 多轮对话记忆
- ✅ 流式响应显示
- ✅ 思考过程展开/折叠
- ✅ 实时响应流

### 2. 文件管理 (📄 File Management)

**路径**: [src/app.py](src/app.py)

- ✅ 上传新文档
- ✅ 删除已有文档
- ✅ 实时索引更新
- ✅ 支持 PDF、TXT 等格式

### 3. 检索引擎 (🔍 Retriever)

**路径**: [src/retriever.py](src/retriever.py)

**核心策略**：
- **多查询**：生成 3 个查询变体，提升召回率
- **向量检索**：ChromaDB 近似最近邻搜索
- **父子架构**：子文本用于向量匹配，父文本用于上下文
- **CrossEncoder 重排**：用精确匹配器精化排序

### 4. RAG 链条 (⛓️ RAG Chain)

**路径**: [src/chain.py](src/chain.py)

**核心步骤**：
1. **问题独立化** (_contextualize_question)
   - 将对话历史 + 当前问题融合
   - 消除代词指代歧义（如"它出了什么错？"）
   - 生成完全独立的、能被理解的问题

2. **检索上下文** (retriever.retrieve_context)
   - 执行多路检索
   - 返回精选的相关文档片段

3. **组装 Prompt**
   - 系统提示词
   - 对话历史
   - 检索到的上下文
   - 用户问题

4. **LLM 生成**
   - 流式调用 Ollama/GLM
   - 返回结构化回答（思考 + 答案）

## ⚙️ 配置说明

**文件**: [src/config.py](src/config.py)

### LLM 配置

```python
USE_ONLINE_LLM = False           # False: 本地 Ollama, True: 在线 GLM
LLM_MODEL = "deepseek-r1:8b"     # 本地 LLM 模型
OLLAMA_BASE_URL = "http://localhost:11434"
```

### 向量模型配置

```python
USE_ONLINE_EMBEDDING = False     # False: 本地 Ollama, True: 在线 GLM
EMBEDDING_MODEL = "nomic-embed-text"
```

### 分块策略

```python
PARENT_CHUNK_SIZE = 1000         # 完整文档分块大小
PARENT_CHUNK_OVERLAP = 100       # 分块重叠
CHILD_CHUNK_SIZE = 200           # 检索粒度
CHILD_CHUNK_OVERLAP = 50
```

### 检索策略

```python
TOP_K_RETRIEVAL = 10             # 单路召回数
TOP_K_RERANK = 3                 # 最终返回数量
RERANKER_MODEL = "BAAI/bge-reranker-base"
```

## 📊 关键特性解析

### ✨ 问题独立化（Query Contextual Rewrite）

**痛点**：
- 用户说"它出了什么错？"
- 向量空间无法理解"它"指代什么

**解决方案**：
```python
# 将历史 + 当前问题 → 独立问题
独立化前: "它出了什么错？"
独立化后: "DeepSeek-R1 模型在推理时出了什么错？"
```

### 🎯 多路检索（Multi-Query Retrieval）

```python
原始问题: "如何优化 RAG 检索性能？"

生成的 3 个变体:
1. "RAG 检索性能优化技巧"
2. "提升向量检索速度的方法"
3. "RAG 系统延迟降低策略"

并行检索 3 个查询 → 召回率提升 30-50%
```

### 📚 父子文档架构（Parent-Child Chunking）

```
完整文档 (Parent)
├─ 子块 1 (Child) - 向量化 + 检索
├─ 子块 2 (Child) - 向量化 + 检索
└─ 子块 3 (Child) - 向量化 + 检索

检索时：
1. 在子块中向量匹配
2. 获取对应的完整父文档
3. 将整个父文档作为上下文 → 避免上下文丢失
```

### 🔄 CrossEncoder 重排（Reranking）

```
多路检索结果（TOP 10）
        ↓
CrossEncoder 打分
        ↓
精确排序
        ↓
返回 TOP 3
```

## 📚 文档与参考

- [RAG_WORKFLOW.md](RAG_WORKFLOW.md) - 详细工作流程解析
- [docs/Rag_Introduction.md](docs/Rag_Introduction.md) - RAG 概念深入讲解
- [docs/小林面试指南.txt](docs/小林面试指南.txt) - 示例知识库

## 🔧 常见问题

### Q1: 如何添加新的知识库文档？

A: 将文档放在 `docs/` 目录，然后在 Streamlit UI 中的"文件管理"模块上传，或运行：

```python
from ingest import setup_ingestion_pipeline
setup_ingestion_pipeline('../docs')
```

### Q2: 如何切换到在线 LLM (GLM)？

A: 修改 [src/config.py](src/config.py)：

```python
USE_ONLINE_LLM = True
GLM_API_KEY = "your_api_key_here"
GLM_LLM_MODEL = "glm-4.7-flash"
```

### Q3: 如何评估系统性能？

A: 运行评估脚本（需准备评估数据集）：

```bash
python src/evaluate.py
```

### Q4: 速度较慢，如何优化？

A: 调整以下配置：

```python
# config.py
TOP_K_RETRIEVAL = 5   # 从 10 减少到 5
TOP_K_RERANK = 2      # 从 3 减少到 2
CHILD_CHUNK_SIZE = 300  # 增加块大小，减少检索数量
```

## 🧪 测试

项目包含测试文件便于验证功能：

```bash
cd src

# 测试导入
python test_imports.py

# 测试检索器
python test_retriever.py
```

## 📦 依赖清单

| 包 | 版本 | 说明 |
|---|---|---|
| `ollama` | ≥0.1.6 | 本地 LLM 推理 |
| `chromadb` | ≥0.4.22 | 向量数据库 |
| `streamlit` | ≥1.30.0 | Web 前端框架 |
| `sentence-transformers` | ≥2.2.0 | 向量编码器 |
| `pypdf` | ≥4.0.0 | PDF 解析 |
| `torchvision` | - | 计算机视觉库 |

详见 [requirements.txt](requirements.txt)

## 💡 最佳实践

### 1. 知识库管理
- 保持文档的更新频率
- 定期验证检索质量
- 监控索引大小和查询延迟

### 2. 提示词优化
- 根据业务场景调整系统提示词（见 [src/chain.py](src/chain.py) L86-99）
- 在思考过程中引导模型的推理方向
- 使用结构化输出格式

### 3. 性能调优
- 合理选择 `TOP_K_RETRIEVAL` 和 `TOP_K_RERANK`
- 根据硬件选择模型大小（8B vs 大模型）
- 使用向量索引加速（FAISS, 产品量化等）

### 4. 生产部署
- 监控错误日志和性能指标
- 实现回源机制处理未知问题
- 定期 A/B 测试新配置

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目仅供学习和研究使用。

## 👨‍💻 开发者

企业级 RAG 系统开发团队

---

**最后更新**: 2026-05-29

**快乐使用！如有问题，请提交 Issue。** 🎉
