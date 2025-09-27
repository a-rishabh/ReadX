import os
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")

def ask_gemini(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """Send a prompt to Gemini and return text output."""
    response = genai.GenerativeModel(model).generate_content(prompt)
    return response.text.strip()
