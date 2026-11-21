"""Task 2 / Test 2.1–2.4：购买功能顺序测试（隔离副本上运行）。

覆盖：
  2.1 正常购买        —— available 商品被其他用户购买，buyer_id/status/finished_at
                          正确写入，get_my_purchases 能查到该笔成交；
  2.2 重复购买        —— 已售商品再次购买必须失败，原买家与成交时间不变；
  2.3 购买自己的商品  —— 卖家自购被拒，商品数据不变；
  2.4 不存在的商品    —— 返回「商品不存在」，数据库不发生任何变化。

运行（工程根目录）：python tests/transactions/test_purchase.py -v
或：python -m unittest tests.transactions.test_purchase -v
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

# 双模式导入引导：既能 python tests/transactions/test_purchase.py 直接运行，
# 也能被 python -m unittest discover 以包模块方式导入。
_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parents[1]), str(_HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import testenv
from testenv import IsolatedTestMixin

SELLER, BUYER_B, BUYER_C = 1, 2, 3   # 基准库既有的三个测试账号


class TestNormalPurchase(IsolatedTestMixin, unittest.TestCase):
    """Test 2.1 正常购买。"""

    def test_buy_available_product_succeeds_and_records_transaction(self):
        from repositories.product_repository import (
            buy_product,
            get_my_purchases,
            get_user_products,
        )
        from services.product_service import buy_product as service_buy

        product_id = self.make_available_product(seller_id=SELLER)
        before = self.product_row(product_id)
        self.assertEqual(before["status"], "available")
        self.assertIsNone(before["buyer_id"])
        self.assertIsNone(before["finished_at"])

        # 走 service 层调用，验证页面真实路径（service -> repository -> copy DB）
        result = service_buy(product_id=product_id, user_id=BUYER_B)
        self.assertTrue(result["ok"], result["message"])
        self.assertEqual(result["message"], "购买成功！")

        row = self.product_row(product_id)
        self.assertEqual(row["buyer_id"], BUYER_B)
        self.assertEqual(row["status"], "sold")
        self.assertIsNotNone(row["finished_at"])
        self.assertRegex(row["finished_at"], r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")

        # 成交记录能被买家查到，且包含分类名与卖家信息
        purchases = [
            p for p in get_my_purchases(BUYER_B)
            if p["product_id"] == product_id
        ]
        self.assertEqual(len(purchases), 1)
        self.assertEqual(purchases[0]["category_name"], "电子产品")
        self.assertEqual(purchases[0]["seller_id"], SELLER)

        # 卖家自己的商品列表中该商品状态同步为 sold
        mine = {p["product_id"]: p for p in get_user_products(SELLER)}
        self.assertEqual(mine[product_id]["status"], "sold")


class TestRepeatPurchase(IsolatedTestMixin, unittest.TestCase):
    """Test 2.2 重复购买（同一买家与他人各再试一次）。"""

    def test_second_purchase_fails_and_keeps_first_transaction(self):
        from repositories.product_repository import buy_product, get_my_purchases

        product_id = self.make_available_product(seller_id=SELLER)
        self.assertEqual(buy_product(product_id, BUYER_B), "购买成功！")
        first = self.product_row(product_id)

        # 另一个买家抢购同一件已售商品
        msg_c = buy_product(product_id, BUYER_C)
        self.assertEqual(msg_c, "错误：该商品已被别人抢先买走！")
        # 原买家重复购买同一件已售商品
        msg_b = buy_product(product_id, BUYER_B)
        self.assertEqual(msg_b, "错误：该商品已被别人抢先买走！")

        after = self.product_row(product_id)
        self.assertEqual(after["buyer_id"], BUYER_B, "原买家 ID 不得改变")
        self.assertEqual(after["finished_at"], first["finished_at"], "原成交时间不得改变")
        self.assertEqual(after["status"], "sold")

        # BUYER_C 的购买历史不得出现该商品
        self.assertNotIn(
            product_id, [p["product_id"] for p in get_my_purchases(BUYER_C)]
        )
        # 两次失败后，成功购买记录仍只有一条（无重复成交）
        self.assertEqual(
            len([p for p in get_my_purchases(BUYER_B)
                 if p["product_id"] == product_id]), 1
        )


class TestSelfPurchase(IsolatedTestMixin, unittest.TestCase):
    """Test 2.3 卖家购买自己发布的商品。"""

    def test_seller_cannot_buy_own_product(self):
        from repositories.product_repository import buy_product, get_my_purchases

        product_id = self.make_available_product(seller_id=SELLER)
        before = self.product_row(product_id)

        msg = buy_product(product_id, SELLER)
        self.assertEqual(msg, "错误：不能购买自己发布的商品！")

        after = self.product_row(product_id)
        self.assertEqual(after, before, "商品数据不得发生任何变化")
        self.assertEqual(after["status"], "available")
        self.assertIsNone(after["buyer_id"])
        self.assertIsNone(after["finished_at"])
        # 该商品不得出现在卖家的购买历史中（用户 1 在基准库另有历史成交，只断言本商品）
        self.assertNotIn(
            product_id, [p["product_id"] for p in get_my_purchases(SELLER)])


class TestNonexistentProduct(IsolatedTestMixin, unittest.TestCase):
    """Test 2.4 不存在的商品 ID。"""

    def test_buy_nonexistent_product_reports_error_and_changes_nothing(self):
        from repositories.product_repository import buy_product

        conn = self.factory()
        try:
            products_before = conn.execute(
                "SELECT COUNT(*) FROM products").fetchone()[0]
            snapshot_before = conn.execute(
                "SELECT COUNT(*) FROM products WHERE status='sold'").fetchone()[0]
        finally:
            conn.close()

        result = buy_product(999_999_999, BUYER_B)
        self.assertEqual(result, "错误：商品不存在")

        conn = self.factory()
        try:
            self.assertEqual(
                conn.execute("SELECT COUNT(*) FROM products").fetchone()[0],
                products_before,
            )
            self.assertEqual(
                conn.execute(
                    "SELECT COUNT(*) FROM products WHERE status='sold'"
                ).fetchone()[0],
                snapshot_before,
            )
            self.assertIsNone(
                conn.execute(
                    "SELECT * FROM products WHERE product_id = 999999999"
                ).fetchone()
            )
        finally:
            conn.close()
        self.assertIsNone(self.product_row(999_999_999))


if __name__ == "__main__":
    unittest.main(verbosity=2)
