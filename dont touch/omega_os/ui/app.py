from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Header, Footer, Static, Log, Button, Select, Input
from textual.reactive import reactive
from textual import work
import hashlib
import asyncio

from .widgets import AgentStatusList, APIStatus, VoiceCommandGuide, GeminiResultBox, AppLogo
from omega_os.core.orchestrator import Orchestrator
import os

import json

def get_password_hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

class LoginScreen(ModalScreen):
    CSS = """
    LoginScreen {
        align: center middle;
        background: $surface 80%;
    }
    #login-dialog {
        padding: 1 2;
        width: 40;
        height: auto;
        border: thick $primary;
        background: $surface;
    }
    #login-title {
        text-align: center;
        text-style: bold;
        padding-bottom: 1;
    }
    #login-error {
        color: $error;
        text-align: center;
        display: none;
    }
    """
    
    def compose(self) -> ComposeResult:
        with Vertical(id="login-dialog"):
            yield Static("Welcome to Omega OS", id="login-title")
            yield Static("Please enter your ID and Password:")
            yield Input(placeholder="User ID", id="userid-input")
            yield Input(placeholder="Password", password=True, id="password-input")
            yield Button("Login", variant="primary", id="login-btn")
            yield Static("", id="login-error")

    def on_mount(self) -> None:
        # Create default admin account if users.json doesn't exist
        if not os.path.exists(".users.json"):
            try:
                default_users = {"admin": get_password_hash("admin")}
                with open(".users.json", "w") as f:
                    json.dump(default_users, f)
            except Exception:
                pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "login-btn":
            self.attempt_login()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "userid-input":
            self.query_one("#password-input").focus()
        elif event.input.id == "password-input":
            self.attempt_login()

    def attempt_login(self):
        uid = self.query_one("#userid-input").value.strip()
        pwd = self.query_one("#password-input").value.strip()
        error_msg = self.query_one("#login-error", Static)
        
        if not uid or not pwd:
            error_msg.update("ID and Password cannot be empty.")
            error_msg.display = True
            return
            
        try:
            if not os.path.exists(".users.json"):
                error_msg.update("No users configured.")
                error_msg.display = True
                return
                
            with open(".users.json", "r") as f:
                users = json.load(f)
            
            if uid in users and users[uid] == get_password_hash(pwd):
                self.dismiss(True)
            else:
                error_msg.update("Invalid ID or password.")
                error_msg.display = True
                self.query_one("#password-input").value = ""
        except Exception:
            error_msg.update("Error reading users file.")
            error_msg.display = True


