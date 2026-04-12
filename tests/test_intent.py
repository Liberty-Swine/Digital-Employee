import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from langchain_ollama import ChatOllama
from supervisor import create_supervisor_node

@pytest.fixture
def llm():
    return ChatOllama(model="qwen2.5:3b", base_url="http://localhost:11434", temperature=0)

def test_intent_knowledge(llm):
    node = create_supervisor_node(llm)
    state = {"messages": [type('msg', (), {'content': '退货政策是什么？', 'type': 'human'})]}
    result = node(state)
    assert result["intent"] == "knowledge"

def test_intent_action(llm):
    node = create_supervisor_node(llm)
    state = {"messages": [type('msg', (), {'content': '查询订单 ORD-123', 'type': 'human'})]}
    result = node(state)
    assert result["intent"] == "action"

def test_intent_human(llm):
    node = create_supervisor_node(llm)
    state = {"messages": [type('msg', (), {'content': '转人工', 'type': 'human'})]}
    result = node(state)
    assert result["intent"] == "human"