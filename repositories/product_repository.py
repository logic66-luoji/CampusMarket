"""products 表的数据访问层（B 域；2026-11-19 合并队友更新包）。

保留 P0–P5 已实现的能力：多条件筛选、白名单排序、分页、发布/编辑/删除；
同时合入队友新增的 buy_product / get_my_purchases 两个接口。

数据模型变更（队友 2026-11-19 更新）：
  * orders 表已移除，成交状态记录在 products.buyer_id / finished_at / status；
  * products 新增 buyer_id、finished_at 两列；status ∈ {available, sold}。

约定：
  * 所有 SQL 只出现在 repositories/，services 与页面不得写 SQL；
  * 读函数返回 list[dict] / dict | None；
  * 写函数统一用 `with conn:` 提交，并在 finally 中关闭连接；
  * ORDER BY 只取自 SORT_COLUMNS 白名单，杜绝拼接注入；
  * 全部连接经 database.connection.get_connection()（绝对路径 + 外键 + Row）。
"""
from __future__ import annotations

from datetime import datetime

from database.connection import get_connection

SORT_COLUMNS = {
    "newest": "p.created_at DESC, p.product_id DESC",
    "oldest": "p.created_at ASC, p.product_id ASC",
    "price_asc": "p.price ASC, p.product_id ASC",
    "price_desc": "p.price DESC, p.product_id DESC",
}
DEFAULT_SORT = "newest"
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

_BASE_SELECT = (
    "SELECT p.*, c.name AS category_name "
    "FROM products p "
    "JOIN categories c ON c.category_id = p.category_id "
)


def _build_where(keyword="", category_id=None, min_price=None, max_price=None):
    clauses = ["p.status = 'available'"]
    params: list = []

    if keyword:
        clauses.append("p.title LIKE ?")
        params.append(f"%{keyword}%")
    if category_id is not None and category_id != "":
        clauses.append("p.category_id = ?")
        params.append(int(category_id))
    if min_price is not None and min_price != "":
        clauses.append("p.price >= ?")
        params.append(float(min_price))
    if max_price is not None and max_price != "":
        clauses.append("p.price <= ?")
        params.append(float(max_price))

    return " AND ".join(clauses), params


def _normalise_paging(page, page_size):
    try:
        page = max(1, int(page))
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = min(max(1, int(page_size)), MAX_PAGE_SIZE)
    except (TypeError, ValueError):
        page_size = DEFAULT_PAGE_SIZE
    return page, page_size


def count_products(keyword="", category_id=None, min_price=None,
                   max_price=None) -> int:
    """返回符合筛选条件的在售商品总数，供分页计算总页数。"""
    where, params = _build_where(keyword, category_id, min_price, max_price)
    conn = get_connection()
    try:
        return conn.execute(
            f"SELECT COUNT(*) FROM products p WHERE {where}", params
        ).fetchone()[0]
    finally:
        conn.close()


def search_products(keyword="", category_id=None, min_price=None,
                    max_price=None, sort=DEFAULT_SORT, page=1,
                    page_size=DEFAULT_PAGE_SIZE) -> list[dict]:
    """多条件筛选 + 白名单排序 + LIMIT/OFFSET 分页，只返回在售商品。

    保持队友原调用方式 `search_products(keyword, category_id)` 可用。
    """
    where, params = _build_where(keyword, category_id, min_price, max_price)
    order_by = SORT_COLUMNS.get(sort, SORT_COLUMNS[DEFAULT_SORT])
    page, page_size = _normalise_paging(page, page_size)
    params.extend([page_size, (page - 1) * page_size])

    query = (
        f"{_BASE_SELECT} WHERE {where} "
        f"ORDER BY {order_by} LIMIT ? OFFSET ?"
    )
    conn = get_connection()
    try:
        return [dict(row) for row in conn.execute(query, params).fetchall()]
    finally:
        conn.close()


