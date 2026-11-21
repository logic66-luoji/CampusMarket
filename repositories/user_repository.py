"""users 表的数据访问层（B 域，P1）。

本期登录降级为固定测试账号切换，不实现注册与密码校验，故只提供只读函数。
password_hash 字段由 A 的 seed.py 以 sha256 写入，保持数据口径一致。
"""
from __future__ import annotations

from database.connection import get_connection

MAX_TEST_USERS = 100


def list_test_users(limit: int = MAX_TEST_USERS) -> list[dict]:
    """返回可选测试账号（不含密码哈希），供侧边栏下拉切换。"""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT user_id, username, email, created_at FROM users "
            "ORDER BY user_id LIMIT ?",
            (int(limit),),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_user_by_id(user_id) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (int(user_id),)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_user_by_username(username) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()
