"""pytest 全局配置：让 API 测试使用隔离的临时数据库，并自动种子数据。"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

# 必须在导入 app 之前设置环境变量，指向临时数据库文件。
# 这样 app.config 在首次导入时就会读取到这个路径（而非 data/diagnosis.db），
# 从而让测试自包含，不依赖本地已种子的数据文件。
_TMP_DIR = Path(tempfile.mkdtemp(prefix="diagnosis-test-"))
_TMP_DB = _TMP_DIR / "test.db"
os.environ["DIAGNOSIS_DB"] = str(_TMP_DB)


@pytest.fixture(scope="session", autouse=True)
def seed_test_database() -> None:
    """会话开始时，向临时数据库写入模拟数据。"""
    from app import seed
    from app.config import DB_PATH

    assert seed.seed_database(DB_PATH), "测试数据库种子失败"
