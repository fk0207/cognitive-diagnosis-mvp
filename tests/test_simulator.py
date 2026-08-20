"""数据模拟器测试用例。

测试范围：
1. Q 矩阵生成的正确性
2. 知识图谱生成的正确性
3. 学生掌握模式生成的正确性
4. 作答记录模拟的正确性
5. 完整数据集生成
"""
from __future__ import annotations

import pytest

from app import simulator


class TestQMatrix:
    """测试 Q 矩阵生成。"""

    def test_shape(self):
        """Q 矩阵维度应为 (20, 5)。"""
        q = simulator.generate_q_matrix()
        assert len(q) == 20, f"期望 20 行，实际 {len(q)}"
        assert all(len(row) == 5 for row in q), "每行应有 5 个元素"

    def test_values_binary(self):
        """所有值应为 0 或 1。"""
        q = simulator.generate_q_matrix()
        for row_idx, row in enumerate(q):
            for col_idx, val in enumerate(row):
                assert val in (0, 1), f"Q[{row_idx}][{col_idx}] = {val}，应为 0 或 1"

    def test_min_one_kp_per_question(self):
        """每道题至少关联 1 个知识点。"""
        q = simulator.generate_q_matrix()
        for row_idx, row in enumerate(q):
            assert sum(row) >= 1, f"题目 {row_idx} 未关联任何知识点"

    def test_min_max_kp_per_question(self):
        """每道题关联 1-3 个知识点。"""
        q = simulator.generate_q_matrix()
        for row_idx, row in enumerate(q):
            count = sum(row)
            assert 1 <= count <= 3, f"题目 {row_idx} 关联 {count} 个知识点，超出 1-3 范围"

    def test_all_kps_covered(self):
        """每个知识点至少被一道题覆盖。"""
        q = simulator.generate_q_matrix()
        for kp_idx in range(5):
            covered = any(row[kp_idx] == 1 for row in q)
            assert covered, f"知识点 {kp_idx} 未被任何题目覆盖"

    def test_reproducible_with_same_seed(self):
        """相同种子应产生相同结果。"""
        q1 = simulator.generate_q_matrix(seed=42)
        q2 = simulator.generate_q_matrix(seed=42)
        assert q1 == q2, "相同种子应产生相同的 Q 矩阵"

    def test_different_seeds_produce_different_results(self):
        """不同种子可能产生不同结果（不严格强制，但验证函数接受 seed 参数）。"""
        q1 = simulator.generate_q_matrix(seed=42)
        q2 = simulator.generate_q_matrix(seed=99)
        # 不同种子可能相同也可能不同，这里只验证函数正常接受参数
        assert len(q1) == 20
        assert len(q2) == 20


class TestKnowledgeGraph:
    """测试知识图谱生成。"""

    def test_chain_length(self):
        """5 个知识点应有 4 条边。"""
        edges = simulator.generate_knowledge_graph()
        assert len(edges) == 4, f"期望 4 条边，实际 {len(edges)}"

    def test_edge_type(self):
        """所有边类型应为 prerequisite。"""
        edges = simulator.generate_knowledge_graph()
        for from_id, to_id, edge_type in edges:
            assert edge_type == "prerequisite", f"边类型应为 prerequisite，实际 {edge_type}"

    def test_sequential_chain(self):
        """应为线性链：1→2→3→4→5。"""
        edges = simulator.generate_knowledge_graph()
        expected = [(1, 2), (2, 3), (3, 4), (4, 5)]
        for i, (from_id, to_id, _) in enumerate(edges):
            assert (from_id, to_id) == expected[i], (
                f"期望 {expected[i]}，实际 ({from_id}, {to_id})"
            )

    def test_no_cycles(self):
        """知识图谱不应有环。"""
        edges = simulator.generate_knowledge_graph()
        # 检查是否有环：从任一节点出发，不应能回到自身
        adj = {}
        for from_id, to_id, _ in edges:
            adj.setdefault(from_id, set()).add(to_id)

        def has_cycle(node, visited, rec_stack):
            visited.add(node)
            rec_stack.add(node)
            for neighbor in adj.get(node, set()):
                if neighbor not in visited:
                    if has_cycle(neighbor, visited, rec_stack):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.remove(node)
            return False

        visited = set()
        for node in range(1, 6):
            if node not in visited:
                if has_cycle(node, visited, set()):
                    pytest.fail("知识图谱不应有环")


