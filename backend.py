# backend.py
import os
import sys
import shutil
import threading
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from werkzeug.utils import secure_filename
import sqlite3
from fastapi.responses import JSONResponse
import json
import pickle
import msgpack
from langchain_core.messages import BaseMessage
import re  
import pymysql
from pydantic import BaseModel
import importlib.util
from pathlib import Path

from document_loader import load_documents_from_folder, split_documents_by_type
from langchain_ollama import OllamaEmbeddings
from document_loader import load_documents_from_folder, split_documents_by_type
from langchain_community.vectorstores import Chroma
import os

CHECKPOINT_DB = "./checkpoints.db"

# ==================== 初始化 FastAPI ====================
app = FastAPI(title="极客科技·订单工单系统")

# 添加 CORS 支持，便于前后端分离部署
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 配置 ====================
DOCS_DIR = "./docs"
os.makedirs(DOCS_DIR, exist_ok=True)

# 索引状态与线程锁
index_lock = threading.Lock()
index_status = {
    "last_built": None,
    "document_count": 0,
    "is_building": False
}

#数据库配置
CHECKPOINT_DB = "./checkpoints.db"

#mysql配置

def get_db_connection():
    return pymysql.connect(
        host="localhost",
        port=3306,
        user="root",
        password="123456",
        database="digital_employee",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )

# ==================== 模拟数据库 ====================
orders_db: Dict[str, dict] = {
    "ORD-20260411-1234": {
        "status": "已发货",
        "logistics": "中通快递 运单号：ZT123456789，预计4月13日送达",
        "items": "极客智能音箱 x1",
        "created_at": "2026-04-11"
    },
    "ORD-20260410-5678": {
        "status": "待发货",
        "logistics": "仓库处理中，预计今日发货",
        "items": "极客无线耳机 x2",
        "created_at": "2026-04-10"
    },
    "ORD-20260409-9999": {
        "status": "已签收",
        "logistics": "顺丰快递 运单号：SF123456789，已于4月11日签收",
        "items": "极客机械键盘 x1",
        "created_at": "2026-04-09"
    }
}

tickets_db: List[dict] = []

# ==================== 请求/响应模型 ====================
class TicketRequest(BaseModel):
    user_id: str
    issue_type: str
    description: str

class TicketResponse(BaseModel):
    status: str
    ticket_id: str
    message: str

class OrderResponse(BaseModel):
    status: str
    order_id: str = None
    message: str = None
    order_status: str = None
    logistics: str = None
    items: str = None
    created_at: str = None

class ConversationLog(BaseModel):
    thread_id: str
    role: str
    content: str

# ==================== 核心业务端点 ====================
@app.get("/")
async def root():
    return {"message": "极客科技订单工单系统已启动", "version": "1.0.0"}

@app.get("/order/{order_id}", response_model=OrderResponse)
async def query_order(order_id: str):
    """根据订单号查询订单详情"""
    order = orders_db.get(order_id.upper())
    if not order:
        return OrderResponse(
            status="not_found",
            message=f"未找到订单 {order_id}，请确认订单号是否正确。"
        )
    return OrderResponse(
        status="success",
        order_id=order_id.upper(),
        order_status=order["status"],
        logistics=order["logistics"],
        items=order["items"],
        created_at=order["created_at"]
    )

@app.post("/ticket", response_model=TicketResponse)
async def create_ticket(req: TicketRequest):
    """创建售后服务工单"""
    ticket_id = f"TKT-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
    ticket = {
        "ticket_id": ticket_id,
        "user_id": req.user_id,
        "issue_type": req.issue_type,
        "description": req.description,
        "created_at": datetime.now().isoformat(),
        "status": "待处理"
    }
    tickets_db.append(ticket)
    print(f"📋 [工单创建] ID: {ticket_id}, 类型: {req.issue_type}, 用户: {req.user_id}")
    
    return TicketResponse(
        status="success",
        ticket_id=ticket_id,
        message=f"您的{req.issue_type}工单已创建，客服将尽快处理。"
    )

@app.get("/tickets")
async def list_tickets():
    """列出所有工单（调试用）"""
    return {"total": len(tickets_db), "tickets": tickets_db}

@app.get("/orders")
async def list_orders():
    """列出所有订单（调试用）"""
    return {"total": len(orders_db), "orders": orders_db}

# ==================== 知识库管理端点 ====================
def count_documents() -> int:
    """递归统计 DOCS_DIR 下所有文件数量"""
    if not os.path.exists(DOCS_DIR):
        return 0
    count = 0
    for root, dirs, files in os.walk(DOCS_DIR):
        count += len(files)
    return count

def rebuild_index_inline():
    """内联版本：直接执行索引重建，不依赖外部 build_index.py"""
    print("📂 正在扫描 docs 文件夹...")
    docs = load_documents_from_folder("./docs")
    if not docs:
        print("⚠️ 没有文档，跳过索引构建")
        return

    print(f"📚 共加载 {len(docs)} 个文档片段")
    chunks = split_documents_by_type(docs)
    print(f"🧩 切分为 {len(chunks)} 个文本块")

    embeddings = OllamaEmbeddings(model="lrs33/bce-embedding-base_v1:latest", base_url="http://localhost:11434")

    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory="./chroma_db"
    )
    print("✅ 向量索引重建完成！")

