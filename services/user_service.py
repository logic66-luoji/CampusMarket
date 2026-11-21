"""当前用户上下文（B 域，P2）。

本期不做注册与密码校验（范围裁剪见报告 §7）：用固定测试账号下拉切换模拟身份，
与库中已有的 sha256 口令哈希数据保持一致，不引入 bcrypt。

设计约束：本模块不写 SQL；Streamlit 采用延迟导入，使业务逻辑可在命令行自测。
"""
from __future__ import annotations

from repositories.user_repository import get_user_by_id, list_test_users

SESSION_KEY = "current_user_id"
_FALLBACK_STATE: dict = {}


def _state() -> dict:
    """取会话状态；无 Streamlit 运行上下文时退回模块级字典，便于自测。"""
    try:
        import streamlit as st

        return st.session_state
    except Exception:
        return _FALLBACK_STATE


def get_available_users() -> list[dict]:
    """返回可切换的测试账号列表（不含口令哈希）。"""
    return list_test_users()


def get_current_user() -> dict | None:
    """取当前用户；首次访问默认选第一个测试账号。"""
    state = _state()
    user_id = state.get(SESSION_KEY)
    if user_id is None:
        users = get_available_users()
        if not users:
            return None
        user_id = users[0]["user_id"]
        state[SESSION_KEY] = user_id
    return get_user_by_id(user_id)


def set_current_user(user_id) -> dict | None:
    """切换当前用户；用户不存在时返回 None 且不改变会话。"""
    user = get_user_by_id(user_id)
    if user is None:
        return None
    _state()[SESSION_KEY] = int(user_id)
    return user


def user_label(user: dict) -> str:
    return f"#{user['user_id']} {user['username']}"


def render_user_selector() -> dict | None:
    """在侧边栏渲染账号切换下拉框，返回切换后的当前用户。"""
    import streamlit as st

    users = get_available_users()
    if not users:
        st.sidebar.warning("数据库中没有可用的测试账号。")
        return None

    id_to_user = {u["user_id"]: u for u in users}
    current = get_current_user()
    default_id = current["user_id"] if current else users[0]["user_id"]

    chosen = st.sidebar.selectbox(
        "当前测试账号",
        options=list(id_to_user),
        index=list(id_to_user).index(default_id),
        format_func=lambda uid: user_label(id_to_user[uid]),
        help="本期以固定测试账号模拟登录，不实现注册与密码校验。",
    )
    return set_current_user(chosen)
