# action_agent.py
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import json
import random
from datetime import datetime

class ActionAgent:
    """售后执行专家：负责处理退货、查询订单、创建工单等具体操作"""

    def __init__(self,model:ChatOllama):
        self.model=model
        # 定义该 Agent 可用的工具集合
        self.tools = [
            self._create_ticket_tool(),
            self._query_order_tool()
        ]
        # 构建 Agent 执行器
        self.agent_executor = self._build_agent()
    
    #创建订单的工具
    def _create_ticket_tool(self):
        """封装工具：创建工单"""
        @tool
        def create_ticket(user_id: str, issue_type: str, description: str) -> str:
            """
            当用户明确要求创建工单、反馈问题、投诉或记录售后请求时调用。
            参数说明：
            - user_id: 用户ID或手机号
            - issue_type: 问题类型，可选：退货、换货、维修、投诉、咨询
            - description: 问题的详细描述
            返回：工单创建结果，包含工单ID和状态。
            """
            # 模拟工单创建逻辑（实际可替换为真实API调用）
            ticket_id = f"TKT-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
            print(f"📋 [模拟] 工单已创建 -> ID: {ticket_id}, 类型: {issue_type}, 用户: {user_id}")
            return json.dumps({
                "status": "success",
                "ticket_id": ticket_id,
                "message": f"您的{issue_type}工单已创建，客服将尽快处理。"
            }, ensure_ascii=False)
        
        return create_ticket

    #创建查询订单的工具
    def _query_order_tool(self):
        """封装工具：查询订单状态"""
        @tool
        def query_order(order_id:str)->str:
            """
            根据订单号查询订单的当前状态和物流信息。
            参数说明：
            - order_id: 订单号，如 ORD-20260411-1234
            返回：订单状态、物流详情等。
            """

            # 模拟订单数据（实际可接入真实数据库或API）
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
            #根据id去查询订单
            order =mock_orders.get(order_id)
            if not order:
                return json.dumps({
                    "status": "not_found",
                    "message": f"未找到订单 {order_id}，请确认订单号是否正确。"
                }, ensure_ascii=False)
            print(f"📦 [模拟] 查询订单 -> {order_id}: {order['status']}")
            #返回结果
            return json.dumps({
                "status": "success",
                "order_id": order_id,
                "order_status": order["status"],
                "logistics": order["logistics"],
                "items": order["items"]
            }, ensure_ascii=False)
        return query_order


    def _build_agent(self):
        """构建 LangChain Agent 执行器"""
        prompt=ChatPromptTemplate.from_messages(
            [
                (
                    "system", """你是一个专业的售后执行专家。你可以使用以下工具：
                    - create_ticket: 当用户要求创建工单、投诉、反馈问题时使用。
                    - query_order: 当用户想查询订单状态、物流信息时使用。

                    **重要规则：**
                    1. 如果用户提供了订单号，优先使用 query_order 查询。
                    2. 如果用户描述了问题但未提供订单号，可以先询问订单号再查询，或直接为其创建工单。
                    3. 工具调用成功后，用友好的语言将结果告知用户。
                    4. 不要编造任何未通过工具确认的信息。
                        """),
                        ("user", "{input}"),
                        MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        agent=create_tool_calling_agent(
            llm=self.model,
            tools=self.tools,
            prompt=prompt
        )

        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            erbose=True, # 打印详细的执行过程，便于调试
            handle_parsing_errors=True,
            max_iterations=3
        )
    

    def execute(self, user_input: str) -> str:
        """
        执行用户请求的操作
        :param user_input: 用户原始输入
        :return: Agent 处理后的回复
        """
        try:
            result = self.agent_executor.invoke({"input": user_input})
            return result["output"]
        except Exception as e:
            return f"【售后执行专家】操作失败：{str(e)}"