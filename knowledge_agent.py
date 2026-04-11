# knowledge_agent.py

# from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaEmbeddings  # 改用 Ollama 嵌入
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate

class KnowledgeAgent:
    """知识库专家：基于本地 RAG 知识库回答用户问题"""
    def __init__(self, persist_directory="./chroma_db"):
        """
        初始化知识库 Agent
        :param persist_directory: Chroma 向量库持久化目录
        """

        print("5. 开始加载 Ollama 嵌入模型...")
        # ✅ 使用本地的 Ollama 嵌入模型
        self.embeddings = OllamaEmbeddings(
            model="lrs33/bce-embedding-base_v1:latest",
            base_url="http://localhost:11434"
        )
        print("6. 嵌入模型加载完成，开始连接向量库...")

        #加载已有的向量数据库
        self.vector_store=Chroma(
            persist_directory=persist_directory,
            embedding_function=self.embeddings
        )
        print("7. 向量库连接完成")

        #创建检索器
        self.retriever=self.vector_store.as_retriever(
            search_kwargs={"k":3}
        )

        #定义回答提示词模板
        self.qa_prompt=ChatPromptTemplate.from_template(
            """
            你是一个专业的客服知识库助手。请**仅基于**以下参考资料回答用户问题。
            如果参考资料中没有相关信息，请如实告知用户，不要编造任何内容。

            【参考资料】
            {context}

            【用户问题】
            {question}

            【回答】
            """
        )

        self.model=None # 先准备一个放“大模型”的位置，现在是空的
        self.qa_chain=None # 先准备一个放“问答链”的位置，现在也是空的

    def set_model(self,model):
        """设置 LLM 模型实例"""
        self.model=model
        self.qa_chain=self.qa_prompt | self.model # 构建问答链

    def answer(self,question:str)->str:
        """回答用户问题"""
        if self.model is None:
            return "错误：知识库 Agent 未正确初始化 LLM 模型。"
        docs=self.retriever.invoke(question)

        if not docs:
            return "抱歉，我在知识库中没有找到与您问题相关的信息。"
            
        context = "\n\n---\n\n".join([doc.page_content for doc in docs])
        response = self.qa_chain.invoke({
            "context": context,
            "question": question
        })

        print(f"📚 [知识库检索] 命中 {len(docs)} 个相关文档片段")
        return response.content.strip()