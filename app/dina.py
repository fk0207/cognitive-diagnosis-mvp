"""DINA 模型推理引擎。

实现固定 slip/guess 的简化 DINA 变体：给定 Q 矩阵与作答 X，
枚举全部 2^K 种掌握模式，用均匀先验计算后验掌握概率。
"""
from __future__ import annotations

from itertools import product

import numpy as np


def compute_ideal_response(Q: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    """计算理想作答 η（合取模型）。

    η_j = ∏_{k: Q[j,k]=1} α_k，即题目 j 要求的全部知识点都被掌握时 η_j = 1。
    """
    Q = np.asarray(Q)
    alpha = np.asarray(alpha)
    # 不考察的知识点用 1 占位，逐题按行求积
    return np.prod(np.where(Q == 1, alpha, 1.0), axis=1)


def compute_likelihood(X, Q, alpha, s: float = 0.1, g: float = 0.2) -> float:
    """计算给定掌握模式 α 下观察到作答 X 的联合概率。

    - η_j = 1: 答对概率 1-s，答错概率 s
    - η_j = 0: 答对概率 g，答错概率 1-g
    """
    X = np.asarray(X, dtype=int)
    eta = compute_ideal_response(Q, alpha)
    p_correct = np.where(eta == 1, 1 - s, g)
    probs = np.where(X == 1, p_correct, 1 - p_correct)
    return float(np.prod(probs))


def compute_posterior(X, Q, s: float = 0.1, g: float = 0.2) -> dict:
    """枚举全部 2^K 种掌握模式，返回归一化后验 {alpha_tuple: probability}。

    后验 ∝ 似然 × 均匀先验(1/2^K)。
    """
    Q = np.asarray(Q)
    K = Q.shape[1]
    prior = 1.0 / (2 ** K)
    unnormalized: dict[tuple, float] = {}
    for pattern in product([0, 1], repeat=K):
        lik = compute_likelihood(X, Q, np.array(pattern), s, g)
        unnormalized[pattern] = prior * lik
    total = sum(unnormalized.values())
    return {pattern: value / total for pattern, value in unnormalized.items()}


def compute_mastery_probability(X, Q, s: float = 0.1, g: float = 0.2) -> np.ndarray:
    """计算单个学生每个知识点的掌握概率 P(α_k = 1 | X)。"""
    Q = np.asarray(Q)
    K = Q.shape[1]
    posterior = compute_posterior(X, Q, s, g)
    mastery = np.zeros(K)
    for pattern, prob in posterior.items():
        for k in range(K):
            if pattern[k] == 1:
                mastery[k] += prob
    return mastery


def compute_all_students_mastery(X_matrix, Q, s: float = 0.1, g: float = 0.2) -> np.ndarray:
    """批量计算所有学生的掌握概率，返回 (N, K) 数组。"""
    X_matrix = np.asarray(X_matrix)
    return np.array([compute_mastery_probability(X, Q, s, g) for X in X_matrix])
