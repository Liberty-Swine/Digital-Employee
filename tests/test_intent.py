import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from langchain_ollama import ChatOllama
from supervisor import create_supervisor_node

# 检查 Ollama 是否可用的辅助函数
def is_ollama_running():
    import requests
    try:
        return requests.get("http://localhost:11434", timeout=2).status_code == 200
    except:
        return False

@pytest.fixture
def llm():
    if not is_ollama_running():
        pytest.skip("Ollama 服务未运行，跳过意图识别测试")
    return ChatOllama(model="qwen2.5:3b", base_url="http://localhost:11434", temperature=0)

class MockMessage:
    def __init__(self, content, type):
        self.content = content
        self.type = type

def test_intent_knowledge(llm):
    node = create_supervisor_node(llm)
    state = {"messages": [MockMessage("退货政策是什么？", "human")]}
    result = node(state)
    assert result["intent"] == "knowledge"

def test_intent_action(llm):
    node = create_supervisor_node(llm)
    state = {"messages": [MockMessage("查询订单 ORD-123", "human")]}
    result = node(state)
    assert result["intent"] == "action"

def test_intent_human(llm):
    node = create_supervisor_node(llm)
    state = {"messages": [MockMessage("转人工", "human")]}
    result = node(state)
    assert result["intent"] == "human"