# agents/human.py
from langchain_core.messages import AIMessage
from langgraph.types import interrupt
from state import CustomerServiceState
from langgraph.errors import GraphInterrupt  # 用于兜底抛出

def human_node(state: CustomerServiceState):
    """人工客服节点：暂停流程，等待人工输入"""
    print("👤 [human_node] ========== 被调用 ==========")
    user_question = state["messages"][-1].content

    # 提取最近几轮对话作为上下文，方便人工客服了解情况
    history = []
    for msg in state["messages"][-6:]:
        role = "用户" if msg.type == "human" else "助手"
        history.append(f"{role}：{msg.content}")
    context = "\n".join(history)

    print("🛑 [human_node] 即将调用 interrupt，期望抛出 GraphInterrupt 异常")
    # 🛑 中断执行，等待外部恢复
    human_response = interrupt({
        "type": "need_human",
        "user_question": user_question,
        "context": context,
        "message": "用户请求转接人工客服，请人工介入处理。"
    })

    # ⚠️ 如果代码执行到了这里，说明 interrupt 没有抛出异常（异常被吞了）
    print("❌ [human_node] interrupt 未抛出异常！手动抛出 GraphInterrupt")
    # 手动抛出异常，确保流程被中断
    raise GraphInterrupt({
        "type": "need_human",
        "user_question": user_question,
        "context": context,
    })

    # 下面的代码永远不会执行，仅作语法占位
    # 当外部调用 Command(resume=...) 后，human_response 会被注入恢复值
    answer = human_response if human_response else "人工客服暂时无法响应，请稍后再试。"
    
    print(f"👤 [人工客服] 已收到人工回复：{answer[:50]}...")
    
    return {
        "final_response": answer,
        "messages": [AIMessage(content=answer)]
    }