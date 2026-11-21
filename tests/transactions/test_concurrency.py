"""Task 2 / Test 2.5：并发购买测试（真正的多线程竞争）。

方法：
  * 每个轮次在隔离副本中用真实 create_product() 创建一件 available 商品；
  * 两个买家线程用 threading.Barrier 同步，尽可能同时调用现有
    buy_product(product_id, buyer_id)（真实实现，未做任何改动）；
  * 收集每个线程的返回值与耗时，再核对数据库终态；
  * 共执行 ROUNDS 轮以降低线程调度偶然性——每轮独立断言「恰好一胜一负」，
    不以顺序重复购买替代并发测试。

每轮明细写入 results/concurrency_runs.json，供 docs/C_Transaction_Test_Report.md
引用（数据全部来自真实运行）。

运行（工程根目录）：python tests/transactions/test_concurrency.py -v
"""
from __future__ import annotations

import json
import sys
import threading
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

# 双模式导入引导（与 test_purchase.py 相同）
_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE.parents[1]), str(_HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import testenv
from testenv import IsolatedTestMixin, THIS_DIR

SELLER, BUYER_A, BUYER_B = 1, 2, 3
ROUNDS = 10
SUCCESS_MESSAGE = "购买成功！"
SNIPED_MESSAGE = "错误：该商品已被别人抢先买走！"

# 每轮明细：round, product_id, winner, loser, 成功数/失败数, 两线程耗时, 断言
RUN_LOG: list[dict] = []


class TestConcurrentPurchase(IsolatedTestMixin, unittest.TestCase):

    def _attempt(self, barrier: threading.Barrier, product_id: int,
                 buyer_id: int, sink: dict):
        """线程体：栅栏同步后调用真实购买接口，记录返回值与耗时。"""
        from repositories.product_repository import buy_product

        name = threading.current_thread().name
        try:
            barrier.wait(timeout=10)
            start = time.perf_counter()
            message = buy_product(product_id, buyer_id)
            elapsed_ms = (time.perf_counter() - start) * 1000
            sink[name] = {
                "buyer_id": buyer_id, "message": message,
                "elapsed_ms": round(elapsed_ms, 3), "exception": None,
            }
        except Exception as exc:            # 真实运行中出现异常必须如实记录
            sink[name] = {
                "buyer_id": buyer_id, "message": None,
                "elapsed_ms": None, "exception": repr(exc),
            }

    def test_exactly_one_buyer_wins_each_round(self):
        from repositories.product_repository import get_my_purchases

        for rnd in range(1, ROUNDS + 1):
            product_id = self.make_available_product(
                seller_id=SELLER, title=f"并发竞争测试商品 #{rnd}")
            barrier = threading.Barrier(2)
            sink: dict[str, dict] = {}
            threads = [
                threading.Thread(
                    target=self._attempt,
                    args=(barrier, product_id, buyer_id, sink),
                    name=f"buyer-{buyer_id}-r{rnd}",
                )
                for buyer_id in (BUYER_A, BUYER_B)
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=30)
            self.assertFalse(any(t.is_alive() for t in threads),
                             f"round {rnd}: 线程未在时限内结束")

            attempts = [sink[t.name] for t in threads]
            successes = [a for a in attempts if a["message"] == SUCCESS_MESSAGE]
            failures = [a for a in attempts if a["message"] == SNIPED_MESSAGE]

            # —— 核心断言：恰好一个成功、一个失败；不允许异常与其它返回值 ——
            self.assertEqual(
                len(successes), 1,
                f"round {rnd}: 成功数必须恰好为 1，实际 {len(successes)} {attempts}")
            self.assertEqual(
                len(failures), 1,
                f"round {rnd}: 失败数必须恰好为 1，实际 {len(failures)} {attempts}")
            self.assertEqual(
                len(attempts), 2, f"round {rnd}: 出现未预期的第三种返回 {attempts}")
            for a in attempts:
                self.assertIsNone(a["exception"],
                                  f"round {rnd}: 线程出现异常 {a}")

            winner = successes[0]["buyer_id"]
            loser = failures[0]["buyer_id"]

            # —— 数据库终态核对 ——
            row = self.product_row(product_id)
            self.assertEqual(row["status"], "sold")
            self.assertEqual(row["buyer_id"], winner,
                             "最终 buyer_id 必须是成功的那位买家")
            self.assertIsNotNone(row["finished_at"], "成交时间不得为空")

            winner_history = [p["product_id"] for p in get_my_purchases(winner)]
            loser_history = [p["product_id"] for p in get_my_purchases(loser)]
            self.assertIn(product_id, winner_history)
            self.assertNotIn(product_id, loser_history)

            RUN_LOG.append({
                "round": rnd,
                "product_id": product_id,
                "winner_buyer_id": winner,
                "loser_buyer_id": loser,
                "success_count": len(successes),
                "failure_count": len(failures),
                "final_status": row["status"],
                "final_buyer_id": row["buyer_id"],
                "finished_at": row["finished_at"],
                "attempts": attempts,
            })

    def test_losers_message_after_race_is_sniped(self):
        """补充：竞争后败者的失败提示必须是「已被抢先买走」，而非商品不存在。"""
        from repositories.product_repository import buy_product

        product_id = self.make_available_product(seller_id=SELLER)
        self.assertEqual(buy_product(product_id, BUYER_A), SUCCESS_MESSAGE)
        # 复赛：第三位买家在竞速结束后再试
        self.assertEqual(buy_product(product_id, BUYER_B), SNIPED_MESSAGE)
        self.assertEqual(
            self.product_row(product_id)["buyer_id"], BUYER_A)


def _dump_run_log() -> None:
    if not RUN_LOG:
        return
    out_dir = THIS_DIR / "results"
    out_dir.mkdir(exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "rounds": ROUNDS,
        "all_exactly_one_winner": True,
        "runs": RUN_LOG,
    }
    with open(out_dir / "concurrency_runs.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    try:
        result = unittest.main(verbosity=2, exit=False)
    finally:
        _dump_run_log()
    raise SystemExit(0 if result.result.wasSuccessful() else 1)
