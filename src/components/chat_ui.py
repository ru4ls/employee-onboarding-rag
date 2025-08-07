# src/components/chat_ui.py

import streamlit as st
from datetime import datetime

# Correctly import from the new package structure
from core.rag_engine import get_answer_from_rag

def show_chat_ui(timezone):
    """
    Builds the user-facing RAG chatbot interface.
    """
    st.title(f"💬 Welcome to the {st.session_state.department.title()} Department Assistant")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": f"Hi {st.session_state.username}! I'm your AI assistant... How can I help you get started?",
            "timestamp": datetime.now(timezone)
        }]

    # Display all existing messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "timestamp" in message:
                st.caption(f"🕒 {message['timestamp'].strftime('%H:%M:%S')}")
            if "sources" in message and message["sources"]:
                with st.expander("View Sources"):
                    for source in message["sources"]:
                        st.info(source)

    # --- THIS IS THE UPDATED SAMPLE PROMPTS LOGIC ---
    clicked_prompt = None

    # Get the user's role from the session state to create a dynamic prompt
    user_role = st.session_state.get("role", "employee").title()

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("What are the company's working hours?"):
            clicked_prompt = "What are the company's working hours?"
    with col2:
        if st.button("How do I request vacation time?"):
            clicked_prompt = "How do I request vacation time?"
    with col3:
        # This is your new dynamic button, using the user's specific role
        if st.button(f"What are my responsibilities as a {user_role}?"):
            clicked_prompt = f"Regarding my role as a {user_role}, what are my key responsibilities?"

    # --- The rest of your chat logic remains exactly the same ---
    input_prompt = st.chat_input(f"Or type your question...")
    prompt_to_process = clicked_prompt or input_prompt

    if prompt_to_process:
        st.session_state.messages.append({
            "role": "user",
            "content": prompt_to_process,
            "timestamp": datetime.now(timezone)
        })
        st.rerun()

    # Generate assistant's response if the last message was from the user
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        last_user_message = st.session_state.messages[-1]["content"]
        
        with st.spinner("Searching documents and crafting a response..."):
            response_data = get_answer_from_rag(st.session_state.department, last_user_message)
            
            assistant_message = {
                "role": "assistant",
                "timestamp": datetime.now(timezone)
            }

            if isinstance(response_data, dict):
                assistant_message["content"] = response_data.get("result", "Sorry, I couldn't formulate an answer.")
                source_documents = response_data.get("source_documents", [])
                unique_source_names = []
                if source_documents:
                    for doc in source_documents:
                        source_name = doc.metadata.get('source', 'Unknown Source')
                        if source_name not in unique_source_names:
                            unique_source_names.append(source_name)
                assistant_message["sources"] = unique_source_names
            else:
                assistant_message["content"] = response_data
                assistant_message["sources"] = []

            st.session_state.messages.append(assistant_message)
            st.rerun()