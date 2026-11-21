"""统一数据库连接工厂（P0 地基）。

全部 repository 与未来的订单模块都必须通过 get_connection() 取连接：
  * 使用基于 __file__ 的绝对路径，不依赖当前工作目录；
  * 每个连接强制开启 PRAGMA foreign_keys（SQLite 默认为 OFF）；
  * 统一 row_factory = sqlite3.Row，查询结果可直接 dict(row)。

A 同学原 product_repository.py 里的连接串混入了 "python test_repo.py"，
会创建一个空库并导致 "no such table: products"，已由本模块取代。
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH: Path = Path(__file__).resolve().parent / "campus_market.db"


def get_db_path() -> Path:
    """返回数据库文件的绝对路径，供脚本与 README 引用。"""
    return DB_PATH


def get_connection() -> sqlite3.Connection:
    """返回一个已开启外键约束、row_factory 为 sqlite3.Row 的连接。"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
