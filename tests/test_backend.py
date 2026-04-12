import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from backend import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "极客科技订单工单系统已启动"

def test_query_order_existing():
    response = client.get("/order/ORD-20260411-1234")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["order_id"] == "ORD-20260411-1234"

def test_query_order_not_found():
    response = client.get("/order/NOTEXIST")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "not_found"

def test_create_ticket():
    response = client.post("/ticket", json={
        "user_id": "test_user",
        "issue_type": "投诉",
        "description": "测试工单"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "ticket_id" in data