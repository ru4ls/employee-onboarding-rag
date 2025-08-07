# src/auth/authenticator.py

import os
import streamlit as st
import yaml
import hashlib
import config

# Use the absolute path for the users file from the central config.
USER_FILE = config.USERS_FILE

# --- Core Functions ---

def load_users():
    """Safely loads user data from the YAML file."""
    if not os.path.exists(USER_FILE):
        st.error(f"⚠️ {os.path.basename(USER_FILE)} file not found.")
        return {}
    try:
        # Use yaml.safe_load for security.
        with open(USER_FILE, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        st.error(f"⚠️ Error reading {os.path.basename(USER_FILE)}: {e}")
        return {}

def hash_password(password):
    """Hashes a password using SHA256 for secure storage."""
    return hashlib.sha256(password.encode()).hexdigest()

# --- Streamlit UI and Session Management ---

def login_form():
    """Renders the login form UI and handles authentication."""
    col1, col2, col3 = st.columns([1, 2, 1]) 
    with col2:
        # Display the logo from the configured path.
        if os.path.exists(config.LOGO_PATH):
            st.image(config.LOGO_PATH, width=500)
        
    st.info("Welcome to the Employee Knowledge Base Chatbot. Please log in.")
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        # Load the latest user data ON CLICK to see newly created users immediately.
        users = load_users()
        
        if username in users:
            # Hash the entered password and compare it to the stored hash.
            hashed_pw = hash_password(password)
            if users[username].get("password") == hashed_pw:
                # --- Set Session State on Success ---
                st.session_state.authenticated = True
                st.session_state.username = users[username].get("name", username)
                st.session_state.username_key = username # Unique key for internal use
                st.session_state.role = users[username].get("role", "user")
                st.session_state.department = users[username].get("department", "general")
                
                st.success("✅ Login successful")
                st.rerun() # Rerun to show the main app.
            else:
                st.error("❌ Invalid username or password")
        else:
            st.error("❌ Invalid username or password")

def get_user_role():
    """Helper to safely get the user's role from the session state."""
    return st.session_state.get("role", "user")

def get_user_department():
    """Helper to safely get the user's department from the session state."""
    return st.session_state.get("department", "general")

def check_authentication():
    """
    Main auth check called by main.py.
    Shows login form and stops execution if the user is not authenticated.
    """
    if not st.session_state.get("authenticated", False):
        login_form()
        st.stop() # Prevents the rest of the app from rendering.

def logout():
    """
    Clears all session state keys to log the user out.
    Used as a button callback.
    """
    keys_to_delete = ["authenticated", "username", "username_key", "role", "department", "messages"]
    for key in keys_to_delete:
        if key in st.session_state:
            del st.session_state[key]