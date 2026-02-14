import time
import google.generativeai as genai
from google.generativeai.generative_models import GenerativeModel
from google.generativeai import types
from src.config import AppConfig
from src.utils.rate_limiter import get_rate_limiter # <--- New Import

class GeminiService:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API Key is required.")
        
        genai.configure(api_key=api_key) # type: ignore
        
        self.generation_config = types.GenerationConfig(
            max_output_tokens=AppConfig.MAX_OUTPUT_TOKENS
        )
        
        self.model = GenerativeModel(
            AppConfig.MODEL_NAME, 
            generation_config=self.generation_config
        )
        
        # Get the global shared limiter
        self.limiter = get_rate_limiter()

    def generate_response(self, context_data: str, user_question: str) -> str:
        """
        Constructs the prompt and gets the response.
        """
        # --- 1. PRE-CHECK: Ask Rate Limiter for permission ---
        status = self.limiter.check_limits()
        
        if status == "DAILY_LIMIT":
            return "🚫 **System Daily Limit Reached.** The global quota for this app is full. Please try again tomorrow (UTC)."
        
        if status == "RPM_LIMIT":
            # If busy, wait 5 seconds and try one last time
            time.sleep(5) 
            if self.limiter.check_limits() == "RPM_LIMIT":
                 return "⏳ **Traffic High.** Too many people are using the AI right now. Please wait 10 seconds."

        # --- 2. Construct Prompt ---
        system_instruction = (
            f"You are a database assistant. Here is the JSON data from the user's MongoDB:\n"
            f"```json\n{context_data}\n```\n"
            f"Answer the user's question based ONLY on this data. Generate the response like an assistant, sound friendly, and keep it concise"
        )
        
        full_prompt = f"{system_instruction}\n\nUser Question: {user_question}"
        
        try:
            # --- 3. Call API ---
            response = self.model.generate_content(full_prompt)
            
            # --- 4. POST-ACTION: Record successful request ---
            self.limiter.record_request()
            
            return response.text
            
        except Exception as e:
            # Handle standard API overload error
            if "429" in str(e):
                 return "🚫 **API Limit Hit:** Rate limit exceeded. Please wait a moment."
            return f"AI Generation Error: {str(e)}"