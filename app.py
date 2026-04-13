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


# 升级版本 添加人工客服版本
# app.py
# import streamlit as st
# from langchain_core.messages import HumanMessage, AIMessage
# from langgraph.types import Command
# from langgraph.errors import GraphInterrupt
# from workflow import build_workflow
# import uuid

# st.set_page_config(page_title="极客科技·数字员工", page_icon="🤖")
# st.title("🤖 极客科技·智能客服")

# @st.cache_resource
# def load_app():
#     return build_workflow()

# app = load_app()

# # 初始化会话状态
# if "thread_id" not in st.session_state:
#     st.session_state.thread_id = str(uuid.uuid4())
#     st.session_state.messages = [
#         {"role": "assistant", "content": "您好！我是极客科技的智能客服。您可以向我咨询政策、查询订单或反馈问题。"}
#     ]
#     st.session_state.interrupted = False
#     st.session_state.interrupt_data = None

# # 显示历史消息
# for msg in st.session_state.messages:
#     with st.chat_message(msg["role"]):
#         st.markdown(msg["content"])

# # 正常用户输入（仅在非中断状态下显示）
# if not st.session_state.interrupted:
#     if prompt := st.chat_input("请输入您的问题..."):
#         st.session_state.messages.append({"role": "user", "content": prompt})
#         with st.chat_message("user"):
#             st.markdown(prompt)

#         with st.chat_message("assistant"):
#             with st.spinner("思考中..."):
#                 input_state = {"messages": [HumanMessage(content=prompt)]}
#                 config = {"configurable": {"thread_id": st.session_state.thread_id}}

#                 try:
#                     result = app.invoke(input_state, config)

#                     # 兼容某些版本可能返回字典包含 __interrupt__ 的情况
#                     if isinstance(result, dict) and "__interrupt__" in result:
#                         interrupt_info = result["__interrupt__"][0]
#                         # 若是 Interrupt 对象则取 value，否则直接使用
#                         interrupt_data = interrupt_info.value if hasattr(interrupt_info, 'value') else interrupt_info
#                         st.session_state.interrupted = True
#                         st.session_state.interrupt_data = interrupt_data
#                         st.rerun()  # 立即刷新

#                     # 正常返回
#                     answer = result.get("final_response", "抱歉，我暂时无法处理您的问题。")
#                     st.markdown(answer)
#                     st.session_state.messages.append({"role": "assistant", "content": answer})

#                 except GraphInterrupt as e:
#                     print("🔥 [app] 成功捕获 GraphInterrupt 异常")
#                     interrupt_obj = e.interrupts[0]
#                     # 从 Interrupt 对象中提取实际数据
#                     interrupt_data = interrupt_obj.value if hasattr(interrupt_obj, 'value') else interrupt_obj
#                     st.session_state.interrupted = True
#                     st.session_state.interrupt_data = interrupt_data
#                     st.rerun()  # 立即刷新

#                 except Exception as e:
#                     print(f"❌ 未预期的错误：{type(e).__name__} - {e}")
#                     st.error(f"系统遇到了一点问题，请稍后重试。")

# # 人工客服回复区域（仅在中断状态下显示）
# else:
#     st.warning("👤 当前为人工客服模式，请输入您的回复...")
#     if st.session_state.interrupt_data:
#         user_q = st.session_state.interrupt_data.get('user_question', '')
#         st.info(f"**用户问题：** {user_q}")

#     human_reply = st.chat_input("人工客服输入回复...")
#     if human_reply:
#         st.session_state.messages.append({"role": "assistant", "content": f"【人工客服】{human_reply}"})

#         config = {"configurable": {"thread_id": st.session_state.thread_id}}
#         try:
#             # 恢复执行，传入人工回复
#             result = app.invoke(Command(resume=human_reply), config)
#         except Exception as e:
#             st.error(f"恢复执行失败：{e}")

#         st.session_state.interrupted = False
#         st.session_state.interrupt_data = None
#         st.rerun()


# app.py 添加用户登录模块
# import streamlit as st
# from langchain_core.messages import HumanMessage, AIMessage
# from langgraph.types import Command
# from langgraph.errors import GraphInterrupt
# from workflow import build_workflow
# import uuid
# import requests
# import threading
# import time
# import os

