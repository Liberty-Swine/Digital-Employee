# app.py

# 初始版本
# import streamlit as st
# from langchain_ollama import ChatOllama
# from digital_employee import SimpleCoordinator

# # 页面配置
# st.set_page_config(page_title="极客科技·数字员工", page_icon="🤖")
# st.title("🤖 极客科技·智能客服")

# # 初始化模型和主管（使用缓存，避免每次交互都重新加载）
# @st.cache_resource
# def load_coordinator():
#     model = ChatOllama(
#         model="qwen2.5:3b",
#         base_url="http://localhost:11434",
#         temperature=0
#     )
#     return SimpleCoordinator(model)

# coordinator = load_coordinator()

# # 初始化会话消息历史
# if "messages" not in st.session_state:
#     st.session_state.messages = [
#         {"role": "assistant", "content": "您好！我是极客科技的智能客服。您可以向我咨询政策、查询订单或反馈问题。"}
#     ]

# # 显示历史消息
# for msg in st.session_state.messages:
#     with st.chat_message(msg["role"]):
#         st.markdown(msg["content"])

# # 接收用户输入
# if prompt := st.chat_input("请输入您的问题..."):
#     # 显示用户消息
#     st.session_state.messages.append({"role": "user", "content": prompt})
#     with st.chat_message("user"):
#         st.markdown(prompt)
    
#     # 调用主管处理
#     with st.chat_message("assistant"):
#         with st.spinner("思考中..."):
#             result = coordinator.route(prompt)
#             answer = result["answer"]
#             intent = result["intent"]
            
#             # 可选：显示内部意图（调试用，正式可隐藏）
#             with st.expander("🔍 内部信息", expanded=False):
#                 st.write(f"意图识别：{intent}")
            
#             st.markdown(answer)
    
#     st.session_state.messages.append({"role": "assistant", "content": answer})


# 升级版本
# app.py
import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from workflow import build_workflow

st.set_page_config(page_title="极客科技·数字员工", page_icon="🤖")
st.title("🤖 极客科技·智能客服 (LangGraph版)")

@st.cache_resource
def load_app():
    return build_workflow()

app = load_app()

# 初始化会话
if "thread_id" not in st.session_state:
    st.session_state.thread_id = "user_session_1"
    st.session_state.messages = [
        {"role": "assistant", "content": "您好！我是极客科技的智能客服。您可以向我咨询政策、查询订单或反馈问题。"}
    ]

# 显示历史消息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 接收用户输入
if prompt := st.chat_input("请输入您的问题..."):
    # 显示用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 调用 LangGraph 工作流
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            # 构建输入状态
            input_state = {
                "messages": [HumanMessage(content=prompt)]
            }
            # 执行图，传入 thread_id 以支持记忆
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            result = app.invoke(input_state, config)
            
            answer = result.get("final_response", "抱歉，我暂时无法处理您的问题。")
            st.markdown(answer)
    
    st.session_state.messages.append({"role": "assistant", "content": answer})