import sys
import subprocess
import os

def install_requirements():
    req_file = "requirements.txt"
    if not os.path.exists(req_file):
        print("[ERROR] requirements.txt not found!")
        sys.exit(1)
        
    with open(req_file, "r") as f:
        reqs = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        
    total = len(reqs)
    if total == 0:
        print("[INFO] No requirements to install.")
        return
        
    # Split out PyAudio to handle its potential failure gracefully
    core_reqs = [r for r in reqs if "PyAudio" not in r]
    pyaudio_req = next((r for r in reqs if "PyAudio" in r), None)
    
    print("\n[INFO] Installing core OS requirements... (This may take a minute)")
    try:
        # Run bulk install for massive speed improvement
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q"] + core_reqs,
            check=True
        )
    except subprocess.CalledProcessError:
        print("\n[ERROR] Failed to install core requirements. Please check your internet connection.")
        sys.exit(1)
        
    if pyaudio_req:
        try:
            # Install PyAudio separately so it doesn't crash the whole process if it fails
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-q", pyaudio_req],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError:
            print(f"\n[WARNING] Failed to install {pyaudio_req}. Voice input will be disabled, but Omega OS will still work.")

    print("\n[INFO] Download Complete!")

if __name__ == "__main__":
    install_requirements()
