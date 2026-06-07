import pyttsx3
import speech_recognition as sr
import threading

# Initialize TTS engine
try:
    engine = pyttsx3.init()
    # Optional: adjust properties like rate or volume if desired
    # engine.setProperty('rate', 175) 
except Exception as e:
    engine = None

_speak_lock = threading.Lock()

def speak(text: str):
    """Speaks the given text using pyttsx3."""
    if engine:
        with _speak_lock:
            try:
                engine.say(text)
                engine.runAndWait()
            except RuntimeError:
                pass


def listen() -> str:
    """Listens to the microphone and returns the transcribed text."""
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            # Listen for up to 5 seconds before giving up if no speech starts
            # Stop after 10 seconds of speech
            audio = r.listen(source, timeout=5, phrase_time_limit=10)
            
        text = r.recognize_google(audio)
        return text
    except sr.WaitTimeoutError:
        return ""
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        return ""
    except Exception as e:
        print(f"Error in listen: {e}")
        return ""

def start_background_listener(app_callback):
    """Starts listening in the background for the wake word 'omega'."""
    r = sr.Recognizer()
    mic = sr.Microphone()
    
    with mic as source:
        r.adjust_for_ambient_noise(source, duration=1)
        
    def callback(recognizer, audio):
        try:
            text = recognizer.recognize_google(audio).lower()
            if "omega" in text:
                app_callback(text)
        except sr.UnknownValueError:
            pass
        except sr.RequestError:
            pass
            
    # Starts a daemon thread that calls callback with audio
    stop_listening = r.listen_in_background(mic, callback)
    return stop_listening
