# agents/action.py
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage
from state import CustomerServiceState
import json
import random
from datetime import datetime
import requests

# API 基础地址
API_BASE_URL = "http://localhost:8000"

# ==================== 工具定义 ====================
@tool
def create_ticket(user_id: str, issue_type: str, description: str) -> str:
    """
    当用户要求创建工单、投诉、反馈问题或退货时调用。
    
    **参数获取优先级：**
    1. 从【对话历史】中提取已有的订单号作为 user_id 或补充信息。
    2. 如果历史中没有，再向用户询问。
    
    参数说明：
    - user_id: 用户ID或订单号（可从历史中提取）
    - issue_type: 问题类型，可选：退货、换货、维修、投诉、咨询
    - description: 问题的详细描述
    """
    try:
        response=requests.post(
            f"{API_BASE_URL}/ticket",
            json={
                "user_id": user_id,
                "issue_type": issue_type,
                "description": description
            },
            timeout=5
        )
        # 自动检查请求是否失败 4xx/5xx → 抛异常；2xx → 正常运行
        response.raise_for_status()
        raw_data = response.json()
        if isinstance(raw_data, str):
            data = json.loads(raw_data)
        else:
            data = raw_data
            
        if not isinstance(data, dict):
            return json.dumps({
                "status": "error",
                "message": f"API 返回格式异常：{type(data)}"
            }, ensure_ascii=False)
        print(f"📋 [真实API] 工单创建 -> ID: {data.get('ticket_id')}, 类型: {issue_type}")
        return json.dumps(data, ensure_ascii=False)
    #连接错误
    except requests.exceptions.ConnectionError:
        return json.dumps({
            "status": "error",
            "message": "无法连接到工单服务，请稍后重试。"
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"创建工单时发生错误：{str(e)}"
        }, ensure_ascii=False)

@tool
def query_order(order_id: str) -> str:
    """根据订单号查询订单的当前状态和物流信息。如果订单号未知或为空，请不要调用此工具，而是询问用户。"""
    if not order_id or order_id.strip() == "":
        return json.dumps({
            "status": "error",
            "message": "缺少订单号，无法查询。请提供有效的订单号。"
        }, ensure_ascii=False)
    try:
        response=requests.get(
            f"{API_BASE_URL}/order/{order_id}",
            timeout=5
        )
        # 自动检查请求是否失败 4xx/5xx → 抛异常；2xx → 正常运行
        response.raise_for_status()
        #强制检查 response.json() 的类型
        raw_data = response.json()
        print(f"🔍 [DEBUG] raw_data type: {type(raw_data)}, content: {raw_data}")
        
        # 如果返回的是字符串，尝试解析为 JSON
        if isinstance(raw_data, str):
            data = json.loads(raw_data)
        else:
            data = raw_data
        #校验格式
        if not isinstance(data, dict):
            return json.dumps({
                "status": "error",
                "message": f"API 返回格式异常：{type(data)}"
            }, ensure_ascii=False)
        
        # 没找到订单
        if data.get("status") == "not_found":
            return json.dumps(data, ensure_ascii=False)
        print(f"📦 [真实API] 查询订单 -> {order_id}: {data.get('order_status')}")
        return json.dumps(data, ensure_ascii=False)
    #连接错误
    except requests.exceptions.ConnectionError:
        return json.dumps({
            "status": "error",
            "message": "无法连接到订单服务，请稍后重试。"
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"查询订单时发生错误：{str(e)}"
        }, ensure_ascii=False)

tools = [create_ticket, query_order]

# ==================== 上下文提取辅助函数 ====================
def format_history(messages):
    """将消息列表格式化为文本历史，并高亮订单号"""
    history = ""
    for msg in messages:
        role = "用户" if msg.type == "human" else "助手"
        content = msg.content
        # 简单高亮：如果内容中包含订单号格式，添加提示
        if "ORD-" in content:
            content += " 【注意：此处包含订单号】"
        history += f"{role}：{content}\n"
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
- query_order: 当用户想查询订单状态、物流信息时使用。
- create_ticket: 当用户要求创建工单、投诉、反馈问题或退货时使用。

**🔥 最重要的规则（请务必遵守）：**
1. **优先从【对话历史】中提取订单号、用户ID等关键信息**，不要重复询问用户已经提供过的信息！
2. 如果历史中已经明确提到了订单号（如 ORD-20260411-1234），在执行退货、查询等操作时，直接使用该订单号，无需再次索要。
3. 只有在历史中**确实找不到**所需信息时，才向用户询问。

**工具调用指南：**
- 当用户说“退货”、“我要退货”、“把这个订单退了”等，如果历史中有订单号，直接调用 `create_ticket`，issue_type 填“退货”，description 填用户描述。
- 如果用户既没提供订单号，历史中也没有，则友好地询问订单号。

【对话历史】
{history}

**请仔细阅读历史，提取其中的订单号、用户ID等信息。**"""

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