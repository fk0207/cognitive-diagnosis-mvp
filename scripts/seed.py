"""种子脚本：生成模拟数据并写入 SQLite。

用法：python scripts/seed.py
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app import config  # noqa: E402
from app import seed  # noqa: E402


def main() -> int:
    print("生成模拟数据...")
    print(f"写入 SQLite: {config.DB_PATH}")
    ok = seed.seed_database(config.DB_PATH)
    if ok:
        print("\n[OK] 数据生成并写入成功")
        return 0
    print("\n[FAIL] 数据校验失败")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
