import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

class AppConfig:
    # ------------------------------------------------------------
    # HYBRID KEY LOADING
    # 1. Try loading from local .env (os.getenv)
    # 2. If not found, try loading from Streamlit Cloud (st.secrets)
    # ------------------------------------------------------------
    
    _key = os.getenv("GEMINI_API_KEY")
    
    # Check if we are on Streamlit Cloud and the key was missing locally
    if not _key:
        try:
            # st.secrets behaves like a dictionary
            if "GEMINI_API_KEY" in st.secrets:
                _key = st.secrets["GEMINI_API_KEY"]
        except (FileNotFoundError, KeyError):
            pass

    GEMINI_API_KEY: str = _key or ""
    
    # 2. Constraints
    MAX_FREE_MESSAGES: int = 3
    MAX_OUTPUT_TOKENS: int = 1000
    DOC_FETCH_LIMIT: int = 50
    MODEL_NAME: str = "gemini-2.5-flash"
    
    PAGE_TITLE: str = "MongoChat"
    PAGE_ICON: str = "🍃"

    @staticmethod
    def validate_keys():
        if not AppConfig.GEMINI_API_KEY:
            raise ValueError("System Error: Gemini API Key not found in .env")