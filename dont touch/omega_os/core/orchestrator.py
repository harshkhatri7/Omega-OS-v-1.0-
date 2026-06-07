import asyncio
import webbrowser
import os
import subprocess
from datetime import datetime
import re
import urllib.parse
from omega_os.core.vision import execute_vision_task
from omega_os.core.memory import save_fact, get_fact
from omega_os.core.create import creator_agent
from omega_os.core.think import execute_think_task
import send2trash

class Orchestrator:
    def __init__(self, log_callback, status_callback, speak_callback, show_gemini_result=None, download_callback=None):
        self.log = log_callback
        self.update_status = status_callback
        self.speak = speak_callback
        self.show_gemini_result = show_gemini_result
        self.download_callback = download_callback
        self.pending_app_list = []
        self.language = "en"

    def set_language(self, lang_code: str):
        self.language = lang_code
        self.log(f"Language set to: {lang_code}")

    def _find_app_links(self, app_name: str) -> list:
        start_menu_paths = [
            os.path.join(os.environ.get("PROGRAMDATA", "C:\\ProgramData"), "Microsoft", "Windows", "Start Menu", "Programs"),
            os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs")
        ]
        matches = []
        for base_path in start_menu_paths:
            if not os.path.exists(base_path): continue
            for root, dirs, files in os.walk(base_path):
                for file in files:
                    if file.endswith(".lnk") and app_name in file.lower():
                        clean_name = file.replace(".lnk", "")
                        lnk_path = os.path.join(root, file)
                        matches.append((clean_name, lnk_path))
        return matches

    async def process_goal(self, goal: str):
        goal_lower = goal.lower()
        self.log(f"Orchestrator analyzing goal: {goal}")
        
        self.update_status("Action Engine", "Running")

        # 0.25 App Disambiguation Selection
        if hasattr(self, 'pending_app_list') and self.pending_app_list:
            sel_match = re.search(r"open (\d+)", goal_lower)
            if sel_match:
                idx = int(sel_match.group(1)) - 1
                if 0 <= idx < len(self.pending_app_list):
                    os.startfile(self.pending_app_list[idx][1])
                    self.speak(f"Opened {self.pending_app_list[idx][0]}")
                    self.log(f"[b]Goal successfully achieved: {self.pending_app_list[idx][0]}.[/b]")
                    self.update_status("Action Engine", "Complete")
                    self.pending_app_list = []
                    return
            elif "cancel" in goal_lower:
                self.pending_app_list = []
                self.speak("Cancelled app selection.")
                self.log("Action Engine: App selection cancelled.")
                self.update_status("Action Engine", "Complete")
                return

        # 0.3 Omega Create Integration
        create_match = re.search(r"omega create (.+)", goal_lower)
        if create_match:
            prompt = create_match.group(1).strip()
            self.speak(f"Creating: {prompt}")
            self.log(f"Action: Forwarding to Omega Creator -> {prompt}")
            self.update_status("Omega Creator", "Running")
            
            # Reset session for a new creation
            creator_agent.reset()
            try:
                result = await asyncio.to_thread(creator_agent.send_prompt, prompt)
                if self.show_gemini_result:
                    self.show_gemini_result(result)
                self.speak("Here is what I created.")
                self.log("Action: Created content successfully.")
            except Exception as e:
                err_msg = str(e)
                self.speak("I encountered an error while creating that.")
                self.log(f"Action Engine [ERROR]: {err_msg}")
            finally:
                self.update_status("Omega Creator", "Waiting")
            
            self.update_status("Action Engine", "Complete")
            return

        # 0.4 Omega Create Follow-up
        change_match = re.search(r"change it to (.+)", goal_lower) or re.search(r"make it (.+)", goal_lower) or re.search(r"update creation to (.+)", goal_lower)
        if change_match:
            prompt = change_match.group(1).strip()
            if creator_agent.svg_session is None:
                self.speak("There is no active creation to modify. Say omega create first.")
            else:
                self.speak("Updating the creation.")
                self.log(f"Action: Forwarding to Omega Creator -> {prompt}")
                self.update_status("Omega Creator", "Running")
                try:
                    result = await asyncio.to_thread(creator_agent.send_prompt, prompt, True)
                    if self.show_gemini_result:
                        self.show_gemini_result(result)
                    self.speak("Creation updated.")
                    self.log("Action: Updated content successfully.")
                except Exception as e:
                    err_msg = str(e)
                    self.speak("I encountered an error while updating that.")
                    self.log(f"Action Engine [ERROR]: {err_msg}")
                finally:
                    self.update_status("Omega Creator", "Waiting")
            self.update_status("Action Engine", "Complete")
            return

        # 0.45 Close / Hide Creation
        if "close creation" in goal_lower or "hide creation" in goal_lower:
            if self.show_gemini_result:
                self.show_gemini_result("")
            self.log("Action: Created content successfully.")
            self.update_status("Omega Creator", "Waiting")
            self.speak("Creation hidden.")
            self.update_status("Action Engine", "Complete")
            return

        # 0.46 Download Creation
        if "download creation" in goal_lower or "save creation" in goal_lower:
            if self.download_callback:
                self.download_callback()
            self.update_status("Action Engine", "Complete")
            return

        # 0.47 Omega Think Integration
        think_match = re.search(r"omega think (.+)", goal_lower)
        if think_match:
            question = think_match.group(1).strip()
            self.speak("Thinking...")
            self.log(f"Action: Forwarding to Gemini Think -> {question}")
            self.update_status("Omega Think", "Running")
            
            try:
                answer = await asyncio.to_thread(execute_think_task, question)
                self.log(f"\n[b]Omega Think Answer:[/b]\n{answer}\n")
                self.speak(answer)
                self.log(f"Think API Response: {answer}")
            except Exception as e:
                self.log(f"Think Engine [ERROR]: {str(e)}")
                self.speak("I encountered an error while thinking.")
            finally:
                self.update_status("Omega Think", "Waiting")
            
            self.update_status("Action Engine", "Complete")
            return

        # 0. Conversational Memory Setting
        name_set_match = re.search(r"my name is (.+)", goal_lower)
        if name_set_match:
            user_name = name_set_match.group(1).strip()
            save_fact("name", user_name)
            self.speak(f"Nice to meet you, {user_name}. I will remember that.")
            self.log(f"Action: Saved name '{user_name}' to secret memory.")
            self.update_status("Action Engine", "Complete")
            self.log("[b]Goal successfully achieved.[/b]")
            return

        # 0.5 Conversational Memory Retrieval
        if "what is my name" in goal_lower or "what's my name" in goal_lower:
            user_name = get_fact("name")
            if user_name:
                self.speak(f"Your name is {user_name}.")
                self.log(f"Action: Retrieved name '{user_name}' from memory.")
            else:
                self.speak("I don't know your name yet. You can tell me by saying 'My name is'.")
                self.log("Action: Name not found in memory.")
            self.update_status("Action Engine", "Complete")
            self.log("[b]Goal successfully achieved.[/b]")
            return

        # 0.75 Screen Access Demo (GUI Automation)
        if re.search(r"access.*screen", goal_lower):
            self.speak("Accessing your screen now. Entering background mode.")
            self.update_status("Action Engine", "Controlling Screen")
            
            loop = asyncio.get_running_loop()
            
            def gui_automation_task():
                import pygetwindow as gw
                from omega_os.core.voice import listen as voice_listen
                import time
                
                # Minimize terminal
                windows = gw.getWindowsWithTitle("OMEGA")
                if not windows:
                    # Fallback
                    windows = [w for w in gw.getAllWindows() if "python" in w.title.lower() or "cmd" in w.title.lower() or "powershell" in w.title.lower() or "windows terminal" in w.title.lower()]
                    
                target_window = windows[0] if windows else None
                if target_window:
                    try:
                        target_window.minimize()
                    except: pass
                    
                time.sleep(1)
                
                self.speak("I am in the background. Tell me what to do.")
                
                # Continuous Recursive Loop
                while True:
                    text = voice_listen().lower()
                    if not text:
                        continue
                        
                    if "omega stop" in text:
                        break
                    
                    self.speak(f"Processing: {text}")
                    # Dispatch to main orchestrator loop
                    asyncio.run_coroutine_threadsafe(self.process_goal(text), loop)
                        
                self.speak("Stopping screen access. Returning to foreground.")
                
                # Maximize terminal
                if target_window:
                    try:
                        target_window.restore()
                    except: pass

            await asyncio.to_thread(gui_automation_task)
            
            self.update_status("Action Engine", "Complete")
            self.log("[b]Goal successfully achieved.[/b]")
            return

        # 1. Background Timers
        timer_match = re.search(r"set.*timer.*for (\d+) (second|minute|hour)", goal_lower)
        if timer_match:
            amount = int(timer_match.group(1))
            unit = timer_match.group(2)
            seconds = amount
            if unit == "minute": seconds *= 60
            elif unit == "hour": seconds *= 3600
            
            self.speak(f"Setting a timer for {amount} {unit}s.")
            self.log(f"Action: Timer set for {amount} {unit}s.")
            
            async def background_timer(sec, a, u):
                await asyncio.sleep(sec)
                self.speak(f"Your timer for {a} {u}s is up!")
                self.log(f"Action: Timer complete.")
            
            asyncio.create_task(background_timer(seconds, amount, unit))
            self.update_status("Action Engine", "Complete")
            self.log("[b]Goal successfully achieved.[/b]")
            return

        # 2. YouTube Search
        yt_search_match = re.search(r"search (.+) (on|in) youtube", goal_lower)
        if yt_search_match:
            query = yt_search_match.group(1).strip()
            self.speak(f"Searching YouTube for {query}")
            self.log(f"Action: YouTube Search for {query}")
            encoded_query = urllib.parse.quote_plus(query)
            webbrowser.open(f"https://www.youtube.com/results?search_query={encoded_query}")
            self.update_status("Action Engine", "Complete")
            self.log("[b]Goal successfully achieved.[/b]")
            return

        # 3. Safe File/Folder Deletion
        del_match = re.search(r"delete (file|folder) (.+)", goal_lower)
        if del_match:
            target = del_match.group(2).strip()
            self.speak(f"Attempting to delete {target}")
            search_paths = [
                os.getcwd(),
                os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
            ]
            deleted = False
            for p in search_paths:
                if not os.path.exists(p): continue
                for root, dirs, files in os.walk(p):
                    for d in dirs:
                        if target == d.lower():
                            try:
                                send2trash.send2trash(os.path.join(root, d))
                                deleted = True
                                break
                            except: pass
                    if not deleted:
                        for f in files:
                            if target == f.lower() or target == os.path.splitext(f)[0].lower():
                                try:
                                    send2trash.send2trash(os.path.join(root, f))
                                    deleted = True
                                    break
                                except: pass
                    if deleted: break
                if deleted: break
                
            if deleted:
                self.speak(f"Safely moved {target} to the Recycle Bin.")
                self.log(f"Action: Deleted {target}")
                self.update_status("Action Engine", "Complete")
                self.log("[b]Goal successfully achieved.[/b]")
            else:
                self.speak(f"Could not find {target} to delete.")
                self.log("Action Engine Failed: Target not found.")
                self.update_status("Action Engine", "Failed")
            return

        # 4. Dynamic Website Match
        website_match = re.search(r"open website (.+)", goal_lower)
        if website_match:
            site_name = website_match.group(1).strip()
            self.speak(f"Searching and opening website {site_name}")
            self.log(f"Action: Dynamic search for {site_name}")
            encoded_name = urllib.parse.quote_plus(site_name)
            webbrowser.open(f"https://duckduckgo.com/?q=!ducky+{encoded_name}")
            self.update_status("Action Engine", "Complete")
            self.log("[b]Goal successfully achieved.[/b]")
            return

        # 5. Dynamic App Match
        app_match = re.search(r"open app (.+)", goal_lower)
        if app_match:
            app_name = app_match.group(1).strip()
            self.speak(f"Searching for app {app_name}")
            self.log(f"Action: Scanning Start Menu for {app_name}")
            matches = self._find_app_links(app_name)
            
            if not matches:
                self.speak(f"Could not find {app_name} on your computer.")
                self.log("Action Engine Failed: App not found.")
                self.update_status("Action Engine", "Failed")
            elif len(matches) == 1:
                os.startfile(matches[0][1])
                self.speak(f"Opened {matches[0][0]}")
                self.log(f"[b]Goal successfully achieved: {matches[0][0]}.[/b]")
                self.update_status("Action Engine", "Complete")
            else:
                self.pending_app_list = matches[:5]
                names_speech = ", ".join([f"Say open {i+1} for {m[0]}" for i, m in enumerate(self.pending_app_list)])
                self.speak(f"I found multiple apps. {names_speech}")
                self.log("Action Engine: Waiting for user to select app.")
                self.update_status("Action Engine", "Waiting")
            return

        # 6. Screen Vision Intent
        if "screen" in goal_lower or "take action" in goal_lower:
            execute_vision_task(goal_lower, self.log, self.speak)
            self.update_status("Action Engine", "Complete")
            self.log("[b]Goal successfully achieved.[/b]")
            return

        # 7. Time (strict match)
        if re.search(r"\btime\b", goal_lower):
            current_time = datetime.now().strftime("%I:%M %p")
            self.speak(f"The current time is {current_time}")
            self.log(f"Action: Time is {current_time}")
            self.update_status("Action Engine", "Complete")
            self.log("[b]Goal successfully achieved.[/b]")
            return

        # Hardcoded Fallbacks
        if "youtube" in goal_lower:
            self.speak("Opening YouTube")
            self.log("Action: Opening YouTube")
            webbrowser.open("https://www.youtube.com")
        elif "browser" in goal_lower or "google" in goal_lower:
            self.speak("Opening your browser")
            self.log("Action: Opening default browser")
            webbrowser.open("https://www.google.com")
        elif "notepad" in goal_lower:
            self.speak("Opening Notepad")
            self.log("Action: Launching Notepad")
            subprocess.Popen(["notepad.exe"])
        else:
            self.speak("I'm sorry, I don't know how to do that yet.")
            self.log("Action: Unrecognized command.")
            self.update_status("Action Engine", "Failed")
            return
            
        self.update_status("Action Engine", "Complete")
        self.log("[b]Goal successfully achieved.[/b]")
        self.speak("Goal achieved.")