class OmegaOSApp(App):
    CSS = """
    Screen {
        background: $surface-darken-1;
        overflow-y: auto;
        overflow-x: auto;
    }
    
    #main-container {
        layout: grid;
        grid-size: 3 3;
        grid-columns: 1fr 2fr 1fr;
        grid-rows: 15% 70% 15%;
        padding: 1;
        grid-gutter: 1;
        min-width: 100;
        min-height: 35;
    }
    
    .panel {
        border: round $primary;
        background: $surface;
        padding: 1;
    }
    
    #goal-panel {
        column-span: 3;
        row-span: 1;
        border: double $accent;
        content-align: center middle;
    }
    
    #left-panel {
        column-span: 1;
        row-span: 1;
        layout: vertical;
    }
    
    #agent-panel {
        height: 100%;
    }
    
    #logs-panel {
        column-span: 1;
        row-span: 1;
    }
    
    #metrics-panel {
        column-span: 1;
        row-span: 1;
        layout: vertical;
    }
    
    #chat-panel {
        column-span: 3;
        row-span: 1;
        layout: horizontal;
    }
    
    #lang-select {
        width: 30;
    }
    
    #text-input {
        width: 3fr;
    }
    
    #speak-btn {
        width: 1fr;
    }
    
    #gemini-result {
        column-span: 1;
        row-span: 1;
        display: none;
    }
    
    Button {
        width: 100%;
    }
    """

    TITLE = "OMEGA OS"
    SUB_TITLE = "Terminal-Native Autonomous OS | Creator - Harsh Khatri"

    def __init__(self):
        super().__init__()
        self.orchestrator = Orchestrator(
            self.update_logs, 
            self.update_agent_status, 
            self.speak,
            self.show_gemini_result,
            self.download_creation_callback
        )
        self.is_awake = False
        
        # Load language from .lang if exists
        self.default_lang = "en"
        try:
            if os.path.exists(".lang"):
                with open(".lang", "r") as f:
                    self.default_lang = f.read().strip()
                self.orchestrator.set_language(self.default_lang)
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main-container"):
            # Top: Active Goal
            yield Static("[b]Active Goal:[/b]\nWaiting for input...", id="goal-panel", classes="panel")
            
            # Middle Left: Agent Status
            with Vertical(id="left-panel", classes="panel"):
                yield AppLogo(id="app-logo")
                yield AgentStatusList(id="agent-panel")
            
            # Middle Center: Live Logs
            yield Log(id="logs-panel", classes="panel")
            
            # Middle Right: Status and Guide / Gemini Box
            with Vertical(id="metrics-panel"):
                yield APIStatus(classes="panel", id="api-status")
                yield VoiceCommandGuide(classes="panel", id="voice-guide")
            yield GeminiResultBox(id="gemini-result", classes="panel")
            
            # Bottom: Chat Console & Settings
            with Horizontal(id="chat-panel", classes="panel"):
                yield Select(
                    options=[
                        ("English", "en"), 
                        ("Hindi", "hi"), 
                        ("Spanish", "es"), 
                        ("French", "fr"), 
                        ("Mandarin", "zh")
                    ],
                    prompt="Language",
                    id="lang-select",
                    value=self.default_lang
                )
                yield Input(placeholder="Type your command here and press Enter...", id="text-input")
                yield Button("Press to Speak", id="speak-btn", variant="primary")
        yield Footer()

    def on_mount(self) -> None:
        def check_login(logged_in: bool | None):
            if logged_in:
                self.start_os()
                
        self.push_screen(LoginScreen(), check_login)

    def start_os(self) -> None:
        log_widget = self.query_one("#logs-panel", Log)
        log_widget.write_line("System initialized.")
        log_widget.write_line("Awaiting voice input. Say 'Hey Omega' or press the button.")
        from omega_os.core.voice import start_background_listener
        self._stop_listening = start_background_listener(self.process_background_audio)

    def process_background_audio(self, text: str) -> None:
        self.call_from_thread(self._handle_background_audio, text)

    def _handle_background_audio(self, text: str) -> None:
        if "omega" in text:
            # Stop background listener so mic is freed
            if hasattr(self, '_stop_listening') and self._stop_listening:
                self._stop_listening(wait_for_stop=False)
                
            self.call_from_thread(self.query_one("#logs-panel", Log).write_line, "Awake and listening...")
            # Trigger active listener
            self.start_listening(from_wake_word=True)

    def execute_goal(self, goal: str) -> None:
        goal_panel = self.query_one("#goal-panel", Static)
        goal_panel.update(f"[b]Active Goal:[/b]\n[green]{goal}[/green]")
        self.query_one("#logs-panel", Log).write_line(f"Received goal: {goal}")
        asyncio.create_task(self.orchestrator.process_goal(goal))

    @work
    async def speak(self, text: str) -> None:
        if not text:
            return
            
        target_lang = getattr(self.orchestrator, 'language', 'en')
        if target_lang != 'en':
            from omega_os.core.think import execute_think_task
            lang_map = {"hi": "Hindi", "es": "Spanish", "fr": "French", "zh": "Mandarin Chinese"}
            lang_name = lang_map.get(target_lang, "English")
            try:
                translated = await execute_think_task(f"Translate the following text into {lang_name}. Output ONLY the translation without quotes: {text}")
                text = translated.strip()
            except Exception as e:
                self.query_one("#logs-panel", Log).write_line(f"Translation error: {e}")
                
        import asyncio
        loop = asyncio.get_running_loop()
        from omega_os.core.voice import speak as voice_speak
        await loop.run_in_executor(None, voice_speak, text)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "speak-btn":
            # If manually pressed, stop background listener so mic is freed
            if hasattr(self, '_stop_listening') and self._stop_listening:
                self._stop_listening(wait_for_stop=False)
            self.start_listening()

    @work(thread=True)
    def start_listening(self, from_wake_word=False) -> None:
        if from_wake_word:
            from omega_os.core.voice import speak as voice_speak
            voice_speak("Hey, I am listening")
            
        goal_panel = self.query_one("#goal-panel", Static)
        self.call_from_thread(goal_panel.update, "[b]Active Goal:[/b]\n[yellow]Listening...[/yellow]")
        self.call_from_thread(self.query_one("#logs-panel", Log).write_line, "Listening to microphone...")
        
        from omega_os.core.voice import listen as voice_listen
        goal = voice_listen()
        
        # Restart background listener immediately after foreground listening finishes
        from omega_os.core.voice import start_background_listener
        self._stop_listening = start_background_listener(self.process_background_audio)
        
        if not goal:
            self.call_from_thread(goal_panel.update, "[b]Active Goal:[/b]\n[red]Didn't catch that. Please try again.[/red]")
            return
            
        self.call_from_thread(goal_panel.update, f"[b]Active Goal:[/b]\n[green]{goal}[/green]")
        self.call_from_thread(self.query_one("#logs-panel", Log).write_line, f"Received goal: {goal}")
        
        # Start orchestration in background
        self.call_from_thread(lambda: asyncio.create_task(self.orchestrator.process_goal(goal)))

    def update_logs(self, message: str) -> None:
        self.query_one("#logs-panel", Log).write_line(message)

    def update_agent_status(self, agent_name: str, status: str) -> None:
        agent_list = self.query_one(AgentStatusList)
        agent_list.update_status(agent_name, status)

    def show_gemini_result(self, text: str) -> None:
        self._toggle_gemini_panel(text)
        
    def _toggle_gemini_panel(self, text: str):
        metrics_panel = self.query_one("#metrics-panel")
        gemini_panel = self.query_one("#gemini-result", GeminiResultBox)
        
        if text:
            metrics_panel.display = False
            gemini_panel.display = True
            gemini_panel.update_content(text)
            # Automatically save and open the high-res image so the user doesn't just see the pixelated terminal version
            try:
                self.download_creation(auto_open=True)
            except Exception as e:
                self.query_one("#logs-panel", Log).write_line(f"Auto-open failed: {e}")
        else:
            metrics_panel.display = True
            gemini_panel.display = False
            gemini_panel.update_content("")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "speak-btn":
            if hasattr(self, '_stop_listening') and self._stop_listening:
                self._stop_listening(wait_for_stop=False)
            self.start_listening()
        elif event.button.id == "download-creation-btn":
            self.download_creation_callback()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.control.id == "lang-select":
            self.orchestrator.set_language(event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "text-input":
            text = event.value.strip()
            if text:
                # Stop background listener while processing
                if hasattr(self, '_stop_listening') and self._stop_listening:
                    self._stop_listening(wait_for_stop=False)
                
                # Clear the input
                event.input.value = ""
                
                # Execute the goal directly
                goal_panel = self.query_one("#goal-panel", Static)
                self.call_from_thread(goal_panel.update, f"[b]Active Goal:[/b]\n[green]{text}[/green]")
                self.call_from_thread(self.query_one("#logs-panel", Log).write_line, f"Received text goal: {text}")
                
                self.call_from_thread(lambda: asyncio.create_task(self.orchestrator.process_goal(text)))
                
                # Restart background listener
                from omega_os.core.voice import start_background_listener
                self._stop_listening = start_background_listener(self.process_background_audio)

    def download_creation_callback(self):
        self.download_creation()
        
    def download_creation(self, auto_open=False):
        from omega_os.core.create import creator_agent
        img_bytes = creator_agent.current_image_bytes
        
        if not img_bytes:
            if not auto_open: self.speak("There is no image to download.")
            return
            
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        images_dir = os.path.join(base_dir, "images")
        if not os.path.exists(images_dir):
            try:
                os.makedirs(images_dir)
            except Exception:
                images_dir = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
        filepath = os.path.join(images_dir, "omega_creation.png")
        try:
            with open(filepath, "wb") as f:
                f.write(img_bytes)
            if not auto_open:
                self.query_one("#logs-panel", Log).write_line(f"Saved image to {filepath}")
                self.speak("Image saved to your images folder.")
            
            # Open the high-res image automatically using Windows default image viewer
            if auto_open:
                os.startfile(filepath)
        except Exception as e:
            self.query_one("#logs-panel", Log).write_line(f"Failed to save image: {e}")
            self.speak("I could not save the creation.")
