# agents/action.py
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage
from state import CustomerServiceState
import json
import random
from datetime import datetime

# ==================== 工具定义 ====================
@tool
def create_ticket(user_id: str, issue_type: str, description: str) -> str:
    """当用户明确要求创建工单、反馈问题、投诉或记录售后请求时调用。"""
    ticket_id = f"TKT-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
    print(f"📋 [模拟] 工单已创建 -> ID: {ticket_id}, 类型: {issue_type}, 用户: {user_id}")
    return json.dumps({
        "status": "success",
        "ticket_id": ticket_id,
        "message": f"您的{issue_type}工单已创建，客服将尽快处理。"
    }, ensure_ascii=False)

@tool
def query_order(order_id: str) -> str:
    """根据订单号查询订单的当前状态和物流信息。"""
    mock_orders = {
        "ORD-20260411-1234": {
            "status": "已发货",
            "logistics": "中通快递 运单号：ZT123456789，预计4月13日送达",
            "items": "极客智能音箱 x1"
        },
        "ORD-20260410-5678": {
            "status": "待发货",
            "logistics": "仓库处理中，预计今日发货",
            "items": "极客无线耳机 x2"
        }
    }
    order = mock_orders.get(order_id)
    if not order:
        return json.dumps({"status": "not_found", "message": f"未找到订单 {order_id}"}, ensure_ascii=False)
    print(f"📦 [模拟] 查询订单 -> {order_id}: {order['status']}")
    return json.dumps({"status": "success", "order_id": order_id, **order}, ensure_ascii=False)

tools = [create_ticket, query_order]

# ==================== 上下文提取辅助函数 ====================
def format_history(messages):
    """将消息列表格式化为文本历史"""
    history = ""
    for msg in messages:
        role = "用户" if msg.type == "human" else "助手"
        history += f"{role}：{msg.content}\n"
    return history

def extract_context(messages, max_messages=12):
    """智能提取上下文：保留第一条用户消息 + 最近 N-2 条消息"""
    if len(messages) <= max_messages:
        return format_history(messages)
    
    # 找到第一条用户消息（通常是核心诉求）
    first_user_msg = next((m for m in messages if m.type == "human"), None)
    recent = messages[-(max_messages - 2):]  # 留出空间给第一条消息
    
    preserved = []
    if first_user_msg and first_user_msg not in recent:
        preserved.append(first_user_msg)
    preserved.extend(recent)
    
    return format_history(preserved)

# ==================== 节点创建函数 ====================
def create_action_node(llm: ChatOllama):
    """创建售后执行节点（带工具绑定的 Agent）"""
    from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

    # ✅ 修复：提示词顶格书写，避免缩进污染
    system_prompt = """你是一个专业的售后执行专家。你可以使用以下工具：
- create_ticket: 当用户要求创建工单、投诉、反馈问题时使用。
- query_order: 当用户想查询订单状态、物流信息时使用。

**重要规则：**
1. 仔细阅读【对话历史】，理解用户的指代关系（如“这个订单”、“它”等）。
2. 如果历史中已提及订单号、用户ID等关键信息，请直接使用，无需重复询问。
3. 工具调用成功后，用友好的语言将结果告知用户。
4. 不要编造任何未通过工具确认的信息。

【对话历史】
{history}"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=3
    )

    def action_node(state: CustomerServiceState):
        messages = state["messages"]
        # ✅ 优化：使用智能上下文提取替代固定窗口
        history = extract_context(messages, max_messages=12)
        
        user_input = messages[-1].content
        result = executor.invoke({
            "history": history if history else "无历史对话",
            "input": user_input
        })
        answer = result["output"]
        print(f"🛠️ [售后专家] 已执行操作")
        return {
            "final_response": answer,
            "messages": [AIMessage(content=answer)]
        }

    return action_node