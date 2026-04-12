# admin.py
import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

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
    ["📊 数据看板", "📚 知识库管理", "📋 工单列表", "💬 对话记录", "📦 订单列表"]  # 🆕 新增看板
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
# ==================== 数据看板 ====================
elif menu == "📊 数据看板":
    st.header("📊 运营数据看板")
    
    # 获取日期范围选择
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("开始日期", value=datetime.now().date() - timedelta(days=7))
    with col2:
        end_date = st.date_input("结束日期", value=datetime.now().date())
    
    if start_date > end_date:
        st.error("开始日期不能晚于结束日期")
        st.stop()
    
    # 从后端获取统计数据（需要新增后端接口，见第三步）
    try:
        resp = requests.get(
            f"{BACKEND_URL}/admin/stats/overview",
            params={"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
            timeout=10
        )
        if resp.status_code != 200:
            st.error("获取统计数据失败")
            st.stop()
        stats = resp.json()
    except Exception as e:
        st.error(f"连接后端失败：{e}")
        st.stop()
    
    # 顶部指标卡片
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📅 总对话量", stats.get("total_conversations", 0))
    col2.metric("💬 总消息数", stats.get("total_messages", 0))
    col3.metric("👥 独立用户数", stats.get("unique_users", 0))
    col4.metric("📏 平均回复长度", f"{stats.get('avg_response_length', 0)} 字")
    
    st.divider()
    
    # 趋势图与分布图
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📈 近7天对话趋势")
        trend = stats.get("daily_trend", [])
        if trend:
            df_trend = pd.DataFrame(trend)
            df_trend["date"] = pd.to_datetime(df_trend["date"])
            df_trend = df_trend.set_index("date")
            st.line_chart(df_trend["count"])
        else:
            st.info("暂无数据")
    
    with col2:
        st.subheader("🥧 意图分布")
        intent_dist = stats.get("intent_distribution", {})
        if intent_dist:
            df_intent = pd.DataFrame({
                "意图": list(intent_dist.keys()),
                "数量": list(intent_dist.values())
            })
            st.bar_chart(df_intent, x="意图", y="数量")
        else:
            st.info("暂无数据")
    
    st.divider()
    
    # 热门问题排行
    st.subheader("🔥 热门用户提问 Top 5")
    top_questions = stats.get("top_questions", [])
    if top_questions:
        for i, q in enumerate(top_questions, 1):
            st.write(f"{i}. {q['content']} (出现 {q['count']} 次)")
    else:
        st.info("暂无数据")