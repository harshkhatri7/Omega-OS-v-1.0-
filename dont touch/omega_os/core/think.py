import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

def execute_think_task(question: str) -> str:
    """Sends a question to Gemini and returns the textual answer."""
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY is missing from the .env file."
        
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=question,
            config=types.GenerateContentConfig(
                temperature=0.7
            )
        )
        return response.text
    except Exception as e:
        return f"Error connecting to Gemini: {str(e)}"
