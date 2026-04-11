# workflow.py
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage

from state import CustomerServiceState
from supervisor import create_supervisor_node
from agents.knowledge import init_knowledge_node, knowledge_node
from agents.action import create_action_node
from agents.human import human_node

def build_workflow():
    """构建并编译 LangGraph 工作流"""
    
    # 1. 创建 LLM 实例（全局共享）
    llm = ChatOllama(
        model="qwen2.5:3b",
        base_url="http://localhost:11434",
        temperature=0
    )

    # 2. 初始化需要 LLM 的节点
    init_knowledge_node(llm, persist_dir="./chroma_db")
    supervisor_node = create_supervisor_node(llm)
    action_node = create_action_node(llm)

    # 3. 构建图
    workflow = StateGraph(CustomerServiceState)

    # 添加节点
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("knowledge", knowledge_node)
    workflow.add_node("action", action_node)
    workflow.add_node("human", human_node)

    # 设置入口
    workflow.set_entry_point("supervisor")

    # 定义路由函数
    def route_after_supervisor(state: CustomerServiceState):
        intent = state.get("intent", "human")
        if intent == "knowledge":
            return "knowledge"
        elif intent == "action":
            return "action"
        else:
            return "human"
    
    # 添加条件边
    workflow.add_conditional_edges("supervisor", route_after_supervisor)

    #专家节点执行完毕后结束
    workflow.add_edge("knowledge", END)
    workflow.add_edge("action", END)
    workflow.add_edge("human", END)

     # 编译（带记忆）
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)

    return app