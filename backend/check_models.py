import google.generativeai as genai
from dotenv import load_dotenv
import os

# Load the API key from your .env file
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

print("--- Jarvis AI Diagnostic Check ---")

if not api_key:
    print("\n[ERROR] GEMINI_API_KEY not found in .env file. Please check your setup.")
else:
    try:
        genai.configure(api_key=api_key)
        print("\n[SUCCESS] API Key configured successfully.")
        print("\nFetching available models...\n")

        # This will list every model your specific API key is allowed to use
        model_found = False
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"  > Found usable model: {m.name}")
                model_found = True

        if not model_found:
             print("[WARNING] No usable models found. This might indicate an issue with your Google Cloud project permissions.")

        print("\n--- Diagnostic Complete ---")
        print("\n[ACTION REQUIRED]:")
        print("1. Look at the list above for a model name (e.g., 'models/gemini-1.5-pro-latest').")
        print("2. Copy the model name *exactly* as it is printed.")
        print("3. Paste it into your main.py file on line 42 to replace the old model name.")


    except Exception as e:
        print(f"\n[CRITICAL ERROR] The test failed: {e}")
        print("\n[TROUBLESHOOTING]:")
        print("1. Your API Key in the .env file might be incorrect or disabled.")
        print("2. The 'Generative Language API' may not be enabled in your Google Cloud Project.")
        print("3. You might need to create a new Google Cloud Project and a new API key within it.")