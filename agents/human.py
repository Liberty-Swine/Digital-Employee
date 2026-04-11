# agents/human.py
from langchain_core.messages import AIMessage
from state import CustomerServiceState

def human_node(state: CustomerServiceState):
    """人工客服节点（占位）"""
    answer = "正在为您转接人工客服，请稍候..."
    print(f"👤 [人工客服] 转接中")
    return {
        "final_response": answer,
        "messages": [AIMessage(content=answer)]
    }