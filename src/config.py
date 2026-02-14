import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

class AppConfig:
    # --- SECRETS (Force String Type) ---
    # We use 'or ""' to ensure it's never None, solving the Pylance error
    MASTER_MONGO_URI: str = os.getenv("MASTER_MONGO_URI") or st.secrets.get("MASTER_MONGO_URI") or ""
    
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET") or st.secrets.get("JWT_SECRET") or "unsafe_default"
    
    # Fernet requires bytes or string. We ensure it's a string here.
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY") or st.secrets.get("ENCRYPTION_KEY") or ""
    
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY") or ""
    
    # --- CONSTANTS ---
    # These must be declared as static class variables
    MAX_FREE_MESSAGES: int = 3
    MAX_OUTPUT_TOKENS: int = 1000
    DOC_FETCH_LIMIT: int = 50
    MODEL_NAME: str = "gemini-2.5-flash"
    
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    PAGE_TITLE: str = "MongoChat Platform"
    PAGE_ICON: str = "🍃"

    @staticmethod
    def validate_secrets():
        """Runtime check to ensure keys are valid"""
        if not AppConfig.MASTER_MONGO_URI:
            raise ValueError("Configuration Error: MASTER_MONGO_URI is missing.")
        if not AppConfig.ENCRYPTION_KEY:
            raise ValueError("Configuration Error: ENCRYPTION_KEY is missing.")
        if not AppConfig.GEMINI_API_KEY:
            raise ValueError("Configuration Error: GEMINI_API_KEY is missing.")