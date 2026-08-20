"""全局配置常量（骨架）。

slip/guess 为固定值，替代原 item_params 表。
"""
from __future__ import annotations

import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# SQLite 数据库路径
DB_PATH = os.environ.get("DIAGNOSIS_DB", str(BASE_DIR / "data" / "diagnosis.db"))

# DINA 固定题目参数
SLIP = float(os.environ.get("DINA_SLIP", "0.1"))    # 失误率：本应答对却答错
GUESS = float(os.environ.get("DINA_GUESS", "0.2"))  # 猜测率：本应不会却答对

# DeepSeek（学习建议加分项）
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
