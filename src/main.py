# src/main.py

import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo

import config

from auth.authenticator import check_authentication, get_user_role, logout
from components.admin_panel import show_admin_panel
from components.chat_ui import show_chat_ui

TARGET_TIMEZONE = ZoneInfo("Asia/Jakarta")

# --- App Config ---
st.set_page_config(config.PAGE_TITLE)

# --- Login Phase ---
# This function handles displaying the login form and stopping execution if not logged in.
check_authentication()

# --- Everything below this line only runs after a successful login ---

# --- Role and Session Setup ---
if "role" not in st.session_state:
    st.session_state.role = get_user_role()
if "username" not in st.session_state:
    st.session_state.username = "User"
if "department" not in st.session_state:
    st.session_state.department = "general"

# --- Sidebar (The App's "Frame") ---
with st.sidebar:
    st.image(config.LOGO_PATH, width=200)
    st.title(f"Hello, {st.session_state.username}!")
    st.markdown(f"**Role:** {st.session_state.role.title()}")
    st.markdown(f"**Department:** {st.session_state.department.title()}")
    st.button("Logout", on_click=logout)

# --- Main Panel Router ---
if st.session_state.role == "admin":
    st.title("Admin Panel")
    show_admin_panel()
else:
    show_chat_ui(TARGET_TIMEZONE)