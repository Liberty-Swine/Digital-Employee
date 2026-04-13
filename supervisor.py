# supervisor.py 主管节点,节点的职责是调用LLM来理解用户意图，其本身不直接回答用户
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from state import CustomerServiceState

# 意图识别提示词（复用你优化后的版本）
# supervisor.py（片段）
# supervisor.py（关键修改部分）

INTENT_PROMPT = ChatPromptTemplate.from_template("""
你是一个专业的客服意图分类专家。请仔细分析**对话历史**和**用户最新问题**，将其归类为以下四种意图之一。

**意图定义与硬边界：**
- **knowledge**: 询问**静态规则/文档**（如政策、说明、制度）。不需要查询动态业务数据。
- **action**: 针对**单个具体对象**的**精确操作**（查询/修改/创建）。对象必须可唯一标识（如订单号、工单号、手机号）。
  ✅ 正确示例："我要退货"、"订单 ORD-123 到哪了？"、"修改收货地址"
- **human**: 转人工、投诉、情绪宣泄。
- **data**: 针对**数据集合**的**聚合统计**（计数、求和、平均、分组、排序）。问题中必含**聚合关键词**（多少、几条、统计、数量、排名、总计）。
  ✅ 正确示例："过去一周有多少订单？"、"售后的工单有几条？"、"销量最高的商品是哪个？"

**🔥 冲突裁决铁律（必须遵守）：**
1. 若问题中**同时包含具体标识符（如订单号、工单号、手机号）** → **action**。
2. 若问题中**包含聚合关键词（多少、几条、统计、数量、总计、排名）且无具体标识符** → **data**。
3. 若问题为“查询订单”且无任何限定词，默认按 **action** 处理（要求提供订单号）。

【对话历史】
{history}

【用户最新问题】
{user_input}

请只输出一个单词：knowledge, action, human, 或 data。
意图：
""")

def create_supervisor_node(llm: ChatOllama):
    """创建主管节点（带上下文感知 + 规则兜底）"""
    chain = INTENT_PROMPT | llm

    def supervisor_node(state: CustomerServiceState):
        messages = state["messages"]
        
        # 提取最近 3 轮对话作为历史上下文
        history = ""
        for msg in messages[-6:]:  # 取最近6条消息（约3轮对话）
            role = "用户" if msg.type == "human" else "助手"
            history += f"{role}：{msg.content}\n"
        
        user_input = messages[-1].content
        
        # ✅ 规则兜底 1：明确要求转人工
        human_keywords = ["转人工", "人工客服", "投诉你们", "找人工"]
        if any(kw in user_input for kw in human_keywords):
            print(f"🧠 [主管] 规则触发：转人工关键词 -> human")
            return {"intent": "human"}
        
        # ✅ 规则兜底 2：聚合关键词 + 无具体标识符 → data
        agg_keywords = ["多少", "几条", "几个", "统计", "数量", "总计", "排名", "销量最高"]
        if any(kw in user_input for kw in agg_keywords) and not any(c.isdigit() for c in user_input):
            print(f"🧠 [主管] 规则触发：聚合关键词 -> data")
            return {"intent": "data"}
        
        # 正常 LLM 意图识别
        response = chain.invoke({
            "history": history if history else "无历史对话",
            "user_input": user_input
        })
        
        intent = response.content.strip().lower()
        valid_intents = ["knowledge", "action", "human", "data"]
        if intent not in valid_intents:
            intent = "human"
        
        print(f"🧠 [主管] 意图识别: '{user_input}' -> {intent}")
        return {"intent": intent}
    
    return supervisor_node