"""历史补丁（P0）：为早期数据库补齐测试账号。

注意：2026-11-19 队友重新交付了 campus_market.db（1,000 个用户、
10,000 件商品），本脚本已不再需要运行。为防误用，检测到用户数充足时
会直接返回，不修改任何数据。

背景（2026-11-18 的早期库）：A 的 seed.py 中用户 INSERT 缩进落在循环外，
users 只有 1 行，而 products.seller_id 取 1..100，开启外键后无法发布商品，
故曾用 INSERT OR IGNORE 补 99 个账号。该问题在更新后的库中已不存在。
"""
from __future__ import annotations

import hashlib

from database.connection import get_connection

EXTRA_USERS = 99
MIN_USERS_FOR_CURRENT_DB = 1000


def main() -> None:
    conn = get_connection()
    users_before = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    products_before = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]

    if users_before >= MIN_USERS_FOR_CURRENT_DB:
        conn.close()
        print(f"当前数据库已有 {users_before} 个账号，无需补齐；未修改任何数据。")
        print("本脚本仅适用于 2026-11-18 的早期数据库，请勿对更新后的库运行。")
        return

    with conn:
        for i in range(1, EXTRA_USERS + 1):
            username = f"user{i:03d}"
            password_hash = hashlib.sha256(
                f"campusmarket:{username}".encode("utf-8")
            ).hexdigest()
            email = f"{username}@campus.example"
            conn.execute(
                "INSERT OR IGNORE INTO users (username, password_hash, email) "
                "VALUES (?, ?, ?)",
                (username, password_hash, email),
            )

    users_after = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    products_after = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    fk_on = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    id_row = conn.execute("SELECT MIN(user_id), MAX(user_id) FROM users").fetchone()
    conn.close()

    print(f"users:    {users_before} -> {users_after}")
    print(f"products: {products_before} -> {products_after} (must be unchanged)")
    print(f"foreign_keys = {fk_on} (must be 1)")
    print(f"user_id range: {id_row[0]}..{id_row[1]}")


if __name__ == "__main__":
    main()
