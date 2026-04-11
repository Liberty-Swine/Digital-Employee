# agents/knowledge.py
from langchain_core.messages import AIMessage
from langchain_ollama import ChatOllama
from state import CustomerServiceState
from knowledge_agent import KnowledgeAgent

_knowledge_agent:KnowledgeAgent=None

def init_knowledge_node(llm: ChatOllama, persist_dir: str = "./chroma_db"):
    """初始化知识库节点（在图构建时调用）"""
    global _knowledge_agent
    _knowledge_agent = KnowledgeAgent(persist_directory=persist_dir)
    _knowledge_agent.set_model(llm)

def knowledge_node(state: CustomerServiceState):
    """知识库专家节点"""
    user_question = state["messages"][-1].content
    answer = _knowledge_agent.answer(user_question)
    print(f"📚 [知识库专家] 已生成回答")
    return {
        "final_response": answer,
        "messages": [AIMessage(content=answer)]
    }