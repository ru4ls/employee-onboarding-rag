# src/components/admin_panel.py

import os
import shutil
import json
import streamlit as st
import yaml
import config
from auth.authenticator import load_users, hash_password

# --- Core Helper Functions ---

def _get_available_departments():
    """
    Scans the data directory and returns a list of all valid department folder names.
    This ensures the UI always reflects the current folder structure.
    """
    if not os.path.exists(config.UPLOAD_DIR):
        return []
    # List comprehension to get all items in UPLOAD_DIR that are directories
    return [d for d in os.listdir(config.UPLOAD_DIR) if os.path.isdir(os.path.join(config.UPLOAD_DIR, d))]

def _save_users(users_data):
    """
    Helper function to safely write the provided user dictionary to the users.yaml file.
    
    Args:
        users_data (dict): The complete dictionary of users to save.
    
    Returns:
        bool: True if save was successful, False otherwise.
    """
    try:
        with open(config.USERS_FILE, "w") as f:
            yaml.dump(users_data, f, default_flow_style=False)
        return True
    except Exception as e:
        st.error(f"Failed to save users file: {e}")
        return False

# --- UI Builder for Tab 1: AI Model Configuration ---

def _build_model_selector():
    """
    Renders the Streamlit UI components for selecting and saving the AI model.
    The choice is saved to the central config.json file.
    """
    # Load model choices and default from the central config file for consistency
    available_models = config.AVAILABLE_MODELS
    default_model = config.DEFAULT_MODEL
    
    # Try to load the currently saved model from config.json
    try:
        with open(config.CONFIG_FILE, 'r') as f:
            cfg = json.load(f)
        current_model = cfg.get("current_model", default_model)
    except (FileNotFoundError, json.JSONDecodeError):
        # If the file doesn't exist or is invalid, use the default
        current_model = default_model

    # Set the default index for the selectbox based on the loaded configuration
    current_index = available_models.index(current_model) if current_model in available_models else 0

    selected_model = st.selectbox(
        "Select the Gemini model for the chatbot:",
        options=available_models,
        index=current_index,
        help="Flash is faster and cheaper. Pro is more powerful."
    )

    # Handle the save action
    if st.button("💾 Save Model Choice"):
        try:
            with open(config.CONFIG_FILE, 'w') as f:
                json.dump({"current_model": selected_model}, f, indent=2)
            st.success(f"Model successfully set to: **{selected_model}**")
        except Exception as e:
            st.error(f"Failed to save configuration: {e}")

# --- UI Builder for Tab 2: User Management ---

def _build_user_manager():
    """
    Renders the complete UI for listing, deleting, and adding new users.
    """
    # Load the most recent user data at the beginning of the render
    users = load_users()
    
    st.subheader("Existing Users")
    if not users:
        st.info("No users found in users.yaml.")
    else:
        # Get the current admin's username key to prevent them from deleting themselves
        current_admin_username = st.session_state.get("username_key", "")
        
        # Iterate over a copy of the dictionary to allow for safe deletion during the loop
        for username, details in users.copy().items():
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            with col1:
                st.write(f"**{details.get('name', username)}** (`{username}`)")
            with col2:
                st.write(f"Role: `{details.get('role', 'N/A')}`")
            with col3:
                st.write(f"Department: `{details.get('department', 'N/A')}`")
            with col4:
                # Add safety checks: cannot delete the currently logged-in admin or any user with the 'admin' role
                if username != current_admin_username and details.get('role') != 'admin':
                    if st.button("🗑️ Delete", key=f"delete_{username}", help=f"Delete user {username}"):
                        del users[username]
                        if _save_users(users):
                            st.success(f"User '{username}' deleted.")
                            st.rerun()

    st.markdown("---")
    
    # User creation form, wrapped in an expander
    with st.expander("➕ Add a New User", expanded=True):
        is_admin_user = st.toggle("Create as Administrator", key="is_admin_toggle")
        
        # Conditional UI: Show different forms for admin vs. departmental users
        if is_admin_user:
            # --- Admin User Creation Form ---
            st.info("Administrators will be assigned to the 'it' department.")
            with st.form("new_admin_form", clear_on_submit=True):
                st.subheader("New Admin User Details")
                new_username = st.text_input("Username (must be unique)")
                new_name = st.text_input("Full Name")
                new_password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Create Admin User")
                if submitted:
                    # Load a fresh copy of users to perform the most up-to-date validation
                    current_users = load_users()
                    if not new_username or not new_password:
                        st.warning("Username and password are required.")
                    elif new_username in current_users:
                        st.error("This username already exists.")
                    else:
                        current_users[new_username] = {"name": new_name, "password": hash_password(new_password), "role": "admin", "department": "it"}
                        if _save_users(current_users):
                            st.success(f"Admin user '{new_username}' created successfully!")
                            st.rerun()
        else:
            # --- Departmental User Creation Form ---
            st.subheader("Step 1: Select Department")
            # Department selector is outside the form to allow dynamic role updates
            selected_dept = st.selectbox("Department", options=config.DEPARTMENTS, key="department_selector")
            # Get the roles for the currently selected department
            available_roles = config.DEPARTMENT_ROLES.get(selected_dept, [])
            
            st.subheader("Step 2: Fill in Details")
            with st.form("new_dept_user_form", clear_on_submit=True):
                new_username = st.text_input("Username (must be unique)")
                new_name = st.text_input("Full Name")
                new_password = st.text_input("Password", type="password")
                
                # The role selector's options are now dynamically populated
                if not available_roles:
                    new_role = st.text_input("Role", disabled=True, value="No roles defined for this department.")
                else:
                    new_role = st.selectbox("Role", options=available_roles)
                    
                submitted = st.form_submit_button("Create Department User")
                if submitted:
                    current_users = load_users()
                    if not new_username or not new_password:
                        st.warning("Username and password are required.")
                    elif new_username in current_users:
                        st.error("This username already exists.")
                    else:
                        current_users[new_username] = {"name": new_name, "password": hash_password(new_password), "role": new_role, "department": selected_dept}
                        if _save_users(current_users):
                            st.success(f"User '{new_username}' created successfully!")
                            st.rerun()

