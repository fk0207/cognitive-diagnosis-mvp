"""SQLite 数据访问层。"""
import sqlite3
from pathlib import Path
from typing import Optional

import numpy as np

from app.config import DB_PATH


def _get_conn() -> sqlite3.Connection:
    """获取数据库连接。"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_all_students() -> list[dict]:
    """获取所有学生列表。"""
    conn = _get_conn()
    try:
        rows = conn.execute("SELECT id, name FROM students ORDER BY id").fetchall()
        return [{"id": r["id"], "name": r["name"]} for r in rows]
    finally:
        conn.close()


def get_student(student_id: int) -> Optional[dict]:
    """获取单个学生，不存在返回 None。"""
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT id, name FROM students WHERE id = ?", (student_id,)
        ).fetchone()
        return {"id": row["id"], "name": row["name"]} if row else None
    finally:
        conn.close()


def get_all_knowledge_points() -> list[dict]:
    """获取所有知识点。"""
    conn = _get_conn()
    try:
        rows = conn.execute("SELECT id, name FROM knowledge_points ORDER BY id").fetchall()
        return [{"id": r["id"], "name": r["name"]} for r in rows]
    finally:
        conn.close()


def get_all_questions() -> list[dict]:
    """获取所有题目。"""
    conn = _get_conn()
    try:
        rows = conn.execute("SELECT id, name FROM questions ORDER BY id").fetchall()
        return [{"id": r["id"], "name": r["name"]} for r in rows]
    finally:
        conn.close()


def get_q_matrix() -> np.ndarray:
    """获取 Q 矩阵，返回 (n_questions, n_kps) numpy array。"""
    conn = _get_conn()
    try:
        kp_ids = [r["id"] for r in conn.execute("SELECT id FROM knowledge_points ORDER BY id")]
        q_ids = [r["id"] for r in conn.execute("SELECT id FROM questions ORDER BY id")]
        kp_index = {kp_id: i for i, kp_id in enumerate(kp_ids)}
        q_index = {q_id: j for j, q_id in enumerate(q_ids)}

        Q = np.zeros((len(q_ids), len(kp_ids)), dtype=int)
        for r in conn.execute("SELECT question_id, kp_id FROM q_matrix"):
            Q[q_index[r["question_id"]], kp_index[r["kp_id"]]] = 1
        return Q
    finally:
        conn.close()


def get_student_responses(student_id: int) -> np.ndarray:
    """获取某学生的作答记录，返回 (n_questions,) numpy array。"""
    conn = _get_conn()
    try:
        q_ids = [r["id"] for r in conn.execute("SELECT id FROM questions ORDER BY id")]
        q_index = {q_id: j for j, q_id in enumerate(q_ids)}

        X = np.zeros(len(q_ids), dtype=int)
        for r in conn.execute(
            "SELECT question_id, correct FROM responses WHERE student_id = ?",
            (student_id,),
        ):
            X[q_index[r["question_id"]]] = r["correct"]
        return X
    finally:
        conn.close()


def get_kg_edges() -> list[dict]:
    """获取知识图谱边。"""
    conn = _get_conn()
    try:
        rows = conn.execute(
            "SELECT from_kp_id, to_kp_id, edge_type FROM kg_edges ORDER BY from_kp_id, to_kp_id"
        ).fetchall()
        return [
            {
                "from_kp_id": r["from_kp_id"],
                "to_kp_id": r["to_kp_id"],
                "edge_type": r["edge_type"],
            }
            for r in rows
        ]
    finally:
        conn.close()


def check_db_exists() -> bool:
    """检查数据库是否存在且有数据。"""
    if not Path(DB_PATH).exists():
        return False

    conn = _get_conn()
    try:
        tables = [
            "students",
            "questions",
            "knowledge_points",
            "responses",
            "q_matrix",
            "kg_edges",
        ]
        for table in tables:
            exists = conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
                (table,),
            ).fetchone()
            if exists is None:
                return False
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            if count == 0:
                return False
        return True
    finally:
        conn.close()
