"""LLM 学习建议测试用例。

覆盖：
1. 降级模板（薄弱点/全掌握）
2. 未配置 API Key 时的降级
3. LLM 成功路径（mock requests.post 返回 200）
4. 非 200 / 网络异常时的降级
"""
from __future__ import annotations

from unittest.mock import Mock

from app import llm


class TestFallbackSuggestion:
    """测试模板降级建议。"""

    def test_no_weak_points(self):
        """无薄弱知识点时返回鼓励文案。"""
        mastery = [{"kp_name": "分数加法", "probability": 0.9}]
        text = llm._fallback_suggestion(1, mastery)
        assert "恭喜" in text

    def test_with_weak_points_lists_only_weak(self):
        """薄弱知识点应被列出，已掌握的不出现。"""
        mastery = [
            {"kp_name": "分数加法", "probability": 0.3},
            {"kp_name": "分数减法", "probability": 0.2},
            {"kp_name": "分数乘法", "probability": 0.9},
        ]
        text = llm._fallback_suggestion(1, mastery)
        assert "学生 1" in text
        assert "分数加法" in text
        assert "分数减法" in text
        assert "分数乘法" not in text


class TestGenerateSuggestionWithoutKey:
    """未配置 API Key 时应降级。"""

    def test_missing_key_falls_back(self, monkeypatch):
        monkeypatch.setattr(llm, "DEEPSEEK_API_KEY", "")
        text = llm.generate_suggestion(1, [{"kp_name": "分数加法", "probability": 0.3}])
        assert "分数加法" in text

    def test_placeholder_key_falls_back(self, monkeypatch):
        monkeypatch.setattr(llm, "DEEPSEEK_API_KEY", "your_api_key_here")
        text = llm.generate_suggestion(1, [{"kp_name": "分数加法", "probability": 0.3}])
        assert "分数加法" in text


class TestGenerateSuggestionWithKey:
    """配置 API Key 后走 LLM 路径（mock 网络调用）。"""

    def test_returns_llm_content_on_200(self, monkeypatch):
        """200 响应时返回 LLM 生成的内容。"""
        monkeypatch.setattr(llm, "DEEPSEEK_API_KEY", "sk-test")
        fake_resp = Mock()
        fake_resp.status_code = 200
        fake_resp.json.return_value = {"choices": [{"message": {"content": "个性化建议内容"}}]}
        mock_post = Mock(return_value=fake_resp)
        monkeypatch.setattr(llm.requests, "post", mock_post)

        text = llm.generate_suggestion(1, [{"kp_name": "分数加法", "probability": 0.5}])

        assert text == "个性化建议内容"
        mock_post.assert_called_once()
        assert "/v1/chat/completions" in mock_post.call_args.args[0]
        assert mock_post.call_args.kwargs["json"]["model"] == llm.DEEPSEEK_MODEL

    def test_falls_back_on_non_200(self, monkeypatch):
        """非 200 响应时降级为模板建议。"""
        monkeypatch.setattr(llm, "DEEPSEEK_API_KEY", "sk-test")
        fake_resp = Mock()
        fake_resp.status_code = 500
        monkeypatch.setattr(llm.requests, "post", Mock(return_value=fake_resp))

        text = llm.generate_suggestion(1, [{"kp_name": "分数加法", "probability": 0.3}])
        assert "分数加法" in text

    def test_falls_back_on_exception(self, monkeypatch):
        """网络异常时降级为模板建议。"""
        monkeypatch.setattr(llm, "DEEPSEEK_API_KEY", "sk-test")

        def boom(*args, **kwargs):
            raise RuntimeError("network down")

        monkeypatch.setattr(llm.requests, "post", boom)

        text = llm.generate_suggestion(1, [{"kp_name": "分数加法", "probability": 0.3}])
        assert "分数加法" in text
