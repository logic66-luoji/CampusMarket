"""联调自检（只读）：验证 2026-11-19 更新后的数据模型与接口契约。

运行：python check_interfaces.py
本脚本不修改任何数据；会顺带实跑 A 的 performance_test.py，
确认索引前后对比与执行计划采集仍然可用。
"""
from __future__ import annotations

import inspect
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> int:
    from database.connection import get_connection, get_db_path
    from repositories.product_repository import (
        buy_product,
        get_my_purchases,
        get_product_detail,
        search_products,
    )

    checks: list[tuple[str, bool, str]] = []

    conn = get_connection()
    fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    checks.append(("统一连接开启外键", fk == 1, f"foreign_keys={fk}"))

    tables = [
        r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
    ]
    checks.append((
        "三张核心表齐全且 orders 已移除",
        {"users", "categories", "products"}.issubset(set(tables))
        and "orders" not in tables,
        ", ".join(tables),
    ))

    columns = [r[1] for r in conn.execute("PRAGMA table_info('products')")]
    checks.append((
        "成交字段 buyer_id / finished_at 存在",
        {"buyer_id", "finished_at"}.issubset(set(columns)),
        ", ".join(columns),
    ))

    status = {
        r[0]: r[1] for r in conn.execute(
            "SELECT status, COUNT(*) FROM products GROUP BY status"
        )
    }
    checks.append((
        "status 同时含在售与已售",
        "available" in status and "sold" in status,
        str(status),
    ))

    counts = {
        t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        for t in ("users", "categories", "products")
    }
    checks.append((
        "数据快照符合队友交付",
        counts == {"users": 1000, "categories": 5, "products": 10000},
        str(counts),
    ))

    violations = len(conn.execute("PRAGMA foreign_key_check").fetchall())
    checks.append(("外键完整性", violations == 0, f"{violations} 处违规"))
    conn.close()

    detail = get_product_detail(1)
    needed = {
        "product_id", "title", "price", "seller_id", "status",
        "buyer_id", "finished_at",
    }
    checks.append((
        "商品详情字段完整",
        detail is not None and needed.issubset(set(detail)),
        ", ".join(sorted(detail)) if detail else "None",
    ))

    checks.append((
        "购买接口可调用",
        callable(buy_product) and callable(get_my_purchases),
        "buy_product" + str(inspect.signature(buy_product)),
    ))

    proc = subprocess.run(
        [sys.executable, "performance_test.py"],
        cwd=ROOT, capture_output=True, text=True, timeout=120,
    )
    checks.append((
        "A 的 performance_test.py 可运行",
        proc.returncode == 0 and "EXPLAIN QUERY PLAN" in proc.stdout,
        f"exit={proc.returncode}",
    ))

    for name, ok, info in checks:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {info}")

    print("\n--- 数据模型（2026-11-19 起）---")
    print("orders 表已移除；成交记录在 products.buyer_id / finished_at / status。")
    print("防超卖由 buy_product 的条件 UPDATE ... WHERE status='available' 保证。")
    print(f"数据库：{get_db_path()}")

    print("\n--- 接口摘要 ---")
    print("search_products" + str(inspect.signature(search_products)))
    print("buy_product" + str(inspect.signature(buy_product)))
    print("get_my_purchases" + str(inspect.signature(get_my_purchases)))
    print("旧调用 search_products(keyword, category_id) 仍兼容。")

    print("\n--- 注意 ---")
    print("不要重跑 database/seed.py（会撞 UNIQUE 并使 products 翻倍）。")
    print("不要运行 database/patch_users.py（新库已有 1000 个账号）。")
    print("不要改 schema.sql / 索引 / 10,000 行 products（A 的 §6 实验基准）。")

    failed = [name for name, ok, _ in checks if not ok]
    print(f"\n结果：{len(checks) - len(failed)}/{len(checks)} 通过")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
