# admin.py
import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="极客科技·管理后台", page_icon="🛠️", layout="wide")

BACKEND_URL = "http://localhost:8000"

# 简单的管理员验证（可自行扩展）
if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

if not st.session_state.admin_authenticated:
    st.title("🔐 管理员登录")
    password = st.text_input("请输入管理员密码", type="password")
    if st.button("登录") and password == "admin123":  # 示例密码
        st.session_state.admin_authenticated = True
        st.rerun()
    elif password:
        st.error("密码错误")
    st.stop()

# ==================== 主界面 ====================
st.title("🛠️ 极客科技·管理后台")
st.caption(f"登录时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 侧边栏导航
menu = st.sidebar.radio(
    "导航菜单",
    ["📚 知识库管理", "📋 工单列表", "💬 对话记录", "📦 订单列表"]
)

# ==================== 知识库管理 ====================
if menu == "📚 知识库管理":
    st.header("📚 知识库管理")
    
    col1, col2, col3 = st.columns(3)
    
    # 获取状态
    try:
        resp = requests.get(f"{BACKEND_URL}/knowledge/status", timeout=3)
        if resp.status_code == 200:
            status = resp.json()
            col1.metric("📄 文档数量", status.get("document_count", 0))
            col2.metric("🔄 重建中", "是" if status.get("is_building") else "否")
            last_built = status.get("last_built")
            col3.metric("⏱️ 最后索引", last_built[:16] if last_built else "从未")
        else:
            st.warning("无法获取知识库状态")
    except Exception as e:
        st.error(f"连接后端失败：{e}")
    
    st.divider()
    
    # 文件上传
    st.subheader("📤 上传文档")
    uploaded_file = st.file_uploader(
        "选择文件（支持 txt, md, pdf, docx）",
        type=["txt", "md", "pdf", "docx", "doc"]
    )
    if uploaded_file:
        if st.button("确认上传"):
            with st.spinner("上传中..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                resp = requests.post(f"{BACKEND_URL}/knowledge/upload", files=files)
                if resp.status_code == 200 and resp.json().get("status") == "success":
                    st.success(f"✅ {uploaded_file.name} 上传成功")
                    st.rerun()
                else:
                    st.error("上传失败")
    
    st.divider()
    
    # 重建索引
    st.subheader("🔄 重建向量索引")
    if st.button("开始重建", type="primary"):
        with st.spinner("提交重建任务..."):
            resp = requests.post(f"{BACKEND_URL}/knowledge/rebuild")
            if resp.status_code == 200:
                st.success("重建任务已开始，请稍后刷新状态")
            else:
                st.error("启动重建失败")

# ==================== 工单列表 ====================
elif menu == "📋 工单列表":
    st.header("📋 工单记录")
    try:
        resp = requests.get(f"{BACKEND_URL}/tickets")
        if resp.status_code == 200:
            tickets = resp.json().get("tickets", [])
            if tickets:
                df = pd.DataFrame(tickets)
                # 格式化时间列
                if "created_at" in df.columns:
                    df["created_at"] = pd.to_datetime(df["created_at"]).dt.strftime("%m-%d %H:%M")
                st.dataframe(df, use_container_width=True)
            else:
                st.info("暂无工单记录")
    except Exception as e:
        st.error(f"获取工单失败：{e}")

# ==================== 对话记录 ====================
elif menu == "💬 对话记录":
        st.header("💬 最近对话")
        limit = st.slider("显示条数", 10, 100, 30)
        resp = requests.get(f"{BACKEND_URL}/admin/conversations", params={"limit": limit})
        if resp.status_code == 200:
            convs = resp.json().get("conversations", [])
            if convs:
                df = pd.DataFrame(convs)
                st.dataframe(df, use_container_width=True)
                
                # 详情查看
                st.subheader("🔍 查看完整对话")
                selected_thread = st.selectbox("选择对话ID", [c["thread_id"] for c in convs])
                if st.button("加载对话详情"):
                    detail_resp = requests.get(f"{BACKEND_URL}/admin/conversation/{selected_thread}")
                    if detail_resp.status_code == 200:
                        detail = detail_resp.json()
                        for turn in detail.get("conversation", []):
                            role_icon = "🧑" if turn["role"] in ("human", "user") else "🤖"
                            with st.chat_message(turn["role"]):
                                st.write(f"{role_icon} {turn['content']}")
                    else:
                        st.error("加载失败")
            else:
                st.info("暂无对话记录")

# ==================== 订单列表 ====================
elif menu == "📦 订单列表":
    st.header("📦 订单数据库")
    try:
        resp = requests.get(f"{BACKEND_URL}/orders")
        if resp.status_code == 200:
            orders = resp.json().get("orders", {})
            if orders:
                # 转换为表格友好格式
                rows = []
                for oid, detail in orders.items():
                    rows.append({
                        "订单号": oid,
                        "状态": detail.get("status"),
                        "物流": detail.get("logistics", "")[:20] + "...",
                        "商品": detail.get("items"),
                        "创建时间": detail.get("created_at")
                    })
                df = pd.DataFrame(rows)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("暂无订单")
    except Exception as e:
        st.error(f"获取订单失败：{e}")