# #禁用追踪器,有兼容性问题
# os.environ["LANGCHAIN_TRACING_V2"] = "false"

# BACKEND_URL = "http://localhost:8000"

# st.set_page_config(page_title="极客科技·数字员工", page_icon="🤖")

# def log_conversation_async(thread_id, role, content, intent=None):
#     """异步记录对话，不阻塞主线程"""
#     def _log():
#         try:
#             payload = {"thread_id": thread_id, "role": role, "content": content}
#             if intent:
#                 payload["intent"] = intent
#             requests.post(f"{BACKEND_URL}/admin/conversation/log", json=payload, timeout=2)
#         except Exception as e:
#             print(f"⚠️ 记录对话失败: {e}")
#     threading.Thread(target=_log, daemon=True).start()

# # ==================== 用户登录 ====================
# if "user" not in st.session_state:
#     st.session_state.user = None

# if st.session_state.user is None:
#     st.title("🔐 登录 · 极客科技智能客服")
#     username = st.text_input("请输入您的用户名（任意非空字符）", key="login_input")
#     if st.button("进入系统") and username.strip():
#         st.session_state.user = username.strip()
#         # 为每个用户生成唯一的 thread_id 前缀
#         st.session_state.user_prefix = f"{st.session_state.user}_{str(uuid.uuid4())[:8]}"
#         st.rerun()
#     st.stop()


# # ==================== 主应用（登录后） ====================
# st.title(f"🤖 极客科技·智能客服")
# st.caption(f"👤 当前用户：{st.session_state.user}")

# @st.cache_resource
# def load_app():
#     return build_workflow()

# app = load_app()

# # 初始化会话状态（每个用户独立）
# if "thread_id" not in st.session_state:
#     # thread_id 结合用户名，确保不同用户状态隔离
#     st.session_state.thread_id = f"{st.session_state.user_prefix}_session"
#     st.session_state.messages = [
#         {"role": "assistant", "content": f"您好 {st.session_state.user}！我是极客科技的智能客服。您可以向我咨询政策、查询订单或反馈问题。"}
#     ]
#     st.session_state.interrupted = False
#     st.session_state.interrupt_data = None

# # 显示历史消息
# for msg in st.session_state.messages:
#     with st.chat_message(msg["role"]):
#         st.markdown(msg["content"])

# # 正常用户输入（仅在非中断状态下显示）
# if not st.session_state.interrupted:
#     if prompt := st.chat_input("请输入您的问题..."):
#         st.session_state.messages.append({"role": "user", "content": prompt})
#         log_conversation_async(st.session_state.thread_id, "user", prompt)  # 保持日志记录
        
#         with st.chat_message("user"):
#             st.markdown(prompt)

#         with st.chat_message("assistant"):
#             message_placeholder = st.empty()  # 用于流式更新
#             full_response = ""
            
#             with st.spinner("思考中..."):
#                 input_state = {"messages": [HumanMessage(content=prompt)]}
#                 config = {"configurable": {"thread_id": st.session_state.thread_id}}

#                 try:
#                     # 一次性获取完整回答（非流式）
#                     result = app.invoke(input_state, config)
                    
#                     # 检查中断（与之前逻辑完全一致）
#                     if isinstance(result, dict) and "__interrupt__" in result:
#                         interrupt_info = result["__interrupt__"][0]
#                         interrupt_data = interrupt_info.value if hasattr(interrupt_info, 'value') else interrupt_info
#                         st.session_state.interrupted = True
#                         st.session_state.interrupt_data = interrupt_data
#                         st.rerun()
#                     full_response = result.get("final_response", "抱歉，我暂时无法处理您的问题。")
                    
#                 except GraphInterrupt as e:
#                     interrupt_obj = e.interrupts[0]
#                     interrupt_data = interrupt_obj.value if hasattr(interrupt_obj, 'value') else interrupt_obj
#                     st.session_state.interrupted = True
#                     st.session_state.interrupt_data = interrupt_data
#                     st.rerun()
                    
#                 except Exception as e:
#                     full_response = f"系统遇到了一点问题，请稍后重试。"
#                     print(f"❌ 未预期的错误：{type(e).__name__} - {e}")
            
