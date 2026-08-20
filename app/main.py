"""FastAPI 应用：路由实现。"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from app import db, dina, schemas
from app.config import GUESS, SLIP

app = FastAPI(title="认知诊断系统 MVP", version="0.1.0")

# 静态文件目录（如果存在）
# app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/api/students", response_model=list[schemas.Student], tags=["students"])
def list_students() -> list[schemas.Student]:
    """获取学生列表。"""
    students = db.get_all_students()
    return [schemas.Student(**s) for s in students]


@app.get("/api/diagnosis/{student_id}", response_model=schemas.DiagnosisResult, tags=["diagnosis"])
def get_diagnosis(student_id: int) -> schemas.DiagnosisResult:
    """获取某学生的诊断结果（各知识点掌握概率）。"""
    student = db.get_student(student_id)
    if student is None:
        raise HTTPException(status_code=404, detail=f"学生 {student_id} 不存在")

    # 获取 Q 矩阵和该学生作答
    Q = db.get_q_matrix()
    X = db.get_student_responses(student_id)

    # 获取知识点列表
    kps = db.get_all_knowledge_points()

    # 调用 DINA 计算掌握概率
    probs = dina.compute_mastery_probability(X, Q, SLIP, GUESS)

    # 构造响应
    mastery = []
    for kp, prob in zip(kps, probs):
        mastery.append(schemas.MasteryEntry(
            kp_id=kp["id"],
            kp_name=kp["name"],
            probability=round(float(prob), 4)
        ))

    return schemas.DiagnosisResult(
        student_id=student_id,
        mastery=mastery
    )


@app.post("/api/suggest", response_model=schemas.SuggestResponse, tags=["suggest"])
def suggest(request: schemas.SuggestRequest) -> schemas.SuggestResponse:
    """根据诊断结果生成学习建议（模板降级，LLM 稍后接入）。"""
    # 简单模板建议（LLM 稍后实现）
    weak_points = [m for m in request.mastery if m.probability < 0.4]
    if weak_points:
        names = "、".join(m.kp_name for m in weak_points)
        suggestion = f"你在「{names}」上掌握度较低，建议加强相关知识点的学习。"
    else:
        suggestion = "恭喜你已掌握所有知识点，可以挑战更高难度的题目！"

    return schemas.SuggestResponse(
        student_id=request.student_id,
        suggestion=suggestion
    )


@app.get("/api/knowledge-graph", response_model=schemas.KnowledgeGraph, tags=["knowledge-graph"])
def knowledge_graph() -> schemas.KnowledgeGraph:
    """获取知识点节点与前置/后续关系。"""
    kps = db.get_all_knowledge_points()
    edges = db.get_kg_edges()

    nodes = [schemas.KnowledgePoint(**kp) for kp in kps]
    edge_list = [schemas.KnowledgeGraphEdge(**e) for e in edges]

    return schemas.KnowledgeGraph(nodes=nodes, edges=edge_list)
