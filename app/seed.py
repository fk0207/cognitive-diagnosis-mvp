"""数据库种子逻辑：生成模拟数据并写入 SQLite。

供 scripts/seed.py（命令行）与 tests/conftest.py（测试隔离 DB）复用。
"""
from __future__ import annotations

import sqlite3
from collections import Counter
from pathlib import Path

from app import simulator
from app.config import BASE_DIR

# 按外键依赖逆序删除，保证可重复执行
_TABLES = [
    "responses",
    "q_matrix",
    "kg_edges",
    "students",
    "questions",
    "knowledge_points",
]

_SCHEMA_PATH = BASE_DIR / "app" / "schema.sql"


def drop_tables(conn: sqlite3.Connection) -> None:
    for table in _TABLES:
        conn.execute(f"DROP TABLE IF EXISTS {table}")


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(_SCHEMA_PATH.read_text(encoding="utf-8"))


def insert_data(conn: sqlite3.Connection, ds: simulator.SimulatedDataset) -> None:
    cur = conn.cursor()

    kp_ids: list[int] = []
    for name in ds.kp_names:
        cur.execute("INSERT INTO knowledge_points(name) VALUES (?)", (name,))
        kp_ids.append(cur.lastrowid)

    question_ids: list[int] = []
    for j in range(len(ds.q_matrix)):
        cur.execute("INSERT INTO questions(name) VALUES (?)", (f"题目{j + 1}",))
        question_ids.append(cur.lastrowid)

    student_ids: list[int] = []
    for i in range(len(ds.responses)):
        cur.execute("INSERT INTO students(name) VALUES (?)", (f"学生{i + 1}",))
        student_ids.append(cur.lastrowid)

    for j, row in enumerate(ds.q_matrix):
        for k, val in enumerate(row):
            if val:
                cur.execute(
                    "INSERT INTO q_matrix(question_id, kp_id) VALUES (?, ?)",
                    (question_ids[j], kp_ids[k]),
                )

    for i, row in enumerate(ds.responses):
        for j, correct in enumerate(row):
            cur.execute(
                "INSERT INTO responses(student_id, question_id, correct) VALUES (?, ?, ?)",
                (student_ids[i], question_ids[j], correct),
            )

    for from_kp, to_kp, edge_type in ds.kg_edges:
        cur.execute(
            "INSERT INTO kg_edges(from_kp_id, to_kp_id, edge_type) VALUES (?, ?, ?)",
            (kp_ids[from_kp - 1], kp_ids[to_kp - 1], edge_type),
        )


def verify(conn: sqlite3.Connection) -> bool:
    """运行校验，确认数据生成成功。"""
    cur = conn.cursor()

    def count(table: str) -> int:
        return cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    n_kp = count("knowledge_points")
    n_q = count("questions")
    n_s = count("students")
    n_r = count("responses")
    n_qm = count("q_matrix")
    n_kg = count("kg_edges")

    ok = True

    print(f"知识点数:   {n_kp} (期望 {simulator.N_KNOWLEDGE_POINTS})")
    print(f"题目数:     {n_q} (期望 {simulator.N_QUESTIONS})")
    print(f"学生数:     {n_s} (期望 {simulator.N_STUDENTS})")
    print(f"作答记录:   {n_r} (期望 {simulator.N_STUDENTS * simulator.N_QUESTIONS})")
    print(f"Q矩阵关联:  {n_qm} 条")
    print(f"知识图谱边: {n_kg} (期望 {simulator.N_KNOWLEDGE_POINTS - 1})")

    if n_kp != simulator.N_KNOWLEDGE_POINTS:
        ok = False
    if n_q != simulator.N_QUESTIONS:
        ok = False
    if n_s != simulator.N_STUDENTS:
        ok = False
    if n_r != simulator.N_STUDENTS * simulator.N_QUESTIONS:
        ok = False
    if n_kg != simulator.N_KNOWLEDGE_POINTS - 1:
        ok = False

    for qid, c in cur.execute("SELECT question_id, COUNT(*) FROM q_matrix GROUP BY question_id"):
        if not 1 <= c <= 3:
            ok = False
            print(f"  ! 题目 {qid} 关联 {c} 个知识点，超出 1~3")

    covered = {kp for kp, _ in cur.execute("SELECT kp_id, COUNT(*) FROM q_matrix GROUP BY kp_id")}
    missing = set(range(1, simulator.N_KNOWLEDGE_POINTS + 1)) - covered
    if missing:
        ok = False
        print(f"  ! 知识点 {sorted(missing)} 未被任何题目覆盖")

    bad = cur.execute("SELECT COUNT(*) FROM responses WHERE correct NOT IN (0, 1)").fetchone()[0]
    if bad:
        ok = False
        print(f"  ! 存在 {bad} 条非法作答取值")

    return ok


def seed_database(db_path) -> bool:
    """生成模拟数据并写入指定数据库，返回校验是否通过。"""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    ds = simulator.generate_dataset()
    depths = Counter(sum(p) for p in ds.mastery_patterns)
    print(f"掌握深度分布(掌握知识点数: 学生数): {dict(sorted(depths.items()))}")

    conn = sqlite3.connect(db_path)
    try:
        drop_tables(conn)
        create_schema(conn)
        insert_data(conn, ds)
        conn.commit()
        return verify(conn)
    finally:
        conn.close()
