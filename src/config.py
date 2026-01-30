import os
from dotenv import load_dotenv

load_dotenv()

class AppConfig:
    # 1. Load YOUR Gemini Key
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY") or ""
    
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