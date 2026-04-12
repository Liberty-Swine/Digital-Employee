# supervisor.py 主管节点,节点的职责是调用LLM来理解用户意图，其本身不直接回答用户
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from state import CustomerServiceState

# 意图识别提示词（复用你优化后的版本）
# supervisor.py（片段）
# supervisor.py（关键修改部分）

INTENT_PROMPT = ChatPromptTemplate.from_template("""
你是一个专业的客服意图分类专家。请仔细分析**对话历史**和**用户最新问题**，将其归类为以下三种意图之一。

**意图定义与核心区别：**
- **knowledge**: 用户想了解**静态知识、公司政策、产品说明、规章制度**。这类信息通常记录在文档中，**不需要调用业务系统查询实时数据**。
  ✅ 正确示例："退货政策是什么？"、"保修期多久？"、"怎么使用产品？"
  
- **action**: 用户要求执行一个**具体的业务操作**，包括**创建、修改、查询动态数据**（如订单状态、物流信息、工单记录、会员积分）。**任何涉及特定订单号、手机号、工单号的查询都属于 action**。
  ✅ 正确示例："我要退货"、"帮我查一下订单12345"、"我的订单发货了吗？"、"修改收货地址"、"查询物流"、"查积分"
  ❌ 易错辨析：即使用户使用了“查询”一词，只要查询的对象是**动态业务数据**（如某笔订单），就属于 **action**，因为它需要调用业务系统。

- **human**: 用户情绪激动、明确要求人工客服、或问题超出能力范围。
  ✅ 正确示例："我要投诉"、"转人工"、"你们太差了"

**易混淆案例强制规则：**
| 用户问题 | 正确答案 | 理由 |
| :--- | :--- | :--- |
| "查询订单 ORD-1234" | **action** | 查询特定订单的动态状态 |
| "查询退货政策" | **knowledge** | 查询静态的公司政策 |
| "我的订单到哪了？" | **action** | 查询物流动态信息 |
| "订单一般几天到？" | **knowledge** | 询问一般规则，不涉及具体订单 |

**重要上下文规则：**
- 如果对话历史中助手刚询问了订单号，用户回复了一串数字或订单号，**意图应与上一轮保持一致（通常为 action）**。

【对话历史】
{history}

【用户最新问题】
{user_input}

请只输出一个单词：knowledge, action, 或 human。
意图：
""")

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