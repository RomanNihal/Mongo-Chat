import streamlit as st
from src.config import AppConfig

def init_session_state():
    """Initializes all session state variables if they don't exist."""
    defaults = {
        "message_count": 0,
        "chat_history": [],
        "mongo_data": None,
        "db_connected": False,
        "mongo_service": None # We can store the instance if we want persistence
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def check_usage_limit() -> bool:
    """Returns True if user has reached the limit."""
    return st.session_state.message_count >= AppConfig.MAX_FREE_MESSAGES

def increment_message_count():
    st.session_state.message_count += 1