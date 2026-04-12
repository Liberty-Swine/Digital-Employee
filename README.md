
# 🤖 极客科技 · 数字员工 —— 基于 LangGraph 的多 Agent 智能客服系统

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.0+-green)](https://github.com/langchain-ai/langgraph)
[![Ollama](https://img.shields.io/badge/Ollama-Local-ff7000)](https://ollama.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red)](https://streamlit.io/)

## 📖 项目介绍

**Digital Employee（数字员工）** 是一个从零开始构建的**企业级多 Agent 智能客服系统**。它能够像真人客服一样：

- ✅ **理解用户意图** —— 自动区分“咨询政策”、“执行操作”和“转接人工”。
- ✅ **查询私有知识库** —— 基于 RAG 技术精准回答公司制度、产品说明等问题。
- ✅ **调用业务工具** —— 模拟查询订单、创建工单等实际操作。
- ✅ **记住多轮对话** —— 即使对话长达数十轮，也能正确理解“这个订单”、“它”等指代。

本项目不仅是一个功能完整的 Demo，更是一次**从“单体 Agent”到“LangGraph 状态图编排”的架构演进实战**。代码结构清晰、注释详尽，非常适合 AI Agent 初学者学习和二次开发。

---

## 🏗️ 系统架构

系统采用 **LangGraph** 实现 **Supervisor-Specialist（主管-专家）** 协作模式。所有 Agent 被封装为图中的节点，通过**条件边**动态路由，状态统一管理。

```mermaid
graph TD
    A[👤 用户输入] --> B[🧠 主管节点 supervisor]
    B --> C{🔀 意图路由}
    C -- knowledge --> D[📚 知识库专家 knowledge]
    C -- action --> E[🛠️ 售后执行专家 action]
    C -- human --> F[👥 人工客服 human]
    D --> G[✅ 结束]
    E --> G
    F --> G
```

### 核心组件说明

| 组件 | 职责 | 技术实现 |
| :--- | :--- | :--- |
| **主管 (Supervisor)** | 分析对话历史，识别用户意图 (`knowledge`/`action`/`human`) | LLM + Prompt Engineering |
| **知识库专家 (Knowledge Agent)** | 从本地文档中检索答案，回答政策、说明类问题 | Ollama Embedding + ChromaDB (RAG) |
| **售后执行专家 (Action Agent)** | 处理需操作的任务（查订单、建工单），自主决策调用工具 | Function Calling (LangChain Tools) |
| **人工客服 (Human Agent)** | 处理情绪化或超出系统能力的问题，预留转人工接口 | 占位节点，可扩展 `interrupt` |
| **共享状态 (State)** | 存储对话历史、意图、最终回复等，实现跨节点上下文记忆 | `TypedDict` + `add_messages` |

---

## ✨ 主要特性

- **🧠 智能意图识别**：基于本地 Ollama 模型（`qwen2.5:3b`）进行语义理解，告别生硬的关键词匹配。
- **📚 私有化 RAG 知识库**：文档向量化存储在 ChromaDB，检索精准，数据不出本地。
- **🛠️ 工具调用能力**：售后 Agent 可调用 `query_order`、`create_ticket` 等模拟工具，展现“动手”能力。
- **💬 强大的上下文记忆**：通过 LangGraph 的 `MemorySaver` 与智能上下文提取，在超长对话中保持关键信息不丢失。
- **🕸️ 声明式流程编排**：使用 LangGraph 的 `StateGraph` 替代僵硬的 `if-else`，流程清晰、易于扩展。
- **🖥️ 可视化 Web 界面**：Streamlit 构建，开箱即用，支持一键启动。

---

## 📁 项目结构

```
aiCustomerService/
├── app.py                    # Streamlit Web 入口
├── workflow.py               # LangGraph 图构建与编译
├── state.py                  # 共享状态定义
├── supervisor.py             # 主管节点（意图识别）
├── knowledge_agent.py        # 知识库 Agent 类（RAG）
├── action_agent.py           # 售后 Agent 类（工具调用）
├── agents/                   # LangGraph 节点封装
│   ├── knowledge.py
│   ├── action.py
│   └── human.py
├── chroma_db/                # ChromaDB 向量库持久化目录
├── docs/                     # 知识库原始文档（.txt）
├── requirements.txt          # 项目依赖
└── README.md                 # 本文件
```

---

## 🚀 快速开始

### 环境要求
- Python **3.11+**
- [Ollama](https://ollama.com/) 已安装并启动
- 已拉取以下模型：
  - 对话模型：`qwen2.5:3b`（或其他支持 Function Calling 的模型）
  - 嵌入模型：`lrs33/bce-embedding-base_v1:latest`

### 1. 克隆项目
```bash
git clone https://github.com/Liberty-Swine/digital-employee.git
cd digital-employee
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 启动 Ollama 并拉取模型
```bash
ollama serve   # 在新终端中保持运行
ollama pull qwen2.5:3b
ollama pull lrs33/bce-embedding-base_v1:latest
```

### 4. 准备知识库文档
在 `docs/` 目录下放入你的 `.txt` 文档（例如 `退货政策.txt`）。文件编码请使用 **UTF-8**。

### 5. 构建向量索引
```bash
python build_index.py   # 脚本见下方
```
> 执行后会在项目根目录生成 `chroma_db/` 文件夹，即向量库。

### 6. 启动 Web 应用
```bash
streamlit run app.py
```
浏览器将自动打开 `http://localhost:8501`，即可开始对话！

---

## 📋 测试用例

你可以用以下对话流程验证系统的多轮协作能力：

| 轮次 | 用户输入 | 预期系统行为 |
| :--- | :--- | :--- |
| 1 | “你们的退货政策是什么？” | 主管识别为 `knowledge`，从知识库检索并回答退货条件。 |
| 2 | “我的订单 ORD-20260411-1234 发货了吗？” | 识别为 `action`，调用 `query_order` 返回物流信息。 |
| 3 | “我想把这个订单退货” | 通过历史上下文自动关联订单号，调用 `create_ticket` 生成工单。 |
| 4 | “刚才那个工单号是多少？” | 再次从历史中提取工单号并告知用户。 |
| 5 | “转人工” | 识别为 `human`，返回转接提示。 |

---

## 🛠️ 技术栈

| 类别 | 技术 | 用途 |
| :--- | :--- | :--- |
| **Agent 编排** | LangGraph | 构建状态图，管理节点与条件路由 |
| **LLM 调用** | Ollama + LangChain | 本地运行对话与嵌入模型 |
| **知识库** | ChromaDB | 向量存储与语义检索 |
| **工具调用** | LangChain Tools (`@tool`) | 封装业务操作（查订单、建工单） |
| **Web 界面** | Streamlit | 快速搭建对话交互 UI |
| **开发语言** | Python 3.11+ | 主要开发语言 |

---

## 📊 项目演进路线

- [x] **v0**：基于关键词的硬编码路由（`SimpleCoordinator`）
- [x] **v1**：引入 LLM 意图识别 + RAG 知识库 + 模拟工具调用
- [x] **v2**：使用 LangGraph 重构，实现状态图编排与上下文记忆
- [ ] **v3**：对接真实业务 API（如 FastAPI 后端）
- [ ] **v4**：加入 `Human-in-the-loop` 与 LangSmith 可观测性
- [ ] **v5**：Docker 镜像打包与 Streamlit Cloud 部署

---

## 📝 补充脚本：`build_index.py`

如果你没有向量索引构建脚本，可以新建 `build_index.py` 并写入以下内容：

```python
# build_index.py
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

loader = DirectoryLoader("./docs", glob="**/*.txt", loader_cls=TextLoader, loader_kwargs={"encoding": "utf-8"})
docs = loader.load()

splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(docs)

embeddings = OllamaEmbeddings(model="lrs33/bce-embedding-base_v1:latest", base_url="http://localhost:11434")
Chroma.from_documents(chunks, embeddings, persist_directory="./chroma_db")
print("✅ 向量索引构建完成！")
```

---

## 🤝 贡献与交流

本项目是个人学习与实践的作品，欢迎任何形式的交流与讨论！如果你发现 Bug 或有更好的实现思路，欢迎提 Issue 或 PR。

---

**⭐ 如果这个项目对你有帮助，欢迎给个 Star！**
```

---