#             # 🆕 流式显示完整回答（模拟打字机）
#             if full_response:
#                 displayed = ""
#                 # 控制打字速度（字符/秒），可调整 计算动态延迟：短文本稍慢，长文本稍快
#                 base_delay = 0.03
#                 if len(full_response) > 200:
#                     delay_per_char = 0.015
#                 elif len(full_response) > 100:
#                     delay_per_char = 0.02
#                 else:
#                     delay_per_char = 0.03
#                 for char in full_response:
#                     displayed += char
#                     message_placeholder.markdown(displayed + "▌")
#                     time.sleep(delay_per_char)
#                 message_placeholder.markdown(full_response)  # 最终去掉光标
#             else:
#                 message_placeholder.markdown("抱歉，我暂时无法处理您的问题。")
#                 full_response = "抱歉，我暂时无法处理您的问题。"
#             # 记录助手消息到数据库
#             st.session_state.messages.append({"role": "assistant", "content": full_response})
#             intent = result.get("intent", "unknown")  # 🆕 提取意图
#             log_conversation_async(st.session_state.thread_id, "assistant", full_response,intent)    

# # 人工客服回复区域（仅在中断状态下显示）
# else:
#     st.warning("👤 当前为人工客服模式，请输入您的回复...")
#     if st.session_state.interrupt_data:
#         user_q = st.session_state.interrupt_data.get('user_question', '')
#         st.info(f"**用户问题：** {user_q}")

#     human_reply = st.chat_input("人工客服输入回复...")
#     if human_reply:
#         st.session_state.messages.append({"role": "assistant", "content": f"【人工客服】{human_reply}"})
#         log_conversation_async(st.session_state.thread_id, "assistant", f"【人工客服】{human_reply}", intent="human")
#         config = {"configurable": {"thread_id": st.session_state.thread_id}}
#         try:
#             result = app.invoke(Command(resume=human_reply), config)
#         except Exception as e:
#             st.error(f"恢复执行失败：{e}")

#         st.session_state.interrupted = False
#         st.session_state.interrupt_data = None
#         st.rerun()

# app.py 添加多用户登录模块
import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.types import Command
from langgraph.errors import GraphInterrupt
from workflow import build_workflow
import uuid
import requests
import threading
import time
import os

# 禁用追踪器，有兼容性问题
os.environ["LANGCHAIN_TRACING_V2"] = "false"

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="极客科技·数字员工", page_icon="🤖")

def log_conversation_async(thread_id, role, content, intent=None):
    """异步记录对话，不阻塞主线程"""
    def _log():
        try:
            payload = {"thread_id": thread_id, "role": role, "content": content}
            if intent:
                payload["intent"] = intent
            requests.post(f"{BACKEND_URL}/admin/conversation/log", json=payload, timeout=2)
        except Exception as e:
            print(f"⚠️ 记录对话失败: {e}")
    threading.Thread(target=_log, daemon=True).start()

# ==================== 用户登录与注册 ====================
if "user" not in st.session_state:
    st.session_state.user = None
    st.session_state.user_info = None

if st.session_state.user is None:
    st.title("🔐 登录 · 极客科技智能客服")
    tab1, tab2 = st.tabs(["登录", "注册"])
    
    with tab1:
        username = st.text_input("用户名", key="login_username")
        password = st.text_input("密码", type="password", key="login_password")
        if st.button("登录"):
            resp = requests.post(f"{BACKEND_URL}/auth/login", json={
                "username": username, "password": password
            })
            if resp.status_code == 200:
                data = resp.json()
                st.session_state.user = data["user"]["username"]
                st.session_state.user_info = data["user"]
                # 生成基于用户ID的唯一 thread_id
                st.session_state.thread_id = f"{data['user']['id']}_{uuid.uuid4().hex[:8]}_session"
                st.rerun()
            else:
                st.error(resp.json().get("error", "用户名或密码错误"))
    
    with tab2:
        new_username = st.text_input("用户名", key="reg_username")
        new_password = st.text_input("密码", type="password", key="reg_password")
        display_name = st.text_input("显示名称（可选）")
        role = st.selectbox("注册身份", ["customer", "merchant"], format_func=lambda x: "普通用户" if x=="customer" else "商家")
        if st.button("注册"):
            resp = requests.post(f"{BACKEND_URL}/auth/register", json={
                "username": new_username,
                "password": new_password,
                "display_name": display_name,
                "role_code": role
            })
            if resp.status_code == 200:
                st.success("注册成功，请登录")
            else:
                st.error(resp.json().get("error", "注册失败"))
    st.stop()

