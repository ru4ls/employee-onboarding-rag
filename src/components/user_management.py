# src/components/user_management.py

import streamlit as st
import yaml
import os
import config
from auth.authenticator import load_users, hash_password

def _save_users(users_data):
    try:
        with open(config.USERS_FILE, "w") as f:
            yaml.dump(users_data, f, default_flow_style=False)
        return True
    except Exception as e:
        st.error(f"Failed to save users file: {e}")
        return False

def show_user_management():
    """Builds the complete UI for managing users."""
    st.header("👤 User Management")

    users = load_users()
    
    # --- Display Current Users ---
    st.subheader("Existing Users")
    if not users:
        st.info("No users found in users.yaml.")
    else:
        current_admin_username = st.session_state.get("username_key", "") 
        for username, details in users.items():
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            with col1:
                st.write(f"**{details.get('name', username)}** (`{username}`)")
            with col2:
                st.write(f"Role: `{details.get('role', 'N/A')}`")
            with col3:
                st.write(f"Department: `{details.get('department', 'N/A')}`")
            with col4:
                if username != current_admin_username and details.get('role') != 'admin':
                    if st.button("🗑️ Delete", key=f"delete_{username}", help=f"Delete user {username}"):
                        del users[username]
                        if _save_users(users):
                            st.success(f"User '{username}' deleted.")
                            st.rerun()

    st.markdown("---")

    # --- Add New User Form ---
    with st.expander("➕ Add a New User", expanded=False):
        st.subheader("Step 1: Select Department to See Available Roles")

        department_options = config.DEPARTMENTS
        
        selected_dept = st.selectbox(
            "Department",
            options=department_options,
            key="department_selector"
        )

        st.subheader("Step 2: Fill in New User Details")
        
        with st.form("new_user_form", clear_on_submit=True):
            
            available_roles = config.DEPARTMENT_ROLES.get(selected_dept, [])
            role_options = ["admin"] + available_roles

            new_username = st.text_input("Username (must be unique)")
            new_name = st.text_input("Full Name")
            new_password = st.text_input("Password", type="password")
            
            new_role = st.selectbox(
                "Role",
                options=role_options
            )

            submitted = st.form_submit_button("Create User")
            if submitted:
                if not new_username or not new_password:
                    st.warning("Username and password are required.")
                elif new_username in users:
                    st.error("This username already exists.")
                else:
                    # If the role is 'admin', the department is conventionally 'it'
                    # Otherwise, use the department selected outside the form.
                    final_department = 'it' if new_role == 'admin' else selected_dept
                    
                    users[new_username] = {
                        "name": new_name,
                        "password": hash_password(new_password),
                        "role": new_role,
                        "department": final_department
                    }
                    if _save_users(users):
                        st.success(f"User '{new_username}' created successfully!")
                        # We don't need to rerun here, the form clear_on_submit handles it