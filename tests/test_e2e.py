"""端到端集成测试用例。

测试范围：
1. 完整业务流程：获取学生列表 → 诊断 → 验证结果
2. 知识图谱接口
3. 学习建议接口
4. 异常情况处理
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """创建测试客户端。"""
    return TestClient(app)


class TestEndToEndFlow:
    """端到端业务流程测试。"""

    def test_full_diagnosis_flow(self, client):
        """完整流程：获取学生列表 → 诊断 → 验证结果。"""
        # 1. 获取学生列表
        response = client.get("/api/students")
        assert response.status_code == 200
        students = response.json()
        assert len(students) == 10, f"应有 10 个学生，实际 {len(students)}"

        # 2. 获取第一个学生的诊断结果
        first_student_id = students[0]["id"]
        response = client.get(f"/api/diagnosis/{first_student_id}")
        assert response.status_code == 200
        diagnosis = response.json()

        # 3. 验证诊断结果结构
        assert diagnosis["student_id"] == first_student_id
        assert len(diagnosis["mastery"]) == 5, "应有 5 个知识点"

        # 4. 验证每个知识点结构完整
        for entry in diagnosis["mastery"]:
            assert "kp_id" in entry
            assert "kp_name" in entry
            assert "probability" in entry
            assert isinstance(entry["probability"], float)
            assert 0.0 <= entry["probability"] <= 1.0

    def test_multiple_students_diagnosis(self, client):
        """验证多个学生的诊断结果。"""
        response = client.get("/api/students")
        students = response.json()

        # 验证每个学生都能获取诊断
        for student in students:
            response = client.get(f"/api/diagnosis/{student['id']}")
            assert response.status_code == 200
            diagnosis = response.json()
            assert len(diagnosis["mastery"]) == 5

    def test_diagnosis_mastery_probabilities_varied(self, client):
        """验证掌握概率多样化（不应所有学生完全相同）。"""
        response = client.get("/api/students")
        students = response.json()

        all_mastery = []
        for student in students:
            response = client.get(f"/api/diagnosis/{student['id']}")
            diagnosis = response.json()
            probs = [e["probability"] for e in diagnosis["mastery"]]
            all_mastery.append(probs)

        # 至少有两个学生的掌握情况不同
        unique_patterns = set()
        for probs in all_mastery:
            # 四舍五入到 2 位小数比较
            rounded = tuple(round(p, 2) for p in probs)
            unique_patterns.add(rounded)

        assert len(unique_patterns) > 1, "学生掌握情况应多样化"


class TestKnowledgeGraphEndToEnd:
    """知识图谱端到端测试。"""

    def test_knowledge_graph_structure(self, client):
        """验证知识图谱接口返回正确结构。"""
        response = client.get("/api/knowledge-graph")
        assert response.status_code == 200
        data = response.json()

        # 验证包含节点和边
        assert "nodes" in data
        assert "edges" in data

        # 验证节点数量
        assert len(data["nodes"]) == 5, f"应有 5 个节点，实际 {len(data['nodes'])}"

        # 验证边数量
        assert len(data["edges"]) == 4, f"应有 4 条边，实际 {len(data['edges'])}"

    def test_knowledge_graph_node_fields(self, client):
        """验证节点字段完整。"""
        response = client.get("/api/knowledge-graph")
        data = response.json()

        for node in data["nodes"]:
            assert "id" in node
            assert "name" in node
            assert isinstance(node["id"], int)
            assert isinstance(node["name"], str)

    def test_knowledge_graph_edge_fields(self, client):
        """验证边字段完整。"""
        response = client.get("/api/knowledge-graph")
        data = response.json()

        for edge in data["edges"]:
            assert "from_kp_id" in edge
            assert "to_kp_id" in edge
            assert "edge_type" in edge
            assert edge["edge_type"] == "prerequisite"

    def test_knowledge_graph_sequential(self, client):
        """验证知识图谱为线性链。"""
        response = client.get("/api/knowledge-graph")
        data = response.json()

        # 按 from_kp_id 排序后检查
        edges = sorted(data["edges"], key=lambda e: e["from_kp_id"])
        for i in range(len(edges)):
            expected_from = i + 1
            expected_to = i + 2
            assert edges[i]["from_kp_id"] == expected_from
            assert edges[i]["to_kp_id"] == expected_to


class TestSuggestEndToEnd:
    """学习建议端到端测试。"""

    def _mastery_of(self, client, student_id):
        """获取某学生的诊断 mastery 列表，作为 suggest 请求体。"""
        return client.get(f"/api/diagnosis/{student_id}").json()["mastery"]

    def test_suggest_with_valid_student(self, client):
        """验证学习建议接口正常返回。"""
        response = client.post("/api/suggest", json={
            "student_id": 1,
            "mastery": self._mastery_of(client, 1),
        })
        assert response.status_code == 200
        data = response.json()

        # 验证返回包含建议字段
        assert "suggestion" in data
        assert isinstance(data["suggestion"], str)
        assert len(data["suggestion"]) > 0, "建议文本不应为空"

    def test_suggest_with_all_students(self, client):
        """验证所有学生都能生成建议。"""
        for student_id in range(1, 11):
            response = client.post("/api/suggest", json={
                "student_id": student_id,
                "mastery": self._mastery_of(client, student_id),
            })
            assert response.status_code == 200
            data = response.json()
            assert len(data["suggestion"]) > 0

    def test_suggest_invalid_body(self, client):
        """缺少 mastery 字段的请求体应返回 422。"""
        response = client.post("/api/suggest", json={"student_id": 1})
        assert response.status_code == 422


class TestErrorHandlingEndToEnd:
    """异常处理端到端测试。"""

    def test_student_not_found(self, client):
        """不存在的学生 ID 应返回 404。"""
        response = client.get("/api/diagnosis/9999")
        assert response.status_code == 404
        assert "detail" in response.json()

    def test_invalid_http_method(self, client):
        """不支持的 HTTP 方法应返回 405。"""
        response = client.post("/api/diagnosis/1")
        assert response.status_code == 405

    def test_api_routes_exist(self, client):
        """验证所有主要 API 路由存在。"""
        get_routes = [
            "/api/students",
            "/api/diagnosis/1",
            "/api/knowledge-graph",
        ]
        for route in get_routes:
            response = client.get(route)
            assert response.status_code != 404, f"路由 {route} 不存在"

        # POST /api/suggest 路由存在（GET 请求会返回 405 而非 404）
        assert client.get("/api/suggest").status_code != 404, "路由 /api/suggest 不存在"
