"""categories 表的数据访问层（B 域，P1）。"""
from __future__ import annotations

from database.connection import get_connection


def get_categories() -> list[dict]:
    """返回全部分类，按 category_id 排序，供筛选下拉框使用。"""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT category_id, name FROM categories ORDER BY category_id"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_category_name(category_id) -> str | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT name FROM categories WHERE category_id = ?",
            (int(category_id),),
        ).fetchone()
        return row["name"] if row else None
    finally:
        conn.close()
