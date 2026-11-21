"""Task 2 / Test 2.6：数据完整性测试。

两部分：
  A. 基准库只读核查 —— 对原始 database/campus_market.db 以 mode=ro URI 打开，
     验证无效 buyer_id / seller_id / category_id、sold↔(buyer_id, finished_at)、
     available↔NULL 等规则在**真实历史数据**上成立。只读，绝不修改。
  B. 副本写入核查 —— 在隔离副本上：走完整购买流程后重跑全部规则；
     并直接注入非法数据（非法 status / 负价格 / 无效外键），证明表级
     CHECK 与外键约束在连接工厂（PRAGMA foreign_keys=ON）下真实生效。

运行（工程根目录）：python tests/transactions/test_integrity.py -v
"""
from __future__ import annotations

import sqlite3
import sys
import unittest
from pathlib import Path

# 双模式导入引导（与 test_purchase.py 相同）
_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parents[1]), str(_HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import testenv
from testenv import IsolatedTestMixin, ORIGINAL_DB

SELLER, BUYER = 1, 2

INTEGRITY_RULES_SQL = {
    "无效 buyer_id": """
        SELECT COUNT(*) FROM products p
        LEFT JOIN users u ON u.user_id = p.buyer_id
        WHERE p.buyer_id IS NOT NULL AND u.user_id IS NULL""",
    "无效 seller_id": """
        SELECT COUNT(*) FROM products p
        LEFT JOIN users u ON u.user_id = p.seller_id
        WHERE u.user_id IS NULL""",
    "无效 category_id": """
        SELECT COUNT(*) FROM products p
        LEFT JOIN categories c ON c.category_id = p.category_id
        WHERE c.category_id IS NULL""",
    "已售但缺 buyer_id": """
        SELECT COUNT(*) FROM products
        WHERE status = 'sold' AND buyer_id IS NULL""",
    "已售但缺 finished_at": """
        SELECT COUNT(*) FROM products
        WHERE status = 'sold' AND finished_at IS NULL""",
    "在售却带 buyer_id": """
        SELECT COUNT(*) FROM products
        WHERE status = 'available' AND buyer_id IS NOT NULL""",
    "在售却带 finished_at": """
        SELECT COUNT(*) FROM products
        WHERE status = 'available' AND finished_at IS NOT NULL""",
    "自购成交（buyer=seller）": """
        SELECT COUNT(*) FROM products
        WHERE status = 'sold' AND buyer_id = seller_id""",
    "非法 status 值": """
        SELECT COUNT(*) FROM products
        WHERE status NOT IN ('available', 'sold')""",
    "非法价格（NULL 或负数）": """
        SELECT COUNT(*) FROM products
        WHERE price IS NULL OR price < 0""",
}


def check_rules(conn: sqlite3.Connection) -> dict[str, int]:
    """逐条执行完整性规则，返回 {规则: 违规数}。"""
    return {
        name: conn.execute(sql).fetchone()[0]
        for name, sql in INTEGRITY_RULES_SQL.items()
    }


class TestBaselineDataIntegrity(unittest.TestCase):
    """A. 原始基准库（只读 URI，物理上无法写入）。"""

    def test_baseline_history_satisfies_all_rules(self):
        conn = sqlite3.connect(f"file:{ORIGINAL_DB}?mode=ro", uri=True)
        try:
            violations = check_rules(conn)
            fk_violations = len(conn.execute("PRAGMA foreign_key_check").fetchall())
        finally:
            conn.close()
        for rule, count in violations.items():
            self.assertEqual(count, 0, f"基准库违反规则「{rule}」：{count} 行")
        self.assertEqual(fk_violations, 0,
                         f"PRAGMA foreign_key_check 违规 {fk_violations} 处")


class TestPostPurchaseIntegrity(IsolatedTestMixin, unittest.TestCase):
    """B. 隔离副本：真实购买流程后的完整性 + 约束强制力。"""

    def test_rules_hold_after_real_purchase_flow(self):
        from repositories.product_repository import buy_product

        product_id = self.make_available_product(seller_id=SELLER)
        self.assertEqual(buy_product(product_id, BUYER), "购买成功！")

        conn = self.factory()
        try:
            violations = check_rules(conn)
        finally:
            conn.close()
        for rule, count in violations.items():
            self.assertEqual(count, 0, f"购买后副本违反规则「{rule}」：{count} 行")

    def test_check_constraints_reject_invalid_status_and_price(self):
        conn = self.factory()
        try:
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO products (seller_id, category_id, title, price, "
                    "status) VALUES (1, 1, '非法状态', 10.0, 'shipped')")
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO products (seller_id, category_id, title, price) "
                    "VALUES (1, 1, '负价格', -1.0)")
        finally:
            conn.close()

    def test_foreign_keys_reject_invalid_references(self):
        """连接工厂开启 PRAGMA foreign_keys=ON 后，无效引用必须被拒绝。"""
        conn = self.factory()
        try:
            fk_on = conn.execute("PRAGMA foreign_keys").fetchone()[0]
            self.assertEqual(fk_on, 1, "测试工厂必须开启外键")
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO products (seller_id, category_id, title, price) "
                    "VALUES (99999, 1, '无效卖家', 10.0)")
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO products (seller_id, category_id, title, price) "
                    "VALUES (1, 99999, '无效分类', 10.0)")
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "UPDATE products SET buyer_id = 99999 "
                    "WHERE product_id = (SELECT MIN(product_id) FROM products)")
        finally:
            conn.close()

    def test_rules_catch_bypassed_tampering_then_recover(self):
        """成交字段只应经 buy_product 变更。模拟绕过业务层的半吊子篡改
        （只把 status 改回 available，漏清 buyer_id），规则体系必须报警；
        完整还原后规则应恢复全部通过。"""
        from repositories.product_repository import buy_product

        product_id = self.make_available_product(seller_id=SELLER)
        self.assertEqual(buy_product(product_id, BUYER), "购买成功！")

        conn = self.factory()
        try:
            # 只改 status、漏清 buyer_id / finished_at —— 规则必须抓住
            with conn:
                conn.execute(
                    "UPDATE products SET status='available' "
                    "WHERE product_id=?", (product_id,))
            violations = check_rules(conn)
            self.assertGreater(
                violations["在售却带 buyer_id"] + violations["在售却带 finished_at"],
                0, "半吊子还原未被规则捕获")

            # 完整还原（回到购买前状态）—— 规则恢复全部通过
            with conn:
                conn.execute(
                    "UPDATE products SET status='available', buyer_id=NULL, "
                    "finished_at=NULL WHERE product_id=?", (product_id,))
            violations = check_rules(conn)
            self.assertEqual(
                sum(violations.values()), 0, f"规则误报：{violations}")
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
