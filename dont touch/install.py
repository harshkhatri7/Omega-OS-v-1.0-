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
        
    bar_length = 30
    
    print() # New line for the progress bar
    for i, req in enumerate(reqs):
        # Progress calculation (current item being downloaded)
        progress = i / total
        filled_length = int(bar_length * progress)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        # Determine package name for display (strip versions)
        display_req = req.split(">=")[0].split("==")[0].split("<=")[0].strip()
        display_req_padded = (display_req[:15] + '...') if len(display_req) > 15 else display_req.ljust(18)
        
        # Print progress using carriage return to overwrite the line
        sys.stdout.write(f"\r[INFO] Downloading: {display_req_padded} [{bar}] [{i+1}/{total}]")
        sys.stdout.flush()
        
        # Check if already installed
        try:
            import pkg_resources
            pkg_resources.require(req)
            already_installed = True
        except Exception:
            already_installed = False

        if not already_installed:
            # Install the package silently
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-q", req],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except subprocess.CalledProcessError:
                if "PyAudio" in req:
                    print(f"\n[WARNING] Failed to install {req}. Voice input will be disabled, but Omega OS will still work.")
                else:
                    print(f"\n[ERROR] Failed to install {req}. Please check your connection.")
                    sys.exit(1)
            
    # Final 100% state
    bar = '█' * bar_length
    sys.stdout.write(f"\r[INFO] Download Complete!   {' '*18} [{bar}] [{total}/{total}]\n")
    sys.stdout.flush()

if __name__ == "__main__":
    install_requirements()