# --- UI Builder for Tab 3: Document Management ---

def _build_document_manager(departments):
    """
    Renders the UI for managing knowledge base documents for each department.
    Includes listing, editing, deleting, uploading, and re-indexing.
    """
    st.info("After uploading, editing, or deleting a file, you must click **'Update Knowledge Base'** for the chatbot to see the changes.")
    
    for dept in departments:
        with st.expander(f"📂 Manage Documents for: **{dept.title()}**"):
            folder_path = os.path.join(config.UPLOAD_DIR, dept)
            os.makedirs(folder_path, exist_ok=True)

            files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
            if not files:
                st.write("No documents found in this department.")
            
            # Loop through each file to create its management widgets
            for f in files:
                file_path = os.path.join(folder_path, f)
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"- {f}")
                with col2:
                    # Delete button for the file
                    if st.button("🗑️", key=f"delete_{dept}_{f}", help=f"Delete {f}"):
                        os.remove(file_path)
                        st.rerun()
                # Expander to view and edit file content
                with st.expander("📄 View / Edit"):
                    with open(file_path, "r", encoding="utf-8") as file:
                        content = file.read()
                    updated_content = st.text_area("Edit content:", value=content, key=f"edit_{dept}_{f}", height=200)
                    if st.button("💾 Save Changes", key=f"save_{dept}_{f}"):
                        with open(file_path, "w", encoding="utf-8") as file:
                            file.write(updated_content)
                        st.success(f"Updated {f}")
                        st.rerun()

            st.markdown("---")
            # File uploader widget for the department
            st.markdown("#### 📤 Upload New File")
            uploaded_file = st.file_uploader(f"Upload a .txt file for {dept}", type="txt", key=f"upload_{dept}")
            if uploaded_file:
                with open(os.path.join(folder_path, uploaded_file.name), "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"Uploaded: {uploaded_file.name}")
                st.rerun()

            st.markdown("---")
            # Button to trigger the re-indexing process
            st.markdown("#### ✨ Update AI Knowledge Base")
            if st.button("🔄 Update Knowledge Base", key=f"reindex_{dept}"):
                _handle_reindexing(dept)

def _handle_reindexing(dept):
    """
    Handles the clearing of vector stores to allow the RAG engine to re-index.
    This is the core logic for the "Update Knowledge Base" button.
    """
    # Determine which path to clear based on whether it's a 'general' update or a specific department
    if dept == "general":
        path_to_clear = config.VECTOR_DIR
        spinner_message = "Clearing all department knowledge bases..."
        success_message = "All department knowledge bases have been cleared. They will be rebuilt as needed."
    else:
        path_to_clear = os.path.join(config.VECTOR_DIR, dept)
        spinner_message = f"Updating knowledge base for {dept}..."
        success_message = f"Knowledge base for {dept} has been updated."

    with st.spinner(spinner_message):
        if not os.path.exists(path_to_clear):
            st.info(f"Knowledge base for '{dept}' does not exist yet. It will be built on the next query.")
            return

        # Safely remove all files and subdirectories within the target path
        for root, dirs, files in os.walk(path_to_clear, topdown=False):
            for name in files:
                try:
                    os.remove(os.path.join(root, name))
                except OSError as e:
                    st.error(f"Error removing file {name}: {e}")
            for name in dirs:
                try:
                    shutil.rmtree(os.path.join(root, name))
                except OSError as e:
                    st.error(f"Error removing subdirectory {name}: {e}")
    
    st.success(success_message)
        
# --- Main Function ---

def show_admin_panel():
    """
    The main entry point for the admin page. It renders the tabbed interface
    and calls the appropriate UI builder function for each tab.
    """
    # Create the tab layout
    tab1, tab2, tab3 = st.tabs(["🤖 AI Model Configuration", "👤 User Management", "🗂️ Document Management"])

    # Render content for each tab
    with tab1:
        _build_model_selector()
    with tab2:
        _build_user_manager()
    with tab3:
        departments = _get_available_departments()
        if departments:
            _build_document_manager(departments)
        else:
            st.warning("No department folders found in the 'data' directory. Please create a folder for each department.")