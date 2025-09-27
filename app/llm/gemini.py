import os
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def ask_gemini(prompt: str, model: str = "gemini-1.5-flash") -> str:
    """Send a prompt to Gemini and return text output."""
    response = genai.GenerativeModel(model).generate_content(prompt)
    return response.text.strip()