# ==================== 主应用（登录后） ====================
st.title(f"🤖 极客科技·智能客服")
roles = st.session_state.user_info.get("roles", [])
st.caption(f"👤 {st.session_state.user} | 角色: {', '.join(roles)}")

@st.cache_resource
def load_app():
    return build_workflow()

app = load_app()

# 初始化会话状态（每个用户独立）
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": f"您好 {st.session_state.user}！我是极客科技的智能客服。您可以向我咨询政策、查询订单或反馈问题。"}
    ]
    st.session_state.interrupted = False
    st.session_state.interrupt_data = None

# 显示历史消息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 正常用户输入（仅在非中断状态下显示）
if not st.session_state.interrupted:
    if prompt := st.chat_input("请输入您的问题..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        log_conversation_async(st.session_state.thread_id, "user", prompt)
        
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            with st.spinner("思考中..."):
                # 🆕 注入用户上下文到输入状态
                input_state = {
                    "messages": [HumanMessage(content=prompt)],
                    "user_id": st.session_state.user_info["id"],
                    "user_roles": st.session_state.user_info["roles"],
                    "merchant_id": st.session_state.user_info.get("merchant_id")
                }
                config = {"configurable": {"thread_id": st.session_state.thread_id}}

                try:
                    result = app.invoke(input_state, config)
                    
                    if isinstance(result, dict) and "__interrupt__" in result:
                        interrupt_info = result["__interrupt__"][0]
                        interrupt_data = interrupt_info.value if hasattr(interrupt_info, 'value') else interrupt_info
                        st.session_state.interrupted = True
                        st.session_state.interrupt_data = interrupt_data
                        st.rerun()
                    full_response = result.get("final_response", "抱歉，我暂时无法处理您的问题。")
                    
                except GraphInterrupt as e:
                    interrupt_obj = e.interrupts[0]
                    interrupt_data = interrupt_obj.value if hasattr(interrupt_obj, 'value') else interrupt_obj
                    st.session_state.interrupted = True
                    st.session_state.interrupt_data = interrupt_data
                    st.rerun()
                    
                except Exception as e:
                    full_response = f"系统遇到了一点问题，请稍后重试。"
                    print(f"❌ 未预期的错误：{type(e).__name__} - {e}")
            
            # 流式显示回答
            if full_response:
                displayed = ""
                base_delay = 0.03
                if len(full_response) > 200:
                    delay_per_char = 0.015
                elif len(full_response) > 100:
                    delay_per_char = 0.02
                else:
                    delay_per_char = 0.03
                for char in full_response:
                    displayed += char
                    message_placeholder.markdown(displayed + "▌")
                    time.sleep(delay_per_char)
                message_placeholder.markdown(full_response)
            else:
                message_placeholder.markdown("抱歉，我暂时无法处理您的问题。")
                full_response = "抱歉，我暂时无法处理您的问题。"
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            intent = result.get("intent", "unknown")
            log_conversation_async(st.session_state.thread_id, "assistant", full_response, intent)

# 人工客服回复区域（仅在中断状态下显示）
else:
    st.warning("👤 当前为人工客服模式，请输入您的回复...")
    if st.session_state.interrupt_data:
        user_q = st.session_state.interrupt_data.get('user_question', '')
        st.info(f"**用户问题：** {user_q}")

    human_reply = st.chat_input("人工客服输入回复...")
    if human_reply:
        st.session_state.messages.append({"role": "assistant", "content": f"【人工客服】{human_reply}"})
        log_conversation_async(st.session_state.thread_id, "assistant", f"【人工客服】{human_reply}", intent="human")
        config = {"configurable": {"thread_id": st.session_state.thread_id}}
        try:
            result = app.invoke(Command(resume=human_reply), config)
        except Exception as e:
            st.error(f"恢复执行失败：{e}")

        st.session_state.interrupted = False
        st.session_state.interrupt_data = None
        st.rerun()