def get_user_products(seller_id) -> list[dict]:
    """某用户发布的全部商品，含已售出（由页面展示 status）。"""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM products WHERE seller_id = ? "
            "ORDER BY created_at DESC, product_id DESC",
            (int(seller_id),),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_product_detail(product_id) -> dict | None:
    """返回商品详情（含 buyer_id / finished_at），任意状态均可查。"""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM products WHERE product_id = ?", (int(product_id),)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def _write(sql: str, params: tuple):
    """执行一条写语句，返回 (lastrowid, rowcount)；自动提交并关闭连接。"""
    conn = get_connection()
    try:
        with conn:
            cur = conn.execute(sql, params)
            return cur.lastrowid, cur.rowcount
    finally:
        conn.close()


def create_product(seller_id, category_id, title, description="", price=0.0,
                   image_url=None) -> int:
    """发布一件商品，返回新 product_id。status 用表默认值 'available'。"""
    new_id, _ = _write(
        "INSERT INTO products "
        "(seller_id, category_id, title, description, price, image_url) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (int(seller_id), int(category_id), title, description,
         float(price), image_url),
    )
    return new_id


def update_product(product_id, seller_id, *, title=None, description=None,
                   price=None, category_id=None, image_url=None) -> bool:
    """只更新传入的字段，且 WHERE 带 seller_id 保证只能改自己的商品。

    刻意不允许修改 buyer_id / status / finished_at——成交状态只能经
    buy_product() 变更，避免绕过防超卖逻辑。
    """
    fields, params = [], []
    for column, value in (
        ("title", title), ("description", description), ("price", price),
        ("category_id", category_id), ("image_url", image_url),
    ):
        if value is not None:
            fields.append(f"{column} = ?")
            params.append(float(value) if column == "price"
                          else int(value) if column == "category_id"
                          else value)
    if not fields:
        return False
    params.extend([int(product_id), int(seller_id)])
    _, rowcount = _write(
        f"UPDATE products SET {', '.join(fields)} "
        "WHERE product_id = ? AND seller_id = ?",
        tuple(params),
    )
    return rowcount > 0


def delete_product(product_id, seller_id) -> bool:
    """删除自己的商品。已售商品的删除由 service 层拦截。"""
    _, rowcount = _write(
        "DELETE FROM products WHERE product_id = ? AND seller_id = ?",
        (int(product_id), int(seller_id)),
    )
    return rowcount > 0


def buy_product(product_id, buyer_id) -> str:
    """购买商品（队友 2026-11-19 新增接口，已适配统一连接工厂与事务边界）。

    防超卖依靠条件 UPDATE ... WHERE status='available' 的原子性：并发请求中
    只有一个能让 rowcount=1。返回值沿用队友的中文提示约定，便于直接复用。
    """
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT status, seller_id FROM products WHERE product_id = ?",
            (int(product_id),),
        ).fetchone()
        if row is None:
            return "错误：商品不存在"
        if row["status"] == "sold":
            return "错误：该商品已被别人抢先买走！"
        if row["seller_id"] == int(buyer_id):
            return "错误：不能购买自己发布的商品！"

        finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with conn:
            cur = conn.execute(
                "UPDATE products SET buyer_id = ?, status = 'sold', "
                "finished_at = ? WHERE product_id = ? AND status = 'available'",
                (int(buyer_id), finished_at, int(product_id)),
            )
        if cur.rowcount == 0:
            return "错误：该商品已被别人抢先买走！"
        return "购买成功！"
    finally:
        conn.close()


def get_my_purchases(buyer_id) -> list[dict]:
    """查询该买家已买到的商品（含分类名），按成交时间倒序。"""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT p.*, c.name AS category_name "
            "FROM products p JOIN categories c ON c.category_id = p.category_id "
            "WHERE p.buyer_id = ? AND p.status = 'sold' "
            "ORDER BY p.finished_at DESC, p.product_id DESC",
            (int(buyer_id),),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
