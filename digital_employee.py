# digital_employee.py
# 这是你项目的“骨架”，只定义最基本的流程
print("1. 开始导入模块...")
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

#导入知识库模块
from knowledge_agent import KnowledgeAgent
#导入售后执行模块
from action_agent import ActionAgent

print("2. 模块导入完成")

print("3. 初始化模型...")
#初始化模型
model = ChatOllama(
    model="qwen2.5:3b", #模型名称
    base_url="http://localhost:11434", #url
    temperature=0 # 设为0，让模型输出更确定
)
print("4. 模型初始化完成")

#定义意图识别的提示词模板
intent_prompt=ChatPromptTemplate.from_template(
    """
        你是一个专业的客服意图分类专家。请仔细分析用户的问题，并将其归类为以下三种意图之一。

        **意图定义与示例：**
        - knowledge: 用户想**了解或查询**信息，包括政策、规定、产品说明、使用方法等。用户**没有**直接提出要执行某个操作。
        - ✅ 示例："你们的退货政策是什么？"、"这个产品怎么使用？"、"保修期是多久？"
        - action: 用户**明确要求执行**一个具体操作，如退货、修改订单、查询物流、创建工单等。用户的目的是**让系统做某件事**。
        - ✅ 示例："我要退货"、"帮我查一下订单12345到哪了？"、"修改我的收货地址"
        - human: 用户情绪激动、明确要求人工客服，或问题复杂无法简单归类。
        - ✅ 示例："我要投诉"、"转人工"、"你们这什么破服务！"

        **重要提示：**
        - 询问政策、规定的句子（例如"你们的退货政策是什么？"）属于 `knowledge`，因为它是在**了解信息**。
        - 表达执行意愿的句子（例如"我要退货"）属于 `action`，因为它是在**发起操作**。

        请只输出一个单词：knowledge, action, 或 human。

        用户问题：{user_input}
        意图：
    """
)

#创建意图识别链
intent_chain=intent_prompt | model

def llm_route(user_input:str)-> str:
    """使用 LLM 进行意图识别，返回 'knowledge', 'action', 'human' 之一"""
    response=intent_chain.invoke({"user_input":user_input})
    intent=response.content.strip().lower()
    #简单校验，防止模型输出意外内容
    if intent not in ["knowledge", "action", "human"]:
        intent="human" # 默认转人工
    return intent



class SimpleCoordinator:
    """升级版主管：使用LLM进行智能路由"""
    def __init__(self,model):
        self.model=model
        #保留规则做为后备
        self.fallback_routes={
            "退货": "action",
            "订单": "action",
            "投诉": "human"
        }
        #初始化知识库agent
        self.knowledge_agent=KnowledgeAgent(persist_directory="./chroma_db")
        self.knowledge_agent.set_model(self.model)
        #初始化售后模块
        self.action_agent = ActionAgent(self.model)
        # 占位：后续实现

        self.human_agent = None

    def route(self,user_input:str)-> dict:
        try:
            intent=llm_route(user_input)
            print(f"🧠 [LLM 意图识别] 输入: '{user_input}' -> 意图: {intent}")
        except Exception as e:
            print(f"⚠️ LLM 调用失败，降级为规则路由。错误: {e}")
            # 降级逻辑：如果 LLM 出问题，回退到关键词规则
            intent = "human"  # 默认值
            for keyword, fallback_intent  in self.fallback_routes.items():
                if keyword in user_input:
                    intent = fallback_intent
                    break

        if intent=="knowledge":
            answer=self.knowledge_agent.answer(user_input)
        elif intent == "action":
            answer = self.action_agent.execute(user_input)
        elif intent == "human":
            answer = "【人工客服】正在为您转接人工坐席，请稍候..."
        else:
            answer = "抱歉，我无法理解您的意图。"

        return {"intent": intent, "answer": answer}
    
#模拟运行
if __name__ =="__main__" :
    model = ChatOllama(
        model="qwen2.5:3b", #模型名称
        base_url="http://localhost:11434", #url
        temperature=0 # 设为0，让模型输出更确定
    )

    coordinator=SimpleCoordinator(model)
    test_inputs = [
        "帮我查一下订单 ORD-20260411-1234",
        "我的订单号是 ORD-20260410-5678，怎么还没发货",
        "订单 ORD-999 找不到",
        "我想退货",
        "你们的退货政策是什么？",
        "我要投诉",
        "我的订单号是12345，到哪里了？"
    ]

    print("="*50)
    print("🤖 数字员工系统测试")
    print("="*50)

    for text in test_inputs:
        result = coordinator.route(text)
        print(f"用户输入: '{text}'")
        print(f"路由意图: {result['intent']}")
        print(f"回答: {result['answer']}\n")
        print("-" * 50)