"""商品广场：多条件筛选、白名单排序与分页（B 域，P3）。"""
from __future__ import annotations

import streamlit as st

from services import product_service as ps
from services.user_service import render_user_selector

render_user_selector()
st.title("商品广场")
st.caption("所有查询经 service 组装参数、由 repository 以参数化 SQL 执行。")

options = ps.get_filter_options()
category_map = {"全部分类": None}
category_map.update(
    {c["name"]: c["category_id"] for c in options["categories"]}
)

with st.container(border=True):
    c1, c2 = st.columns([3, 2])
    keyword = c1.text_input("关键词", placeholder="按商品标题搜索")
    category_label = c2.selectbox("分类", list(category_map))
    c3, c4, c5 = st.columns([1, 1, 2])
    low = c3.text_input("最低价", placeholder="不限")
    high = c4.text_input("最高价", placeholder="不限")
    sort_label = c5.selectbox("排序方式", options["sort_labels"])

if "market_page" not in st.session_state:
    st.session_state.market_page = 1

try:
    result = ps.browse_products(
        keyword=keyword,
        category_id=category_map[category_label],
        min_price=low,
        max_price=high,
        sort_label=sort_label,
        page=st.session_state.market_page,
    )
except ps.ValidationError as exc:
    st.error(str(exc))
    st.stop()

st.caption(
    f"共 {result['total']:,} 件在售 · "
    f"第 {result['page']} / {result['pages']} 页 · 每页 {result['page_size']} 件"
)

if not result["rows"]:
    st.info("没有符合条件的商品，试试放宽筛选条件。")

for item in result["rows"]:
    with st.container(border=True):
        left, right = st.columns([4, 1])
        left.markdown(f"**{item['title']}**")
        left.caption(
            f"#{item['product_id']} · {item['category_name']} · "
            f"卖家 #{item['seller_id']} · {item['created_at']}"
        )
        if item["description"]:
            left.write(item["description"][:80])
        right.caption("价格")
        right.markdown(f"**¥{item['price']:,.2f}**")
        if right.button("查看详情", key=f"detail_{item['product_id']}"):
            st.session_state.selected_product_id = item["product_id"]
            st.switch_page("pages/2_Product_Detail.py")

st.divider()
prev_col, next_col, _ = st.columns([1, 1, 8])
if prev_col.button("上一页", disabled=result["page"] <= 1):
    st.session_state.market_page = result["page"] - 1
    st.rerun()
if next_col.button("下一页", disabled=result["page"] >= result["pages"]):
    st.session_state.market_page = result["page"] + 1
    st.rerun()
