"""DINA 算法测试用例。

测试范围：
1. 理想作答 η 的计算（合取模型）
2. 作答似然的计算
3. 后验掌握概率的计算
4. 边界情况（全对、全错、无信息退化）
"""
import numpy as np
import pytest

# ========== 测试数据 ==========
# 5 个知识点
N_KPS = 5
# 20 道题，每道题关联 1-3 个知识点
Q = np.array([
    [1, 0, 0, 0, 0],  # 题1：仅考 KP1
    [0, 1, 0, 0, 0],  # 题2：仅考 KP2
    [0, 0, 1, 0, 0],  # 题3：仅考 KP3
    [0, 0, 0, 1, 0],  # 题4：仅考 KP4
    [0, 0, 0, 0, 1],  # 题5：仅考 KP5
    [1, 1, 0, 0, 0],  # 题6：考 KP1+KP2
    [0, 1, 1, 0, 0],  # 题7：考 KP2+KP3
    [0, 0, 1, 1, 0],  # 题8：考 KP3+KP4
    [0, 0, 0, 1, 1],  # 题9：考 KP4+KP5
    [1, 0, 0, 0, 0],  # 题10：仅考 KP1
    [0, 1, 0, 0, 0],  # 题11：仅考 KP2
    [0, 0, 1, 0, 0],  # 题12：仅考 KP3
    [0, 0, 0, 1, 0],  # 题13：仅考 KP4
    [0, 0, 0, 0, 1],  # 题14：仅考 KP5
    [1, 1, 1, 0, 0],  # 题15：考 KP1+KP2+KP3
    [0, 1, 1, 1, 0],  # 题16：考 KP2+KP3+KP4
    [0, 0, 1, 1, 1],  # 题17：考 KP3+KP4+KP5
    [1, 0, 0, 0, 0],  # 题18：仅考 KP1
    [0, 1, 0, 0, 0],  # 题19：仅考 KP2
    [0, 0, 1, 0, 0],  # 题20：仅考 KP3
])

# 学生作答（全对）
X_ALL_CORRECT = np.ones(20)
# 学生作答（全错）
X_ALL_WRONG = np.zeros(20)


class TestIdealResponse:
    """测试理想作答 η 的计算。"""

    def test_master_all_kps(self):
        """掌握所有知识点 → 所有题理想作答为 1。"""
        from app.dina import compute_ideal_response
        alpha = np.ones(5)  # 掌握全部 5 个知识点
        eta = compute_ideal_response(Q, alpha)
        assert np.all(eta == 1), "掌握全部知识点时，所有题理想作答应为 1"

    def test_master_none(self):
        """不掌握任何知识点 → 所有题理想作答为 0。"""
        from app.dina import compute_ideal_response
        alpha = np.zeros(5)
        eta = compute_ideal_response(Q, alpha)
        assert np.all(eta == 0), "不掌握任何知识点时，所有题理想作答应为 0"

    def test_master_only_kp1(self):
        """只掌握 KP1 → 仅考 KP1 的题 η=1，其余为 0。"""
        from app.dina import compute_ideal_response
        alpha = np.array([1, 0, 0, 0, 0])
        eta = compute_ideal_response(Q, alpha)
        # 仅考 KP1 的题：1, 10, 18
        assert eta[0] == 1   # 题1
        assert eta[9] == 1   # 题10
        assert eta[17] == 1  # 题18
        # 考其他知识点的题应为 0
        assert eta[1] == 0   # 题2（考 KP2）
        assert eta[5] == 0   # 题6（考 KP1+KP2，但 KP2 没掌握）


class TestLikelihood:
    """测试作答似然的计算。"""

    def test_correct_prob_when_ideal(self):
        """η=1 时，答对概率 = 1-s。"""
        from app.dina import compute_likelihood
        s, g = 0.1, 0.2
        alpha = np.ones(5)
        X = np.ones(20)  # 全对
        lik = compute_likelihood(X, Q, alpha, s, g)
        # 所有 η=1，且全对，likelihood = (1-s)^20
        expected = (1 - s) ** 20
        assert abs(lik - expected) < 1e-10

    def test_wrong_prob_when_ideal(self):
        """η=1 时，答错概率 = s。"""
        from app.dina import compute_likelihood
        s, g = 0.1, 0.2
        alpha = np.ones(5)
        X = np.zeros(20)  # 全错
        lik = compute_likelihood(X, Q, alpha, s, g)
        expected = s ** 20
        assert abs(lik - expected) < 1e-10


class TestPosterior:
    """测试后验掌握概率的计算。"""

    def test_full_correct_high_prob(self):
        """全部答对 → 掌握概率应接近 1。"""
        from app.dina import compute_mastery_probability
        s, g = 0.1, 0.2
        prob = compute_mastery_probability(X_ALL_CORRECT, Q, s, g)
        # 所有知识点的掌握概率应 > 0.9
        assert np.all(prob > 0.9), f"全对时掌握概率应 > 0.9，实际: {prob}"

    def test_full_wrong_low_prob(self):
        """全部答错 → 掌握概率应接近 0。"""
        from app.dina import compute_mastery_probability
        s, g = 0.1, 0.2
        prob = compute_mastery_probability(X_ALL_WRONG, Q, s, g)
        # 所有知识点的掌握概率应 < 0.1
        assert np.all(prob < 0.1), f"全错时掌握概率应 < 0.1，实际: {prob}"

    def test_posterior_sum_to_one(self):
        """后验概率对所有 32 种模式求和应为 1。"""
        from app.dina import compute_posterior
        s, g = 0.1, 0.2
        posteriors = compute_posterior(X_ALL_CORRECT, Q, s, g)
        assert abs(sum(posteriors.values()) - 1.0) < 1e-10

    def test_no_info_degenerate(self):
        """s=g=0.5 时，后验退化为均匀先验（1/32）。"""
        from app.dina import compute_posterior
        posteriors = compute_posterior(X_ALL_CORRECT, Q, s=0.5, g=0.5)
        expected = 1.0 / 32
        for prob in posteriors.values():
            assert abs(prob - expected) < 1e-10

    def test_marginal_probability_in_range(self):
        """所有掌握概率应在 [0, 1] 范围内。"""
        from app.dina import compute_mastery_probability
        s, g = 0.1, 0.2
        prob = compute_mastery_probability(X_ALL_CORRECT, Q, s, g)
        assert np.all(prob >= 0) and np.all(prob <= 1)


class TestAllStudents:
    """测试批量计算所有学生的掌握概率。"""

    def test_shape_correct(self):
        """返回矩阵应为 (n_students, n_kps)。"""
        from app.dina import compute_all_students_mastery
        # 构造 3 个学生的作答
        X_matrix = np.array([X_ALL_CORRECT, X_ALL_WRONG, np.random.binomial(1, 0.5, 20)])
        result = compute_all_students_mastery(X_matrix, Q, s=0.1, g=0.2)
        assert result.shape == (3, 5)

    def test_first_student_all_correct(self):
        """第一个学生全对 → 掌握概率应高。"""
        from app.dina import compute_all_students_mastery
        X_matrix = np.array([X_ALL_CORRECT])
        result = compute_all_students_mastery(X_matrix, Q, s=0.1, g=0.2)
        assert np.all(result[0] > 0.9)
