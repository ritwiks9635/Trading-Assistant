import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv
import os

# Load API key securely
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise EnvironmentError("Missing GEMINI_API_KEY in environment.")

# Configure client
genai.configure(api_key=api_key)

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash", 
    generation_config=genai.GenerationConfig(
        temperature=0.4,
        max_output_tokens=1024,
        top_p=1.0,
        top_k=1
    ),
)