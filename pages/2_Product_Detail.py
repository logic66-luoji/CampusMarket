"""商品详情与购买（B 域；2026-11-19 接入队友 buy_product 接口）。

数据模型：成交状态记录在 products.buyer_id / finished_at / status，
不再有独立的 orders 表。
"""
from __future__ import annotations

import streamlit as st

from services import product_service as ps
from services.user_service import get_current_user, render_user_selector

render_user_selector()
st.title("商品详情")

selected = st.session_state.get("selected_product_id")
product_id = st.number_input(
    "商品 ID", min_value=1, value=int(selected or 1), step=1,
    help="从商品广场点击「查看详情」会自动带出 ID，也可手动输入。",
)
if st.button("加载该商品"):
    st.session_state.selected_product_id = int(product_id)
    st.rerun()

item = ps.get_product(selected or product_id)
if item is None:
    st.warning("未找到该商品，请检查商品 ID。")
    st.stop()

category_names = {
    c["category_id"]: c["name"] for c in ps.get_filter_options()["categories"]
}

st.header(item["title"])
left, right = st.columns([3, 2])
left.write(f"**商品编号**：#{item['product_id']}")
left.write(f"**分类**：{category_names.get(item['category_id'], item['category_id'])}")
left.write(f"**卖家编号**：#{item['seller_id']}")
left.write(f"**发布时间**：{item['created_at']}")
left.write(f"**状态**：{item['status']}")
if item["status"] == "sold":
    left.write(f"**买家编号**：#{item['buyer_id']}")
    left.write(f"**成交时间**：{item['finished_at']}")
right.caption("价格")
right.markdown(f"**¥{item['price']:,.2f}**")

if item.get("image_url"):
    right.image(item["image_url"], width=260)
else:
    right.info("暂无图片。image_url 为预留字段，本期未启用图片上传。")

st.divider()
st.subheader("描述")
st.write(item["description"] or "卖家未填写描述。")

st.divider()
st.subheader("购买")
if item["status"] != "available":
    st.warning(
        f"该商品已售出（买家 #{item['buyer_id']}，"
        f"成交时间 {item['finished_at']}），不可购买。"
    )
else:
    st.caption(
        "购买在单个事务内完成：条件更新 buyer_id、status 与 finished_at；"
        "WHERE status='available' 的原子性保证同一商品不会被重复购买。"
    )
    if st.button("购买此商品"):
        user = get_current_user()
        try:
            result = ps.buy_product(
                product_id=item["product_id"],
                user_id=user["user_id"] if user else None,
            )
        except ps.ValidationError as exc:
            st.error(str(exc))
        else:
            if result["ok"]:
                st.session_state.last_purchase_id = item["product_id"]
                st.switch_page("pages/4_My_Purchases.py")
            else:
                st.error(result["message"])

if st.button("返回商品广场"):
    st.switch_page("pages/1_Marketplace.py")