class TestMasteryPatterns:
    """测试学生掌握模式生成。"""

    def test_student_count(self):
        """应生成 10 个学生的掌握模式。"""
        patterns = simulator.generate_student_mastery_patterns()
        assert len(patterns) == 10, f"期望 10 个学生，实际 {len(patterns)}"

    def test_kp_count_per_student(self):
        """每个学生应有 5 个知识点的掌握状态。"""
        patterns = simulator.generate_student_mastery_patterns()
        for idx, pattern in enumerate(patterns):
            assert len(pattern) == 5, f"学生 {idx} 应有 5 个知识点，实际 {len(pattern)}"

    def test_binary_values(self):
        """所有值应为 0 或 1。"""
        patterns = simulator.generate_student_mastery_patterns()
        for student_idx, pattern in enumerate(patterns):
            for kp_idx, val in enumerate(pattern):
                assert val in (0, 1), f"学生 {student_idx} 知识点 {kp_idx} 的值 {val} 应为 0 或 1"

    def test_prerequisite_constraint(self):
        """掌握模式应遵循前置约束（前缀形式：[1]*t + [0]*(5-t)）。"""
        patterns = simulator.generate_student_mastery_patterns()
        for student_idx, pattern in enumerate(patterns):
            # 找到第一个 0 的位置
            first_zero_idx = pattern.index(0) if 0 in pattern else len(pattern)
            # 第一个 0 之后不应有 1
            for kp_idx in range(first_zero_idx, len(pattern)):
                assert pattern[kp_idx] == 0, (
                    f"学生 {student_idx} 在位置 {kp_idx} 违反前置约束："
                    f"第一个 0 在位置 {first_zero_idx}，但位置 {kp_idx} 是 {pattern[kp_idx]}"
                )

    def test_depths_varied(self):
        """学生掌握深度应多样化（不应所有学生掌握相同数量的知识点）。"""
        patterns = simulator.generate_student_mastery_patterns()
        depths = [sum(p) for p in patterns]
        unique_depths = set(depths)
        assert len(unique_depths) > 1, "学生掌握深度应多样化"

    def test_reproducible(self):
        """相同种子应产生相同结果。"""
        patterns1 = simulator.generate_student_mastery_patterns(seed=42)
        patterns2 = simulator.generate_student_mastery_patterns(seed=42)
        assert patterns1 == patterns2


class TestResponses:
    """测试作答模拟。"""

    def test_shape(self):
        """作答矩阵维度应为 (10, 20)。"""
        q = simulator.generate_q_matrix()
        patterns = simulator.generate_student_mastery_patterns()
        responses = simulator.simulate_responses(q, patterns)
        assert len(responses) == 10, f"期望 10 个学生，实际 {len(responses)}"
        assert all(len(row) == 20 for row in responses), "每个学生应有 20 个作答"

    def test_binary_values(self):
        """所有作答应为 0 或 1。"""
        q = simulator.generate_q_matrix()
        patterns = simulator.generate_student_mastery_patterns()
        responses = simulator.simulate_responses(q, patterns)
        for student_idx, row in enumerate(responses):
            for q_idx, val in enumerate(row):
                assert val in (0, 1), f"学生 {student_idx} 题目 {q_idx} 的值 {val} 应为 0 或 1"

    def test_different_seeds_produce_different_responses(self):
        """不同种子可能产生不同作答。"""
        q = simulator.generate_q_matrix()
        patterns = simulator.generate_student_mastery_patterns()
        responses1 = simulator.simulate_responses(q, patterns, seed=42)
        responses2 = simulator.simulate_responses(q, patterns, seed=99)
        # 不同种子可能相同也可能不同，这里只验证函数正常接受参数
        assert len(responses1) == 10
        assert len(responses2) == 10


class TestFullDataset:
    """测试完整数据集生成。"""

    def test_generate_full_structure(self):
        """generate_dataset 应返回完整数据集结构。"""
        ds = simulator.generate_dataset()

        # 检查 Q 矩阵
        assert len(ds.q_matrix) == 20
        assert all(len(row) == 5 for row in ds.q_matrix)

        # 检查知识图谱
        assert len(ds.kg_edges) == 4

        # 检查掌握模式
        assert len(ds.mastery_patterns) == 10
        assert all(len(p) == 5 for p in ds.mastery_patterns)

        # 检查作答
        assert len(ds.responses) == 10
        assert all(len(r) == 20 for r in ds.responses)

        # 检查知识点名称
        assert len(ds.kp_names) == 5
        assert "分数加法" in ds.kp_names
        assert "分数混合运算" in ds.kp_names

    def test_generate_full_with_custom_seed(self):
        """支持自定义种子。"""
        ds = simulator.generate_dataset(seed=123)
        assert len(ds.q_matrix) == 20
        assert len(ds.responses) == 10
