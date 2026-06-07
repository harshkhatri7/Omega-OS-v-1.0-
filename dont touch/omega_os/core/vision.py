import pyautogui
from PIL import ImageGrab
import os

import json
import threading
from dotenv import load_dotenv

def capture_screen(save_path="screenshot.png"):
    """Captures the current screen and saves it."""
    screenshot = ImageGrab.grab()
    screenshot.save(save_path)
    return save_path

def execute_vision_task(task_instruction: str, log_callback, speak_callback):
    """
    Uses Gemini 2.5 Flash to analyze the screen and execute mouse/keyboard commands.
    """
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key or api_key == "":
        speak_callback("I need a Gemini API key to see your screen. Please add it to the dot E N V file I created in your folder.")
        log_callback("Vision Engine [ERROR]: AI Vision API key missing. Please add GEMINI_API_KEY to .env file.")
        return
        
    log_callback("Vision Engine: Capturing screen...")
    screenshot_path = capture_screen("current_screen.png")
    
    speak_callback("Analyzing your screen...")
    log_callback("Vision Engine: Sending to Gemini 2.5 Flash...")
    
    def _run_gemini():
        from google import genai
        from google.genai import types
        import time
        from PIL import Image
        
        client = genai.Client(api_key=api_key)
        
        speak_callback("Vision Agent initialized. Commencing autonomous operation.")
        
        step = 0
        while True:
            step += 1
            if step > 20:
                speak_callback("I have reached the maximum number of steps. Stopping.")
                log_callback("Vision Engine: Max steps reached.")
                break
                
            log_callback(f"Vision Engine: Capturing screen (Step {step})...")
            screenshot_path = capture_screen("current_screen.png")
        
            prompt = f'''
            You are an autonomous AI screen control agent. The user's ultimate goal is: "{task_instruction}".
            Analyze the provided screenshot of the user's current screen.
            Determine the single NEXT action required to progress towards achieving this goal.
            If the goal is fully achieved, or you cannot proceed, return action: "done".
            If the request requires clicking an element, output a bounding box [ymin, xmin, ymax, xmax] of that element, normalized 0-1000.
            Format your response as strict JSON with this exact structure:
            {{
               "action": "click" | "scroll" | "type" | "press_key" | "done",
               "box_2d": [ymin, xmin, ymax, xmax],
               "text": "text to type or key to press",
               "scroll_amount": -500
            }}
            For "click", you must provide box_2d.
            For "scroll", provide scroll_amount (negative for down, positive for up).
            For "type" or "press_key", provide "text".
            Return ONLY valid JSON.
            '''
            
            try:
                img = Image.open(screenshot_path)
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[img, prompt],
                    config=types.GenerateContentConfig(
                        temperature=0.0,
                        response_mime_type="application/json",
                    )
                )
                
                text_response = response.text
                if text_response.startswith('```json'):
                    text_response = text_response.strip('```json').strip('```').strip()
                
                data = json.loads(text_response)
                action = data.get('action')
                
                if action == 'done':
                    log_callback("Vision Engine: Agent determined goal is complete.")
                    speak_callback("I have completed the task.")
                    break
                
                elif action == 'click':
                    box = data.get('box_2d')
                    if box and len(box) == 4:
                        screen_w, screen_h = pyautogui.size()
                        ymin, xmin, ymax, xmax = box
                        center_x = int(((xmin + xmax) / 2) / 1000 * screen_w)
                        center_y = int(((ymin + ymax) / 2) / 1000 * screen_h)
                        
                        pyautogui.moveTo(center_x, center_y, duration=0.3)
                        pyautogui.click()
                        log_callback(f"Vision Engine: Clicked at ({center_x}, {center_y})")
                        
                elif action == 'scroll':
                    amount = data.get('scroll_amount', -500)
                    pyautogui.scroll(amount)
                    log_callback(f"Vision Engine: Scrolled {amount}")
                    
                elif action == 'type':
                    text_to_type = data.get('text', '')
                    pyautogui.write(text_to_type, interval=0.05)
                    log_callback(f"Vision Engine: Typed '{text_to_type}'")
                    
                elif action == 'press_key':
                    key = data.get('text', 'enter')
                    pyautogui.press(key)
                    log_callback(f"Vision Engine: Pressed '{key}'")
                    
                else:
                    log_callback(f"Vision Engine: Unrecognized action '{action}'. Stopping.")
                    speak_callback("I encountered an unknown action. Stopping.")
                    break
                    
                # Wait for the screen to update before taking the next screenshot
                time.sleep(2)
                    
            except Exception as e:
                log_callback(f"Vision Engine [ERROR]: {str(e)}")
                speak_callback("I encountered an error analyzing the screen. Stopping.")
                break

    threading.Thread(target=_run_gemini).start()
