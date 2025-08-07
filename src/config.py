# src/config.py

import os

# --- Path Configuration ---
# Get the absolute path of the project's root directory
# This works by taking the path of the current file (__file__) and going up two levels (from src/config.py -> src/ -> root)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# Define all other paths relative to the project root
UPLOAD_DIR = os.path.join(PROJECT_ROOT, "data")
VECTOR_DIR = os.path.join(PROJECT_ROOT, "vectorstore")
CONFIG_FILE = os.path.join(PROJECT_ROOT, "config.json")
USERS_FILE = os.path.join(PROJECT_ROOT, "users.yaml")
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
LOGO_PATH = os.path.join(ASSETS_DIR, "logo.svg")

PAGE_TITLE="Employee Knowledge Base Chatbot"
DEFAULT_MODEL = "gemini-2.5-flash-lite"
AVAILABLE_MODELS = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.5-pro"]

DEPARTMENT_ROLES = {
    "finance": [
        "Junior Accountant",
        "AP/AR Officer",
        "Finance Analyst",
        "Finance Manager",
        "Treasury Officer"
    ],
    "marketing": [
        "Marketing Associate",
        "Digital Content Specialist",
        "Campaign Manager",
        "Marketing Lead"
    ],
    "production": [
        "Production Operator",
        "Quality Control Inspector",
        "Maintenance Technician",
        "Production Supervisor"
    ],
    "warehouse": [
        "Warehouse Operator",
        "Inventory Clerk",
        "Logistics Coordinator",
        "Warehouse Supervisor"
    ],
    "it": [
        "IT Support Specialist",
        "Junior IT Support",
    ]
}

DEPARTMENTS = list(DEPARTMENT_ROLES.keys())



