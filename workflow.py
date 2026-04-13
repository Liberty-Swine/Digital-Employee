# workflow.py
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver #导入 SQLite 检查点
import sqlite3         # 用于创建数据库连接
from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage

from state import CustomerServiceState
from supervisor import create_supervisor_node
from agents.knowledge import init_knowledge_node, knowledge_node
from agents.action import create_action_node
from agents.human import human_node
from agents.sql_agent import create_sql_node   # 🆕 导入 SQL 节点
import pymysql
from langgraph.checkpoint.mysql.pymysql import PyMySQLSaver

def build_workflow():
    """构建并编译 LangGraph 工作流"""
    
    # 1. 创建 LLM 实例（全局共享）
    llm = ChatOllama(
        model="qwen2.5:3b",
        base_url="http://localhost:11434",
        temperature=0
    )

    # 2. 初始化需要 LLM 的节点
    init_knowledge_node(llm, persist_dir="./chroma_db") # 创建 知识库 节点
    supervisor_node = create_supervisor_node(llm)
    action_node = create_action_node(llm) # 创建 售后 节点
    sql_node = create_sql_node(llm) # 创建 SQL 节点

    # 3. 构建图
    workflow = StateGraph(CustomerServiceState)

    # 添加节点
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("knowledge", knowledge_node)
    workflow.add_node("action", action_node)
    workflow.add_node("human", human_node)
    workflow.add_node("data", sql_node)

    # 设置入口
    workflow.set_entry_point("supervisor")

    # 定义路由函数
    def route_after_supervisor(state: CustomerServiceState):
        intent = state.get("intent", "human")
        if intent == "knowledge":
            return "knowledge"
        elif intent == "action":
            return "action"
        elif intent == "data":
            return "data"
        else:
            return "human"
    
    # 添加条件边
    workflow.add_conditional_edges("supervisor", route_after_supervisor)

    #专家节点执行完毕后结束
    workflow.add_edge("knowledge", END)
    workflow.add_edge("action", END)
    workflow.add_edge("human", END)
    workflow.add_edge("data", END)

    # 创建 MySQL 连接（必须设置 autocommit=True）
    conn = pymysql.connect(
        host="localhost",
        port=3306,
        user="root",
        password="123456",
        database="digital_employee",
        charset="utf8mb4",
        autocommit=True,          # 必须设置为 True
    )
    # 创建检查点保存器
    memory = PyMySQLSaver(conn)
    # 首次使用必须调用 setup() 创建表
    memory.setup()

    app = workflow.compile(checkpointer=memory)

    # 调试：打印每次更新后的消息数量
    def debug_print(state):
        print(f"🔍 当前 messages 数量: {len(state.get('messages', []))}")
        return state
    app = app.with_listeners(on_end=debug_print)

    return app