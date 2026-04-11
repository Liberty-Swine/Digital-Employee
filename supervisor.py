# supervisor.py 主管节点,节点的职责是调用LLM来理解用户意图，其本身不直接回答用户
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from state import CustomerServiceState

# 意图识别提示词（复用你优化后的版本）
# supervisor.py（片段）
INTENT_PROMPT = ChatPromptTemplate.from_template(
    """
    你是一个专业的客服意图分类专家。请仔细分析**对话历史**和**用户最新问题**，将其归类为以下三种意图之一。

    **意图定义与示例：**
    - knowledge: 用户想**了解或查询**公司的**静态知识、政策、说明**。这类信息通常记录在文档或规章中，不需要调用业务系统。
    ✅ 示例："你们的退货政策是什么？"、"这个产品怎么使用？"、"保修期是多久？"

    - action: 用户要求执行一个**具体的业务操作**，包括创建、修改、查询**动态数据**（如订单状态、物流信息、工单记录）。
    ✅ 示例："我要退货"、"帮我查一下订单12345到哪了？"、"我的订单发货了吗？"、"修改我的收货地址"

    - human: 用户情绪激动、明确要求人工客服，或问题复杂无法简单归类。
    ✅ 示例："我要投诉"、"转人工"、"你们这什么破服务！"

    **关键区分规则：**
    - 如果问题涉及**实时数据**（如某订单的物流状态、某工单的处理进度），属于 `action`，因为需要调用业务系统查询。
    - 如果问题涉及**固定规章**（如退货条件、保修期限），属于 `knowledge`，因为可从文档中检索。
    - 如果用户的最新回复是对上一轮追问的回答（例如提供订单号），**意图应与上一轮保持一致**。

    【对话历史】
    {history}

    【用户最新问题】
    {user_input}

    请只输出一个单词：knowledge, action, 或 human。
    意图：
    """
)

def create_supervisor_node(llm:ChatOllama):
    """创建主管节点（带上下文感知）"""
    chain = INTENT_PROMPT | llm

    def supervisor_node(state: CustomerServiceState):
        messages = state["messages"]
        
        # 提取最近 3 轮对话作为历史上下文
        history = ""
        for msg in messages[-6:]:  # 取最近6条消息（约3轮对话）
            role = "用户" if msg.type == "human" else "助手"
            history += f"{role}：{msg.content}\n"
        #用户输入
        user_input = messages[-1].content
        response = chain.invoke({
            "history": history if history else "无历史对话",
            "user_input": user_input
        })

        intent = response.content.strip().lower()
        if intent not in ["knowledge", "action", "human"]:
            intent = "human"

        print(f"🧠 [主管] 意图识别: '{user_input}' -> {intent}")
        return {"intent": intent}

    return supervisor_node