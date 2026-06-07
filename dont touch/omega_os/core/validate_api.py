import os
import sys
import urllib.request
import urllib.error
import json
from google import genai

def validate_keys():
    from dotenv import load_dotenv
    load_dotenv()
    gemini_key = os.environ.get("GEMINI_API_KEY")
    hf_key = os.environ.get("HF_API_KEY")
    
    if not gemini_key or not hf_key:
        print("[ERROR] Missing API Keys.")
        sys.exit(1)
        
    print("\n[INFO] Validating Gemini API Key...")
    try:
        client = genai.Client(api_key=gemini_key)
        # Verify connection by generating tiny content
        client.models.generate_content(
            model='gemini-2.5-flash',
            contents='test'
        )
        print("[OK] Gemini API Key is Online!")
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
            print("[WARNING] Gemini API Key is valid, but you have hit a rate limit (429). The OS will boot, but text features may be temporarily limited.")
        else:
            print(f"[ERROR] Gemini API Key is Invalid or Offline. Details: {e}")
            sys.exit(1)
        
    print("[INFO] Validating Hugging Face API Key...")
    try:
        req = urllib.request.Request("https://huggingface.co/api/whoami-v2")
        req.add_header("Authorization", f"Bearer {hf_key}")
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if "name" in data or "type" in data:
                print(f"[OK] Hugging Face API Key is Online! (Authenticated)")
            else:
                print("[ERROR] Invalid Hugging Face Token.")
                sys.exit(1)
    except urllib.error.HTTPError as e:
        print(f"[ERROR] Hugging Face API Key is Invalid. Server returned {e.code}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Hugging Face validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    validate_keys()
    sys.exit(0)
