"""数据模拟器：生成 Q 矩阵、知识图谱、学生掌握模式与作答记录。

所有随机性使用固定随机种子，保证结果可复现。
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from app.config import GUESS, SLIP

N_KNOWLEDGE_POINTS = 5
N_QUESTIONS = 20
N_STUDENTS = 10

# 知识点名称（顺序即知识点 id 顺序，与前置链一致）
KP_NAMES = ["分数加法", "分数减法", "分数乘法", "分数除法", "分数混合运算"]

DEFAULT_SEED = 42


@dataclass
class SimulatedDataset:
    """一次模拟生成的全部数据。"""
    kp_names: list[str]
    q_matrix: list[list[int]]                     # [n_questions][n_kps]
    kg_edges: list[tuple[int, int, str]]          # (from_kp_id, to_kp_id, edge_type)
    mastery_patterns: list[list[int]]             # [n_students][n_kps]
    responses: list[list[int]]                    # [n_students][n_questions]
    slip: float
    guess: float


def generate_q_matrix(
    n_questions: int = N_QUESTIONS,
    n_kps: int = N_KNOWLEDGE_POINTS,
    min_kps: int = 1,
    max_kps: int = 3,
    seed: int = DEFAULT_SEED,
) -> list[list[int]]:
    """生成 n_questions × n_kps 的 Q 矩阵，每道题关联 min_kps~max_kps 个知识点。

    返回 [n_questions][n_kps] 的 0/1 列表，并保证每个知识点至少被一道题覆盖。
    """
    rng = random.Random(seed)
    q = [[0] * n_kps for _ in range(n_questions)]

    # 1) 每道题至少关联 1 个知识点
    for j in range(n_questions):
        q[j][rng.randrange(n_kps)] = 1

    # 2) 保证每个知识点至少被覆盖一次（挑一道关联数未满的题补上）
    for kp in range(n_kps):
        if not any(q[j][kp] for j in range(n_questions)):
            candidates = [j for j in range(n_questions) if sum(q[j]) < max_kps]
            q[rng.choice(candidates)][kp] = 1

    # 3) 随机把每道题扩充到目标数量（min_kps~max_kps）
    for j in range(n_questions):
        target = rng.randint(min_kps, max_kps)
        available = [kp for kp in range(n_kps) if not q[j][kp]]
        extra = max(0, min(target - sum(q[j]), len(available)))
        for kp in rng.sample(available, extra):
            q[j][kp] = 1

    return q


def generate_knowledge_graph(
    n_kps: int = N_KNOWLEDGE_POINTS,
) -> list[tuple[int, int, str]]:
    """生成线性前置链 KP1 → KP2 → … → KPn，边类型为 'prerequisite'。

    返回 [(from_kp_id, to_kp_id, edge_type), ...]，id 从 1 开始。
    """
    return [(i, i + 1, "prerequisite") for i in range(1, n_kps)]


def generate_student_mastery_patterns(
    n_students: int = N_STUDENTS,
    n_kps: int = N_KNOWLEDGE_POINTS,
    seed: int = DEFAULT_SEED,
) -> list[list[int]]:
    """生成 n_students 个学生的掌握模式，遵循线性前置约束。

    线性前置链下，合法掌握模式必为前缀形式 [1]*t + [0]*(n_kps-t)：
    掌握知识点 k 必先掌握 1..k-1。t 为每个学生随机抽取的掌握深度（0~n_kps）。
    """
    rng = random.Random(seed)
    patterns = []
    for _ in range(n_students):
        t = rng.randint(0, n_kps)
        patterns.append([1] * t + [0] * (n_kps - t))
    return patterns


def simulate_responses(
    q_matrix: list[list[int]],
    mastery_patterns: list[list[int]],
    slip: float = SLIP,
    guess: float = GUESS,
    seed: int = DEFAULT_SEED,
) -> list[list[int]]:
    """用掌握模式 + Q 矩阵 + slip/guess 模拟作答。

    理想作答 η_ij = 1 当且仅当学生 i 掌握题目 j 要求的全部知识点（合取模型）。
    - η=1: 答对概率 1-slip，答错概率 slip
    - η=0: 答对概率 guess，答错概率 1-guess
    返回 [n_students][n_questions] 的 0/1 矩阵。
    """
    n_kps = len(mastery_patterns[0])
    assert all(len(row) == n_kps for row in q_matrix), "Q 矩阵列数须与知识点数一致"

    rng = random.Random(seed)
    n_questions = len(q_matrix)
    responses: list[list[int]] = []
    for mastery in mastery_patterns:
        row: list[int] = []
        for j in range(n_questions):
            required = [k for k in range(n_kps) if q_matrix[j][k]]
            ideal = all(mastery[k] for k in required)
            p_correct = (1 - slip) if ideal else guess
            row.append(1 if rng.random() < p_correct else 0)
        responses.append(row)
    return responses


def generate_dataset(seed: int = DEFAULT_SEED) -> SimulatedDataset:
    """一次性生成完整模拟数据集（Q 矩阵、知识图谱、掌握模式、作答）。"""
    q_matrix = generate_q_matrix(seed=seed)
    kg_edges = generate_knowledge_graph()
    mastery = generate_student_mastery_patterns(seed=seed)
    responses = simulate_responses(q_matrix, mastery, SLIP, GUESS, seed=seed)
    return SimulatedDataset(
        kp_names=KP_NAMES,
        q_matrix=q_matrix,
        kg_edges=kg_edges,
        mastery_patterns=mastery,
        responses=responses,
        slip=SLIP,
        guess=GUESS,
    )
