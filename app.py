"""CampusMarket 主入口（B 域）。

启动方式（在工程根目录）：streamlit run app.py
侧边栏切换当前测试账号；业务页面位于 pages/。
"""
from __future__ import annotations

import streamlit as st

from services import product_service as ps
from services.user_service import (
    get_available_users,
    render_user_selector,
    user_label,
)

st.set_page_config(page_title="CampusMarket", layout="wide")

user = render_user_selector()
st.sidebar.divider()
st.sidebar.caption("Track 1 · Database Application Development")

st.title("CampusMarket")
st.subheader("校园二手交易平台")
st.write(
    "面向在校学生的二手物品交易平台：浏览、筛选、发布与购买闲置物品。"
    "本期聚焦关系数据库设计与查询，登录以固定测试账号模拟，"
    "图片上传与可视化不在范围内。"
)

if user:
    st.success(f"当前身份：{user_label(user)}（固定测试账号）")
else:
    st.warning("未找到测试账号，请检查 database/campus_market.db 是否完整。")

options = ps.get_filter_options()
overview = ps.browse_products(page=1)
c1, c2, c3 = st.columns(3)
c1.metric("在售商品", f"{overview['total']:,}")
c2.metric("商品分类", len(options["categories"]))
c3.metric("可切换账号", len(get_available_users()))

st.divider()
st.subheader("功能导航")
st.page_link("pages/1_Marketplace.py", label="商品广场：筛选、排序与分页")
st.page_link("pages/2_Product_Detail.py", label="商品详情与购买")
st.page_link("pages/3_Sell_MyProducts.py", label="发布与管理我发布的商品")
st.page_link("pages/4_My_Purchases.py", label="我的购买：成交记录与状态")
st.caption(
    "「发布与管理」按 seller_id 查我发布的商品；"
    "「我的购买」按 buyer_id 查我买到的商品，两者是不同的数据线。"
)
