"""发布商品与管理自己发布的商品（B 域，P3）。"""
from __future__ import annotations

import streamlit as st

from services import product_service as ps
from services.user_service import get_current_user, render_user_selector, user_label

render_user_selector()
user = get_current_user()
st.title("发布与管理商品")

if user is None:
    st.warning("请先选择当前测试账号。")
    st.stop()

st.caption(f"当前身份：{user_label(user)} · 本期不实现注册与密码校验。")
category_map = {
    c["name"]: c["category_id"] for c in ps.get_filter_options()["categories"]
}

st.subheader("发布新商品")
with st.form("publish_form", clear_on_submit=True):
    title = st.text_input("标题 *", max_chars=100)
    category_label = st.selectbox("分类 *", list(category_map))
    price = st.text_input("价格 *", placeholder="例如 88.5")
    description = st.text_area("描述", max_chars=2000)
    submitted = st.form_submit_button("发布")
    if submitted:
        try:
            new_id = ps.publish_product(
                user_id=user["user_id"],
                title=title,
                category_id=category_map[category_label],
                price=price,
                description=description,
            )
            st.success(f"发布成功，商品 #{new_id}")
        except ps.ValidationError as exc:
            st.error(str(exc))

st.divider()
items = ps.get_my_products(user["user_id"])
st.subheader(f"我的商品（共 {len(items)} 件）")
if len(items) > 50:
    st.caption("仅展示最近 50 件，避免页面过长。")

for item in items[:50]:
    headline = (
        f"#{item['product_id']} {item['title']} | "
        f"¥{item['price']:,.2f} | {item['status']}"
    )
    with st.expander(headline):
        with st.form(f"edit_{item['product_id']}"):
            new_title = st.text_input("标题", value=item["title"], max_chars=100)
            new_price = st.text_input("价格", value=str(item["price"]))
            new_desc = st.text_area(
                "描述", value=item["description"] or "", max_chars=2000
            )
            if st.form_submit_button("保存修改"):
                try:
                    changed = ps.edit_product(
                        product_id=item["product_id"],
                        user_id=user["user_id"],
                        title=new_title,
                        price=new_price,
                        description=new_desc,
                    )
                    if changed:
                        st.success("已更新")
                        st.rerun()
                    else:
                        st.info("没有需要更新的字段")
                except ps.ValidationError as exc:
                    st.error(str(exc))

        if item["status"] == "sold":
            st.caption("已售出的商品保留成交记录，不能删除。")
        elif st.button("删除该商品", key=f"delete_{item['product_id']}"):
            try:
                if ps.remove_product(
                    product_id=item["product_id"], user_id=user["user_id"]
                ):
                    st.success("已删除")
                    st.rerun()
                else:
                    st.error("删除失败：只能删除自己发布的商品。")
            except ps.ValidationError as exc:
                st.error(f"删除失败：{exc}")
