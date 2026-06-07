import os
import io
import tempfile
import urllib.request
from dotenv import load_dotenv
from PIL import Image
class CreatorAgent:
    def __init__(self):
        self.current_image_bytes = None
        self.last_prompt = ""

    def reset(self):
        """Clears the current session context."""
        self.current_image_bytes = None
        self.last_prompt = ""

    def send_prompt(self, prompt: str, is_modification: bool = False) -> str:
        """
        Sends a prompt to generate an image using Pollinations AI, and returns the ANSI representation.
        """
        try:
            if not is_modification:
                self.reset()
                self.last_prompt = prompt
                final_prompt = prompt
            else:
                final_prompt = f"{self.last_prompt}, {prompt}"
                self.last_prompt = final_prompt

            print(f"Generating image... This should only take a few seconds...")
            
            import urllib.parse
            import urllib.request
            import json
            import os
            
            hf_key = os.environ.get("HF_API_KEY")
            if not hf_key:
                raise RuntimeError("HF_API_KEY is not set. Please ensure it is loaded in your environment.")

            API_URL = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
            headers = {
                "Authorization": f"Bearer {hf_key}",
                "Content-Type": "application/json"
            }
            
            payload = {"inputs": final_prompt}
            req = urllib.request.Request(API_URL, data=json.dumps(payload).encode('utf-8'), headers=headers)
            with urllib.request.urlopen(req) as response:
                image_bytes = response.read()
                
            # Open and standardize to PNG bytes
            with Image.open(io.BytesIO(image_bytes)) as img:
                img = img.convert('RGB')
                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
                self.current_image_bytes = buffer.getvalue()
            
            return self._image_to_ansi(self.current_image_bytes)
            
        except Exception as e:
            raise RuntimeError(f"Error generating AI image: {str(e)}")

    def _image_to_ansi(self, image_bytes, width=45) -> str:
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img = img.convert('RGB')
            img = img.resize((width, width))
            
            ansi_str = ""
            for y in range(0, width, 2):
                for x in range(width):
                    r1, g1, b1 = img.getpixel((x, y))
                    r2, g2, b2 = img.getpixel((x, y+1)) if y+1 < width else (0,0,0)
                    ansi_str += f"\033[48;2;{r1};{g1};{b1}m\033[38;2;{r2};{g2};{b2}m\u2584"
                ansi_str += "\033[0m\n"
            return ansi_str
        except Exception as e:
            return f"[Image Rendering Failed: {e}]"

    def get_last_image_bytes(self):
        return self.current_image_bytes

creator_agent = CreatorAgent()
