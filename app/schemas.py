"""数据类型定义（Pydantic v2 models）。

仅定义骨架与字段约束，不含业务逻辑。
字段命名与 SQLite Schema 及 API 契约保持一致。
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class Student(BaseModel):
    """学生。"""
    id: int
    name: str


class KnowledgePoint(BaseModel):
    """知识点。"""
    id: int
    name: str


class MasteryEntry(BaseModel):
    """单个知识点的掌握概率（0~1）。"""
    kp_id: int
    kp_name: str
    probability: float = Field(ge=0.0, le=1.0)


class DiagnosisResult(BaseModel):
    """某学生的诊断结果。"""
    student_id: int
    mastery: list[MasteryEntry]


class SuggestRequest(BaseModel):
    """生成学习建议的请求体：携带诊断结果。"""
    student_id: int
    mastery: list[MasteryEntry]


class SuggestResponse(BaseModel):
    """学习建议。"""
    student_id: int
    suggestion: str


class KnowledgeGraphEdge(BaseModel):
    """知识图谱边（前置关系）。"""
    from_kp_id: int
    to_kp_id: int
    edge_type: str = "prerequisite"


class KnowledgeGraph(BaseModel):
    """知识图谱：知识点节点 + 前置边。"""
    nodes: list[KnowledgePoint]
    edges: list[KnowledgeGraphEdge]
