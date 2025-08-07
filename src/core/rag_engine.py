# src/core/rag_engine.py

import os
import logging
import json
from dotenv import load_dotenv

from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.docstore.document import Document
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate

import config

# --- Initial Configuration ---
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

UPLOAD_DIR = config.UPLOAD_DIR
VECTOR_DIR = config.VECTOR_DIR

# --- Initial API Key Validation ---
if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("Error: GOOGLE_API_KEY not found in the .env file. The application cannot start.")

os.makedirs(VECTOR_DIR, exist_ok=True)

def get_current_model_from_config():
    """Reads the selected model from config.json, with a fallback default."""
    config_path = "config.json"
    default_model = "gemini-2.5-flash"
    
    if not os.path.exists(config_path):
        logging.warning(f"{config_path} not found. Using default model: {default_model}")
        return default_model
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            model = config.get("current_model", default_model)
            logging.info(f"Using configured model: {model}")
            return model
    except (json.JSONDecodeError, KeyError) as e:
        logging.error(f"Error reading {config_path}: {e}. Using default model: {default_model}")
        return default_model

def _load_docs_from_folder(folder_path):
    """
    A safe helper function to load documents from a single folder.
    """
    docs = []
    if not os.path.exists(folder_path):
        logging.warning(f"Directory not found: {folder_path}")
        return docs
        
    for filename in os.listdir(folder_path):
        filepath = os.path.join(folder_path, filename)
        if os.path.isfile(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    metadata = {"source": os.path.join(os.path.basename(folder_path), filename)}
                    docs.append(Document(page_content=content, metadata=metadata))
            except Exception as e:
                logging.error(f"Failed to read file {filepath}: {e}")
    return docs


def load_combined_documents_for_department(dept):
    """
    Loads documents from the specific department folder AND the 'general' folder.
    This implements the requested logic.
    """
    logging.info(f"Loading documents for department '{dept}' and 'general'...")
    
    dept_folder = os.path.join(UPLOAD_DIR, dept)
    general_folder = os.path.join(UPLOAD_DIR, "general")
    
    dept_docs = _load_docs_from_folder(dept_folder)
    general_docs = _load_docs_from_folder(general_folder)
    
    combined_docs = dept_docs + general_docs
    
    logging.info(f"Total documents loaded: {len(combined_docs)}")
    if not combined_docs:
        logging.warning(f"No documents were loaded for department '{dept}' or 'general'.")
        
    return combined_docs


def create_or_load_vectorstore(dept):
    """
    Creates or loads a vector store with improved error handling.
    """
    vector_path = os.path.join(VECTOR_DIR, dept)
    embedding = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

    # Try to load an existing vector store
    if os.path.exists(vector_path):
        try:
            logging.info(f"Attempting to load existing vector store from: {vector_path}")
            return FAISS.load_local(vector_path, embedding, allow_dangerous_deserialization=True)
        except Exception as e:
            logging.warning(f"Failed to load vector store from local. Error: {e}. It will be recreated.")
    
    # If it doesn't exist or failed to load, create a new one
    logging.info("Creating a new vector store...")
    docs = load_combined_documents_for_department(dept)
    if not docs:
        # This will be handled in the get_answer_from_rag function
        return None 

    try:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        splitted_docs = text_splitter.split_documents(docs)
        vectordb = FAISS.from_documents(splitted_docs, embedding)
        vectordb.save_local(vector_path)
        logging.info(f"New vector store created and saved at: {vector_path}")
        return vectordb
    except Exception as e:
        logging.error(f"Failed while creating vector store: {e}")
        return None

def get_answer_from_rag(dept, question, user_role):
    """
    Gets a context-aware answer using the modern, recommended LangChain Expression Language (LCEL) chain.
    This method correctly handles passing custom variables through the chain.
    """
    vectordb = create_or_load_vectorstore(dept)
    if not vectordb:
        return {"result": "Sorry, I couldn't find any documents for this department..."}

    retriever = vectordb.as_retriever(search_kwargs={"k": 5})
    
    selected_model = get_current_model_from_config()
    llm = ChatGoogleGenerativeAI(
        model=selected_model,
        temperature=0.2
    )

    prompt = ChatPromptTemplate.from_template(
        """
        You are a friendly and helpful onboarding assistant for the company "DummyWorX".
        Your goal is to provide accurate, personalized, and conversational answers.

        **IMPORTANT CONTEXT ABOUT THE USER ASKING THE QUESTION:**
        - User's Role: {user_role}
        - User's Department: {department}

        Use the following pieces of retrieved context from the knowledge base to answer the user's question.

        CONTEXT:
        {context}

        QUESTION:
        {input}

        INSTRUCTIONS:
        - Answer the question from the perspective of the user's specific role.
        - If the answer is in the context, provide it directly and confidently.
        - If not, politely say you don't have information on that topic for their role and suggest they contact their manager.
        - Always maintain a friendly, helpful, and professional tone.

        FRIENDLY ANSWER:
        """
    )

    # 1. Create a "stuff" chain: This chain knows how to combine the context and the question into a final prompt.
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    
    # 2. Create the full retrieval chain: This chain knows how to:
    #    a) Take a question.
    #    b) Send it to the retriever to get documents.
    #    c) Pass the documents AND the original question (and any other variables) to the question_answer_chain.
    retrieval_chain = create_retrieval_chain(retriever, question_answer_chain)

    try:
        logging.info(f"Submitting question to RAG for user role '{user_role}': '{question}'")
        
        # We pass all the necessary variables in a single dictionary.
        # The chain is smart enough to route them to the correct places.
        response = retrieval_chain.invoke({
            "input": question,
            "user_role": user_role,
            "department": dept
        })
        
        # The new chain structure returns a dictionary with different keys.
        # The final answer is in the 'answer' key. The retrieved docs are in 'context'.
        return {
            "result": response.get("answer", "Sorry, I couldn't formulate a response."),
            "source_documents": response.get("context", [])
        }
        
    except Exception as e:
        logging.error(f"An error occurred while running the RAG chain: {e}")
        return {"result": "Sorry, it seems there's a technical issue. Please try again later."}