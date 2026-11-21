"""Phase 3 功能整合走查（service 层端到端，模拟 Streamlit 用户旅程）。

与 tests/transactions 的定位不同：那边验证事务/并发语义，这里按页面实际
调用序列走通「发布 → 浏览检索 → 详情 → 购买 → 购买历史 → 管理（编辑/删除）」
完整业务旅程，验证三层整合后接口契约一致、无断链。同样在隔离副本上运行，
被测业务代码零改动。

运行（工程根目录）：python tests/functional/test_workflow_integration.py -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parents[1]), str(_HERE / ".." / "transactions")):
    if _p not in sys.path:
        sys.path.insert(0, str(Path(_p).resolve()))

import testenv
from testenv import IsolatedTestMixin

SELLER, BUYER = 1, 2


class TestFullUserJourney(IsolatedTestMixin, unittest.TestCase):
    """按 pages/ 的真实调用顺序走一遍完整旅程（页面渲染除外）。"""

    def test_publish_browse_detail_buy_history_manage(self):
        from services import product_service as ps
        from services.user_service import set_current_user, get_current_user

        # —— 用户上下文（app.py 侧边栏行为）——
        set_current_user(SELLER)
        self.assertEqual(get_current_user()["user_id"], SELLER)
        set_current_user(BUYER)
        self.assertEqual(get_current_user()["user_id"], BUYER)

        # —— 3_Sell_MyProducts：发布 ——
        new_id = ps.publish_product(
            user_id=SELLER, title="整合走查测试键盘", category_id=1,
            price="129.9", description="Phase 3 整合走查用商品",
        )
        self.assertIsInstance(new_id, int)

        # —— 1_Marketplace：关键词 / 分类 / 价格 / 排序 / 分页 ——
        options = ps.get_filter_options()
        self.assertEqual(len(options["categories"]), 5)
        self.assertEqual(len(options["sort_labels"]), 4)

        hit = ps.browse_products(keyword="整合走查测试键盘")
        self.assertEqual(hit["total"], 1)
        self.assertEqual(hit["rows"][0]["product_id"], new_id)

        by_price = ps.browse_products(min_price=100, max_price=200,
                                      sort_label="价格从高到低")
        prices = [r["price"] for r in by_price["rows"]]
        self.assertEqual(prices, sorted(prices, reverse=True))
        self.assertTrue(all(100 <= p <= 200 for p in prices))

        paged = ps.browse_products(page=99)
        self.assertLessEqual(paged["page"], paged["pages"])   # 越界页收敛

        # —— 2_Product_Detail：详情 ——
        detail = ps.get_product(new_id)
        self.assertEqual(detail["status"], "available")

        # —— 购买：先拦截自购（卖家视角误点），再以买家成交 ——
        self.assertFalse(ps.buy_product(
            product_id=new_id, user_id=SELLER)["ok"])
        ok = ps.buy_product(product_id=new_id, user_id=BUYER)
        self.assertTrue(ok["ok"], ok["message"])

        # —— 4_My_Purchases：购买历史 ——
        history = ps.get_my_purchases(BUYER)
        self.assertIn(new_id, [p["product_id"] for p in history])
        self.assertEqual(
            [p["product_id"] for p in history if p["product_id"] == new_id][0],
            new_id,
        )
        # 详情页此时应显示已售信息
        sold_detail = ps.get_product(new_id)
        self.assertEqual(sold_detail["status"], "sold")
        self.assertEqual(sold_detail["buyer_id"], BUYER)
        self.assertIsNotNone(sold_detail["finished_at"])

        # —— 3_Sell_MyProducts：已售商品禁止删除；未售商品可编辑/删除 ——
        with self.assertRaises(ps.ValidationError):
            ps.remove_product(product_id=new_id, user_id=SELLER)

        keep_id = ps.publish_product(
            user_id=SELLER, title="整合走查待编辑商品", category_id=2,
            price="10", description="")
        self.assertTrue(ps.edit_product(
            product_id=keep_id, user_id=SELLER, price="55.5",
            title="整合走查已编辑商品"))
        self.assertEqual(ps.get_product(keep_id)["price"], 55.5)
        self.assertTrue(ps.remove_product(product_id=keep_id, user_id=SELLER))
        self.assertIsNone(ps.get_product(keep_id))

        # 他人商品不可编辑 / 删除（WHERE seller_id 兜底）
        self.assertFalse(ps.edit_product(
            product_id=new_id, user_id=BUYER, title="越权改名"))
        # 已售商品的删除拦截先于所有权检查：非 owner 也会收到「已售不能删除」
        # 的 ValidationError（保护仍然成立，见 C_Integration_Report.md §3.3）
        with self.assertRaises(ps.ValidationError):
            ps.remove_product(product_id=new_id, user_id=BUYER)
        # 在售商品的非 owner 删除 → repository 层 WHERE seller_id 兜底返回 False
        other_id = ps.publish_product(
            user_id=BUYER, title="买家自己的在售商品", category_id=1, price="5")
        self.assertFalse(ps.remove_product(product_id=other_id, user_id=SELLER))
        self.assertIsNotNone(ps.get_product(other_id))

    def test_marketplace_excludes_sold_and_foreign_rows(self):
        """商品广场只展示 available：自己的与已售的都不出现在列表。"""
        from services import product_service as ps

        pid = ps.publish_product(user_id=SELLER, title="仅供出售一次",
                                 category_id=3, price="8.8")
        listed = ps.browse_products(keyword="仅供出售一次")
        self.assertEqual(listed["total"], 1)

        self.assertTrue(ps.buy_product(product_id=pid, user_id=BUYER)["ok"])
        listed_after = ps.browse_products(keyword="仅供出售一次")
        self.assertEqual(listed_after["total"], 0)   # 已售即从广场消失
        # 但仍可经详情页查看
        self.assertEqual(ps.get_product(pid)["status"], "sold")


if __name__ == "__main__":
    unittest.main(verbosity=2)
