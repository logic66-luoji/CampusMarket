"""C 的隔离测试环境（tests/transactions 共用）。

安全原则：
  * 原始 database/campus_market.db 是 A 的基准快照，测试**绝不**直接写它；
  * 每个测试用例先把基准库按字节复制到临时目录，再把三个 repository 模块里
    实际引用的连接工厂换成指向副本的工厂（注意：product_repository.py 用的是
    `from database.connection import get_connection` 的名字绑定，只 monkeypatch
    database.connection 模块对其无效，必须逐模块替换）；
  * 被测对象保持真实实现——buy_product / get_my_purchases 等业务代码一字不改；
  * tearDown 恢复原工厂、删除临时副本，并复核基准库 SHA-256 未变。

只依赖 Python 标准库（sqlite3 / unittest / threading），不引入新依赖。
"""
from __future__ import annotations

import hashlib
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = THIS_DIR.parents[1]          # CampusMarket_Final/
for p in (str(PROJECT_ROOT), str(THIS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

ORIGINAL_DB = PROJECT_ROOT / "database" / "campus_market.db"
ORIGINAL_DB_SHA256 = (
    "d92adc770fed9df9e30d58944a7ecd7c18f3cc40a1fc244cf90f101337245fdd"
)

_TMP_ROOT = THIS_DIR / ".tmp"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _factory_for(db_path: Path):
    """与 database.connection.get_connection 相同约定的连接工厂：
    绝对路径 + row_factory=Row + 每连接 PRAGMA foreign_keys=ON。"""

    def get_connection() -> sqlite3.Connection:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    return get_connection


class IsolatedTestMixin:
    """unittest 混入：setUp 复制库并接管连接工厂，tearDown 复原并清理。"""

    def setUp(self) -> None:
        import database.connection as db_conn
        import repositories.category_repository as cat_repo
        import repositories.product_repository as prod_repo
        import repositories.user_repository as user_repo

        _TMP_ROOT.mkdir(exist_ok=True)
        self._tmp_dir = Path(tempfile.mkdtemp(prefix="cm_test_", dir=_TMP_ROOT))
        self.test_db = self._tmp_dir / "campus_market_test.db"
        shutil.copy2(ORIGINAL_DB, self.test_db)

        factory = _factory_for(self.test_db)
        self._patched = [
            (prod_repo, "get_connection", prod_repo.get_connection),
            (cat_repo, "get_connection", cat_repo.get_connection),
            (user_repo, "get_connection", user_repo.get_connection),
            (db_conn, "get_connection", db_conn.get_connection),
        ]
        for module, name, _ in self._patched:
            setattr(module, name, factory)
        self.factory = factory

    def tearDown(self) -> None:
        for module, name, original in self._patched:
            setattr(module, name, original)
        shutil.rmtree(self._tmp_dir, ignore_errors=True)
        # 防回归：无论测试是否通过，原始基准库必须保持字节级不变。
        assert sha256_of(ORIGINAL_DB) == ORIGINAL_DB_SHA256, (
            "原始基准库 database/campus_market.db 被修改！"
        )

    # ---- 测试数据便捷方法（全部经真实 repository 接口，SQL 不出 repositories）----

    def make_available_product(self, seller_id: int, title: str = "测试商品",
                               price: float = 66.5,
                               category_id: int = 1) -> int:
        """在测试副本中用真实发布接口创建一件在售商品，返回 product_id。"""
        from repositories.product_repository import create_product
        return create_product(
            seller_id=seller_id, category_id=category_id, title=title,
            description="由 tests/transactions 创建的隔离测试商品", price=price,
        )

    def product_row(self, product_id: int) -> dict | None:
        from repositories.product_repository import get_product_detail
        return get_product_detail(product_id)

    def pick_users(self, exclude_ids: set[int], count: int) -> list[int]:
        """从副本库挑 count 个不属 exclude_ids 的既有用户 id（不新增用户）。"""
        conn = self.factory()
        try:
            rows = conn.execute(
                "SELECT user_id FROM users WHERE user_id NOT IN "
                f"({', '.join('?' * len(exclude_ids))}) ORDER BY user_id "
                "LIMIT ?",
                (*exclude_ids, count),
            ).fetchall()
            return [r[0] for r in rows]
        finally:
            conn.close()
