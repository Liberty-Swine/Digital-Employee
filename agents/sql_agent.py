# agents/sql_agent.py
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_classic.agents import create_sql_agent 
from langchain_classic.agents.agent_types import AgentType
from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage
from state import CustomerServiceState
import os

# 数据库连接配置（从环境变量读取）
# DB_URI = os.environ.get(
#     "MYSQL_URI",
#     "mysql+pymysql://root:root123@localhost:3306/digital_employee"
# )

DB_URI = "mysql+pymysql://root:123456@localhost:3306/digital_employee"


class SQLAgent:
    """数据分析专家：负责查询数据库、统计数据"""
    
    def __init__(self, llm: ChatOllama):
        self.llm = llm
        self.db = SQLDatabase.from_uri(DB_URI)
        self.toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
        self.agent_executor = self._build_agent()
    
    def _build_agent(self):
        from langchain_core.prompts import PromptTemplate
    
        prefix = """你是一个专业的数据分析助手，能够将自然语言问题转换为 SQL 查询并执行。
    **重要规则**：
    - 请用中文回答用户的问题。
    - 只返回最终查询结果，不要输出 SQL 语句、推理过程或解释。
    - 如果查询结果是数字，直接说“共有 X 条记录”。
    - 如果查询结果为空，说“没有找到相关记录”。
    """
        return create_sql_agent(
            llm=self.llm,
            toolkit=self.toolkit,
            agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            prefix=prefix,  # 自定义前缀提示
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5,
            max_execution_time=30,
        )
    
    def query(self, question: str) -> str:
        """执行自然语言查询，返回结果"""
        try:
            result = self.agent_executor.invoke({"input": question})
            # 输出可能包含 'output' 或 'final_output'，我们做兼容处理
            output = result.get("output") or result.get("final_output") or str(result)
            # 如果输出中包含 SQL 语句但未给出数字，尝试补充提示让模型总结
            if "SELECT" in output and "COUNT" in output and not any(char.isdigit() for char in output[-20:]):
                # 输出中没有数字，可能是模型忘记给出最终答案，我们主动要求总结
                follow_up = f"请根据以上查询结果，用中文直接回答数字。"
                follow_result = self.agent_executor.invoke({"input": follow_up})
                output = follow_result.get("output") or follow_result.get("final_output") or output
            return output
        except Exception as e:
            return f"数据查询失败：{str(e)}"

def create_sql_node(llm: ChatOllama):
    """创建 SQL 专家节点（供 LangGraph 使用）"""
    sql_agent = SQLAgent(llm)
    
    def sql_node(state: CustomerServiceState):
        user_question = state["messages"][-1].content
        print(f"📊 [SQL专家] 收到查询: {user_question}")
        answer = sql_agent.query(user_question)
        print(f"📊 [SQL专家] 返回结果")
        return {
            "final_response": answer,
            "messages": [AIMessage(content=answer)]
        }
    
    return sql_node