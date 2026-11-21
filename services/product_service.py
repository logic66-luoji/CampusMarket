"""商品业务逻辑（B 域，P2）。

只负责参数校验、筛选条件组装与结果包装；所有数据读写委托 repositories。
页面与 services 均不得出现 SQL 或直接建立数据库连接。
"""
from __future__ import annotations

import math

from repositories import product_repository as repo
from repositories.category_repository import get_categories

SORT_OPTIONS = {
    "最新发布": "newest",
    "最早发布": "oldest",
    "价格从低到高": "price_asc",
    "价格从高到低": "price_desc",
}
DEFAULT_SORT_LABEL = "最新发布"
PAGE_SIZE = 20
MAX_TITLE_LEN = 100
MAX_DESCRIPTION_LEN = 2000
MAX_PRICE = 1_000_000.0


class ValidationError(ValueError):
    """表单或筛选参数不合法。"""


def get_filter_options() -> dict:
    """提供给页面的下拉选项：分类与排序方式。"""
    return {
        "categories": get_categories(),
        "sort_labels": list(SORT_OPTIONS),
    }


def _parse_price(value, field: str, *, allow_blank=True):
    if value is None or (isinstance(value, str) and not value.strip()):
        if allow_blank:
            return None
        raise ValidationError(f"{field}不能为空")
    try:
        price = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field}必须是数字") from None
    if price < 0 or price > MAX_PRICE:
        raise ValidationError(f"{field}需在 0 到 {MAX_PRICE:,.0f} 之间")
    return price


def build_search_params(*, keyword="", category_id=None, min_price=None,
                        max_price=None, sort_label=DEFAULT_SORT_LABEL,
                        page=1) -> dict:
    """校验并组装筛选参数，可直接传给 repo.search_products / count_products。"""
    low = _parse_price(min_price, "最低价")
    high = _parse_price(max_price, "最高价")
    if low is not None and high is not None and low > high:
        raise ValidationError("最低价不能高于最高价")

    keyword = (keyword or "").strip()
    if len(keyword) > 50:
        raise ValidationError("关键词过长（最多 50 字）")

    if sort_label not in SORT_OPTIONS:
        sort_label = DEFAULT_SORT_LABEL

    try:
        page = max(1, int(page))
    except (TypeError, ValueError):
        page = 1

    return {
        "keyword": keyword,
        "category_id": category_id or None,
        "min_price": low,
        "max_price": high,
        "sort": SORT_OPTIONS[sort_label],
        "page": page,
        "page_size": PAGE_SIZE,
    }


def browse_products(**kwargs) -> dict:
    """一次返回当前页数据、总条数与分页信息，供列表页直接渲染。"""
    params = build_search_params(**kwargs)
    total = repo.count_products(
        keyword=params["keyword"], category_id=params["category_id"],
        min_price=params["min_price"], max_price=params["max_price"],
    )
    rows = repo.search_products(**params)
    pages = max(1, math.ceil(total / params["page_size"]))
    page = min(params["page"], pages)
    if page != params["page"]:
        params["page"] = page
        rows = repo.search_products(**params)
    return {
        "rows": rows,
        "total": total,
        "page": page,
        "pages": pages,
        "page_size": params["page_size"],
        "sort": params["sort"],
    }


def _validate_product_form(title, category_id, price, description=""):
    title = (title or "").strip()
    if not title:
        raise ValidationError("商品标题不能为空")
    if len(title) > MAX_TITLE_LEN:
        raise ValidationError(f"商品标题最多 {MAX_TITLE_LEN} 字")
    description = (description or "").strip()
    if len(description) > MAX_DESCRIPTION_LEN:
        raise ValidationError(f"描述最多 {MAX_DESCRIPTION_LEN} 字")

    valid_ids = {c["category_id"] for c in get_categories()}
    try:
        category_id = int(category_id)
    except (TypeError, ValueError):
        raise ValidationError("请选择有效的分类") from None
    if category_id not in valid_ids:
        raise ValidationError("请选择有效的分类")

    price_value = _parse_price(price, "价格", allow_blank=False)
    if price_value is None or price_value <= 0:
        raise ValidationError("价格必须大于 0")
    return title, description, category_id, price_value


def publish_product(*, user_id, title, category_id, price,
                    description="", image_url=None) -> int:
    """发布商品，返回新 product_id。"""
    if user_id is None:
        raise ValidationError("请先选择当前测试账号")
    title, description, category_id, price_value = _validate_product_form(
        title, category_id, price, description
    )
    return repo.create_product(
        seller_id=user_id, category_id=category_id, title=title,
        description=description, price=price_value, image_url=image_url,
    )


def edit_product(*, product_id, user_id, title=None, description=None,
                 price=None, category_id=None) -> bool:
    """编辑自己的商品；价格与分类若传入则重新校验。"""
    updates: dict = {}
    if title is not None:
        updates["title"] = (title or "").strip()
        if not updates["title"] or len(updates["title"]) > MAX_TITLE_LEN:
            raise ValidationError("商品标题不能为空且最多 100 字")
    if description is not None:
        updates["description"] = description.strip()
        if len(updates["description"]) > MAX_DESCRIPTION_LEN:
            raise ValidationError(f"描述最多 {MAX_DESCRIPTION_LEN} 字")
    if price is not None:
        value = _parse_price(price, "价格", allow_blank=False)
        if value is None or value <= 0:
            raise ValidationError("价格必须大于 0")
        updates["price"] = value
    if category_id is not None:
        valid_ids = {c["category_id"] for c in get_categories()}
        if int(category_id) not in valid_ids:
            raise ValidationError("请选择有效的分类")
        updates["category_id"] = int(category_id)
    if not updates:
        return False
    return repo.update_product(product_id, user_id, **updates)


def remove_product(*, product_id, user_id) -> bool:
    """删除自己的商品；已售商品禁止删除，避免抹掉成交记录。"""
    item = repo.get_product_detail(product_id)
    if item is None:
        return False
    if item["status"] == "sold":
        raise ValidationError("已售出的商品不能删除（成交记录需保留）")
    return repo.delete_product(product_id, user_id)


def buy_product(*, product_id, user_id) -> dict:
    """购买商品，返回 {"ok": bool, "message": str}。"""
    if user_id is None:
        raise ValidationError("请先选择当前测试账号")
    message = repo.buy_product(product_id, user_id)
    return {"ok": message == "购买成功！", "message": message}


def get_my_purchases(user_id) -> list[dict]:
    """当前用户已买到的商品，供后续「我的订单」页面使用。"""
    return repo.get_my_purchases(user_id)


def get_product(product_id) -> dict | None:
    """详情页与 C 的订单页共用的商品详情入口。"""
    return repo.get_product_detail(product_id)


def get_my_products(user_id) -> list[dict]:
    """当前用户发布的全部商品（含已售出与已下架）。"""
    return repo.get_user_products(user_id)
