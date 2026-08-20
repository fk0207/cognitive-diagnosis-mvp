"""LLM 学习建议生成（DeepSeek API）。

降级策略：API Key 未配置或调用失败时，返回模板化建议。
"""
from __future__ import annotations

import os

import requests

from app.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL


def _fallback_suggestion(student_id: int, mastery_list: list) -> str:
    """模板降级建议（不依赖 LLM）。"""
    weak_points = [m for m in mastery_list if m["probability"] < 0.4]
    if not weak_points:
        return "恭喜你已掌握所有知识点，可以挑战更高难度的题目！"

    names = "、".join(m["kp_name"] for m in weak_points)
    return f"学生 {student_id} 在「{names}」上掌握度较低，建议加强相关知识点的学习。"


def generate_suggestion(student_id: int, mastery_list: list) -> str:
    """根据诊断结果生成个性化学习建议。

    Args:
        student_id: 学生 ID
        mastery_list: 掌握概率列表 [{"kp_id": 1, "kp_name": "分数加法", "probability": 0.9}, ...]

    Returns:
        学习建议文本
    """
    # 检查 API Key 是否配置
    if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == "your_api_key_here":
        return _fallback_suggestion(student_id, mastery_list)

    try:
        # 构造 Prompt
        weak_points = [m for m in mastery_list if m["probability"] < 0.4]
        strong_points = [m for m in mastery_list if m["probability"] >= 0.7]

        mastery_text = "\n".join(
            f"- {m['kp_name']}: {m['probability']*100:.1f}%"
            for m in mastery_list
        )

        weak_text = "、".join(m["kp_name"] for m in weak_points) if weak_points else "无"
        strong_text = "、".join(m["kp_name"] for m in strong_points) if strong_points else "无"

        prompt = f"""你是一位经验丰富的教育专家。请根据以下学生的知识掌握情况，生成一段个性化的学习建议（100字以内）。

学生 ID：{student_id}
各知识点掌握概率：
{mastery_text}

薄弱知识点（掌握度 < 40%）：{weak_text}
已掌握知识点（掌握度 >= 70%）：{strong_text}

请给出具体的学习建议，包括：
1. 优先复习的薄弱知识点
2. 建议的学习顺序
3. 鼓励性的语言"""

        # 调用 DeepSeek API
        response = requests.post(
            f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": DEEPSEEK_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500,
                "temperature": 0.7
            },
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        else:
            # API 调用失败，降级
            print(f"[LLM] API 调用失败: {response.status_code}")
            return _fallback_suggestion(student_id, mastery_list)

    except Exception as e:
        # 任何异常都降级，不影响前端
        print(f"[LLM] 异常: {e}")
        return _fallback_suggestion(student_id, mastery_list)
