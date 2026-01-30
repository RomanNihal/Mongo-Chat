import google.generativeai as genai
from google.generativeai.generative_models import GenerativeModel
from google.generativeai import types
from src.config import AppConfig

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

    def generate_response(self, context_data: str, user_question: str) -> str:
        """
        Constructs the prompt and gets the response.
        """
        system_instruction = (
            f"You are a database assistant. Here is the JSON data from the user's MongoDB:\n"
            f"```json\n{context_data}\n```\n"
            f"Answer the user's question based ONLY on this data. Generate the response like an assistant, sound friendly, and keep it concise"
        )
        
        full_prompt = f"{system_instruction}\n\nUser Question: {user_question}"
        
        try:
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            return f"AI Generation Error: {str(e)}"