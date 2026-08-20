"""API 接口测试用例。"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestStudentsAPI:
    """测试学生相关接口。"""

    def test_get_students(self):
        """GET /api/students 返回 200 + 学生列表。"""
        response = client.get("/api/students")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 10  # 10 个学生


class TestDiagnosisAPI:
    """测试诊断接口。"""

    def test_get_diagnosis(self):
        """GET /api/diagnosis/1 返回 5 个知识点概率。"""
        response = client.get("/api/diagnosis/1")
        assert response.status_code == 200
        data = response.json()
        assert "student_id" in data
        assert "mastery" in data
        assert len(data["mastery"]) == 5  # 5 个知识点

    def test_probability_range(self):
        """所有概率应在 [0, 1] 范围内。"""
        response = client.get("/api/diagnosis/1")
        data = response.json()
        for entry in data["mastery"]:
            assert 0 <= entry["probability"] <= 1

    def test_student_not_found(self):
        """不存在的学生 ID 返回 404。"""
        response = client.get("/api/diagnosis/999")
        assert response.status_code == 404


class TestKnowledgeGraphAPI:
    """测试知识图谱接口。"""

    def test_get_knowledge_graph(self):
        """GET /api/knowledge-graph 返回节点+边。"""
        response = client.get("/api/knowledge-graph")
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) == 5  # 5 个知识点
        assert len(data["edges"]) == 4   # 线性链 4 条边


class TestSuggestAPI:
    """测试学习建议接口。"""

    def test_suggest_with_mastery(self):
        """POST /api/suggest 返回建议文本。"""
        payload = {
            "student_id": 1,
            "mastery": [
                {"kp_id": 1, "kp_name": "分数加法", "probability": 0.9},
                {"kp_id": 2, "kp_name": "分数减法", "probability": 0.3},
                {"kp_id": 3, "kp_name": "分数乘法", "probability": 0.2},
            ]
        }
        response = client.post("/api/suggest", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "suggestion" in data
        assert isinstance(data["suggestion"], str)
