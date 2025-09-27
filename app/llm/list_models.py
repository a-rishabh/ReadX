import os
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
# genai.configure(api_key="API KEY_HERE")


for model in genai.list_models():
    # Each model object has useful metadata
    print(f"- {model.name} | Supported methods: {model.supported_generation_methods}")
