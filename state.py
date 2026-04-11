# state.py 定义共享状态，整个流程的数据中枢
from typing import TypedDict, Optional, List, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class CustomerServiceState(TypedDict):
    # 消息历史，使用 add_messages 自动合并
    messages: Annotated[List[BaseMessage],add_messages]
    
    # 业务字段
    intent: Optional[str]             # 识别的意图
    knowledge_context: Optional[str]  # RAG检索出的上下文
    action_result: Optional[str]      # 工具执行的结果
    final_response: Optional[str]     # 最终回复