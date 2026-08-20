"""FastAPI 应用骨架：路由定义 + 契约。

仅定义接口签名与响应模型，不含业务逻辑（stub 抛 NotImplementedError）。
"""
from __future__ import annotations

from fastapi import FastAPI

from app import schemas

app = FastAPI(title="认知诊断系统 MVP", version="0.1.0")


@app.get("/api/students", response_model=list[schemas.Student], tags=["students"])
def list_students() -> list[schemas.Student]:
    """获取学生列表。"""
    raise NotImplementedError("待实现：从 SQLite 读取全部学生")


@app.get("/api/diagnosis/{student_id}", response_model=schemas.DiagnosisResult, tags=["diagnosis"])
def get_diagnosis(student_id: int) -> schemas.DiagnosisResult:
    """获取某学生的诊断结果（各知识点掌握概率）。"""
    raise NotImplementedError("待实现：DINA 推理 + 返回掌握概率")


@app.post("/api/suggest", response_model=schemas.SuggestResponse, tags=["suggest"])
def suggest(request: schemas.SuggestRequest) -> schemas.SuggestResponse:
    """根据诊断结果生成学习建议（加分项，DeepSeek / 模板降级）。"""
    raise NotImplementedError("待实现：DeepSeek 调用 + 模板降级")


@app.get("/api/knowledge-graph", response_model=schemas.KnowledgeGraph, tags=["knowledge-graph"])
def knowledge_graph() -> schemas.KnowledgeGraph:
    """获取知识点节点与前置/后续关系。"""
    raise NotImplementedError("待实现：从 kg_edges 表读取")
