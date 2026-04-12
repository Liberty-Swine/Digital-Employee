# document_loader.py
import os
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredFileLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import List

# ==================== 文档加载 ====================
def load_documents_from_folder(folder_path: str) -> List[Document]:
    """
    从文件夹中加载所有支持格式的文档。
    支持：.txt, .md, .pdf, .docx, .doc
    """
    all_docs = []
    
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            ext = os.path.splitext(file)[-1].lower()
            
            try:
                if ext in [".txt", ".md"]:
                    loader = TextLoader(file_path, encoding="utf-8")
                elif ext == ".pdf":
                    loader = PyPDFLoader(file_path)
                elif ext == ".docx":
                    loader = Docx2txtLoader(file_path)
                elif ext == ".doc":
                    loader = UnstructuredFileLoader(file_path)
                else:
                    print(f"⚠️ 跳过不支持的文件类型：{file}")
                    continue
                
                docs = loader.load()
                for doc in docs:
                    doc.metadata["source"] = file_path
                    doc.metadata["file_name"] = file
                all_docs.extend(docs)
                print(f"✅ 已加载：{file} ({len(docs)} 页/段)")
                
            except Exception as e:
                print(f"❌ 加载失败 {file}：{e}")
    
    return all_docs

# ==================== 自适应分块策略 ====================
def get_splitter_for_doc(doc: Document) -> RecursiveCharacterTextSplitter:
    """
    根据文档的扩展名返回最合适的分块器参数。
    """
    source = doc.metadata.get("source", "")
    file_name = doc.metadata.get("file_name", "")
    ext = os.path.splitext(source or file_name)[-1].lower()

    if ext == ".pdf":
        return RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            separators=["\n\n", "\n", "。", "！", "？", "，", " ", ""]
        )
    elif ext in [".txt", ".md"]:
        return RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", "。", "！", "？", "，", " ", ""]
        )
    elif ext in [".docx", ".doc"]:
        return RecursiveCharacterTextSplitter(
            chunk_size=600,
            chunk_overlap=80,
            separators=["\n\n", "\n", "。", "！", "？", "，", " ", ""]
        )
    else:
        return RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", "。", "！", "？", "，", " ", ""]
        )

def split_documents_by_type(docs: List[Document]) -> List[Document]:
    """
    按文档类型分别使用不同的分块器，返回切分后的所有块。
    """
    all_chunks = []
    for doc in docs:
        splitter = get_splitter_for_doc(doc)
        chunks = splitter.split_documents([doc])
        all_chunks.extend(chunks)
        print(f"   └─ {doc.metadata.get('file_name', '未知')} → {len(chunks)} 个块 (chunk_size={splitter._chunk_size})")
    return all_chunks