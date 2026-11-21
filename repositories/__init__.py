"""数据访问层公共入口（2026-11-19 随队友更新包同步）。

数据模型变更：orders 表已移除，成交状态记录在
products.buyer_id / products.finished_at / products.status。
购买不再写独立订单表，而是由 product_repository.buy_product() 在单个事务内
条件更新同一行（WHERE status='available'），靠原子性防止重复购买。

给后续接手者的约定：
  1. 一律用 `from database.connection import get_connection` 取连接。该工厂
     开启 PRAGMA foreign_keys 并设置 row_factory=sqlite3.Row。
  2. 购买走 `buy_product(product_id, buyer_id)`，查询购买记录走
     `get_my_purchases(buyer_id)`；不要自己拼 UPDATE 绕过防超卖逻辑。
  3. `get_product_detail(product_id)` 返回完整商品行（任意状态），
     含 product_id / title / price / seller_id / status / buyer_id / finished_at。
  4. 不要改 schema.sql、索引或已有 10,000 行 products——A 同学的
     §6 索引前后对比实验依赖这份数据保持不变。
"""
from database.connection import get_connection, get_db_path
from repositories.category_repository import get_categories
from repositories.product_repository import (
    buy_product,
    count_products,
    create_product,
    delete_product,
    get_my_purchases,
    get_product_detail,
    get_user_products,
    search_products,
    update_product,
)
from repositories.user_repository import (
    get_user_by_id,
    get_user_by_username,
    list_test_users,
)

__all__ = [
    "get_connection",
    "get_db_path",
    "get_categories",
    "count_products",
    "search_products",
    "get_product_detail",
    "get_user_products",
    "create_product",
    "update_product",
    "delete_product",
    "buy_product",
    "get_my_purchases",
    "list_test_users",
    "get_user_by_id",
    "get_user_by_username",
]