def run_index_build():
    """后台执行索引重建（使用内联函数）"""
    with index_lock:
        if index_status["is_building"]:
            return
        index_status["is_building"] = True

    try:
        rebuild_index_inline()
        with index_lock:
            index_status["last_built"] = datetime.now().isoformat()
    except Exception as e:
        print(f"❌ 索引重建失败：{e}")
        import traceback
        traceback.print_exc()
    finally:
        with index_lock:
            index_status["is_building"] = False
            index_status["document_count"] = count_documents()

@app.post("/knowledge/upload")
async def upload_document(file: UploadFile = File(...)):
    """上传文档到知识库"""
    if not file.filename:
        return {"status": "error", "message": "文件名不能为空"}
    
    ext = os.path.splitext(file.filename)[-1].lower()
    if ext not in [".txt", ".md", ".pdf", ".docx", ".doc"]:
        return {"status": "error", "message": f"不支持的文件类型：{ext}"}
    
    # 防止路径穿越攻击
    safe_filename = secure_filename(file.filename)
    file_path = os.path.join(DOCS_DIR, safe_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 更新文档计数
    with index_lock:
        index_status["document_count"] = count_documents()
    
    return {"status": "success", "message": f"文件 {safe_filename} 上传成功"}

@app.post("/knowledge/rebuild")
async def rebuild_index(background_tasks: BackgroundTasks):
    """触发索引重建（后台执行）"""
    with index_lock:
        if index_status["is_building"]:
            return {"status": "error", "message": "索引重建正在进行中，请稍后"}
    
    background_tasks.add_task(run_index_build)
    return {"status": "success", "message": "索引重建任务已开始"}

@app.get("/knowledge/status")
async def get_index_status():
    """获取索引状态"""
    with index_lock:
        # 实时统计文档数量
        index_status["document_count"] = count_documents()
        # 返回副本，避免外部意外修改
        return index_status.copy()

# ==================== 对话管理端点 ====================
def extract_message_preview(messages, max_length=50):
    """从各种格式的 messages 中提取第一条用户消息的预览"""
    if not messages:
        return ""
    
    for msg in messages:
        content = None
        
        # 1. 如果是 LangChain BaseMessage 对象
        if isinstance(msg, BaseMessage):
            if msg.type == "human":
                content = msg.content
        # 2. 如果是字典（可能包含 type 和 content 键）
        elif isinstance(msg, dict):
            if msg.get("type") == "human" or msg.get("role") == "user":
                content = msg.get("content", "")
        # 3. 如果是序列化后的消息元组（例如 ('human', '你好')）
        elif isinstance(msg, (list, tuple)) and len(msg) >= 2:
            role = msg[0]
            if role == "human" or role == "user":
                content = msg[1]
        # 4. 如果消息对象有 type 属性（通过 __slots__ 或其他方式）
        elif hasattr(msg, "type") and hasattr(msg, "content"):
            if msg.type == "human":
                content = msg.content
        
        if content:
            # 如果 content 本身是列表（多模态消息），取第一个文本部分
            if isinstance(content, list):
                text_parts = [c.get("text", "") if isinstance(c, dict) else str(c) for c in content]
                content = " ".join(text_parts)
            return str(content)[:max_length]
    
    return "(无用户消息)"


@app.post("/admin/conversation/log")
async def log_conversation(log: ConversationLog):
    """记录对话消息到自建表"""
    if log.role not in ("user", "assistant", "system"):
        return JSONResponse(status_code=400, content={"error": "无效的角色"})
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO conversation_history (thread_id, role, content) VALUES (%s, %s, %s)",
            (log.thread_id, log.role, log.content)
        )
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        print(f"❌ 写入对话日志失败: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

#/admin/conversations
@app.get("/admin/conversations")
async def get_conversations(limit: int = 50):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT 
                thread_id,
                MAX(created_at) AS last_updated,
                (SELECT content FROM conversation_history c2 
                 WHERE c2.thread_id = c1.thread_id AND role = 'user' 
                 ORDER BY created_at ASC LIMIT 1) AS preview
            FROM conversation_history c1
            GROUP BY thread_id
            ORDER BY last_updated DESC
            LIMIT %s
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        return {"conversations": rows}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

#/admin/conversation/{thread_id}
@app.get("/admin/conversation/{thread_id}")
async def get_conversation_detail(thread_id: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT role, content, created_at
            FROM conversation_history
            WHERE thread_id = %s
            ORDER BY created_at ASC
        """, (thread_id,))
        rows = cursor.fetchall()
        conn.close()
        return {"thread_id": thread_id, "conversation": rows}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})



# ==================== 启动入口 ====================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)