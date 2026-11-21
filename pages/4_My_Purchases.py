"""我的购买：按 buyer_id 展示已成交商品与状态（B 域，2026-11-19 新增）。

数据来自 services.product_service.get_my_purchases(user_id)，
底层是 repositories.product_repository.get_my_purchases(buyer_id)。
本页不写 SQL；件数、累计金额、最近成交等聚合在页面内用 Python 完成。
"""
from __future__ import annotations

import streamlit as st

from services import product_service as ps
from services.user_service import get_current_user, render_user_selector, user_label

render_user_selector()
st.title("我的购买")
st.caption("按买家编号查询已成交商品；购买记录绑定当前测试账号。")

user = get_current_user()
if user is None:
    st.warning("请先选择当前测试账号。")
    st.stop()

st.caption(f"当前身份：{user_label(user)}")

last_purchase_id = st.session_state.pop("last_purchase_id", None)
if last_purchase_id is not None:
    st.success(f"购买成功！商品 #{last_purchase_id} 已加入下方成交记录。")

items = ps.get_my_purchases(user["user_id"])
total_amount = sum(float(x["price"]) for x in items)
finished_times = [x["finished_at"] for x in items if x["finished_at"]]
latest = max(finished_times) if finished_times else None

c1, c2, c3 = st.columns(3)
c1.metric("已购件数", len(items))
c2.metric("累计金额", f"¥{total_amount:,.2f}")
c3.metric("最近成交", latest[:10] if latest else "—")

st.divider()
st.subheader("成交记录")

if not items:
    st.info(
        "当前账号还没有购买记录。"
        "可在「商品广场」挑一件在售商品，进入详情页点击「购买此商品」。"
    )
else:
    categories = ps.get_filter_options()["categories"]
    labels = ["全部分类"] + [c["name"] for c in categories]
    chosen = st.selectbox("按分类筛选", labels)
    shown = (
        items if chosen == "全部分类"
        else [x for x in items if x["category_name"] == chosen]
    )
    st.caption(f"共 {len(shown)} 条记录 · 按成交时间倒序")

    if not shown:
        st.info("该分类下没有购买记录。")

    for it in shown:
        with st.container(border=True):
            left, right = st.columns([4, 1])
            left.markdown(f"**{it['title']}**")
            left.caption(
                f"商品 #{it['product_id']} · {it['category_name']} · "
                f"卖家 #{it['seller_id']} · 成交时间 {it['finished_at'] or '—'}"
            )
            left.write(f"状态：**已成交**（{it['status']}）")
            right.caption("成交价")
            right.markdown(f"**¥{it['price']:,.2f}**")
            if right.button("查看详情", key=f"purchase_{it['product_id']}"):
                st.session_state.selected_product_id = it["product_id"]
                st.switch_page("pages/2_Product_Detail.py")

st.divider()
if st.button("去商品广场"):
    st.switch_page("pages/1_Marketplace.py")
