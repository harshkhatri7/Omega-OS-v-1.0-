import os
import urllib.request
import urllib.error
import zipfile
import shutil
import time

# ==========================================
# CONFIGURATION
# ==========================================
# Replace this with your actual GitHub repository URL once uploaded
# Example: "https://github.com/YourUsername/Omega-OS"
GITHUB_REPO_URL = "https://github.com/harshkhatri7/Omega-OS-v-1.0-"

def get_raw_url(repo_url, filepath):
    # Convert https://github.com/User/Repo to https://raw.githubusercontent.com/User/Repo/main/filepath
    parts = repo_url.rstrip('/').split('/')
    if len(parts) >= 5:
        user = parts[-2]
        repo = parts[-1]
        return f"https://raw.githubusercontent.com/{user}/{repo}/main/{filepath}"
    return None

def get_zip_url(repo_url):
    parts = repo_url.rstrip('/').split('/')
    if len(parts) >= 5:
        user = parts[-2]
        repo = parts[-1]
        return f"https://github.com/{user}/{repo}/archive/refs/heads/main.zip"
    return None

def check_for_updates():
    if "YourUsername" in GITHUB_REPO_URL:
        print("[WARNING] Auto-update skipped!")
        print("          Please configure GITHUB_REPO_URL in 'dont touch/updater.py'")
        print("          to enable automatic updates from GitHub.")
        time.sleep(2)
        return

    local_version = "1.0.0"
    version_file = "version.txt"
    if os.path.exists(version_file):
        with open(version_file, "r") as f:
            local_version = f.read().strip()
    else:
        with open(version_file, "w") as f:
            f.write(local_version)

    raw_version_url = get_raw_url(GITHUB_REPO_URL, "dont%20touch/version.txt")
    if not raw_version_url:
        return

    print("[INFO] Checking for updates online...")
    try:
        req = urllib.request.Request(raw_version_url)
        with urllib.request.urlopen(req) as response:
            remote_version = response.read().decode('utf-8').strip()
            
        if remote_version != local_version:
            print(f"[INFO] An update was found! (Local: {local_version} -> Remote: {remote_version})")
            print("[INFO] Downloading the latest Omega OS version...")
            zip_url = get_zip_url(GITHUB_REPO_URL)
            zip_path = "update.zip"
            
            # Download Zip
            req = urllib.request.Request(zip_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response, open(zip_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
            
            print("[INFO] Extracting and installing update...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                extract_dir = "update_extracted"
                zip_ref.extractall(extract_dir)
                
                # Github zips contain a root folder like Omega-OS-main
                extracted_root = os.path.join(extract_dir, os.listdir(extract_dir)[0])
                
                # Overwrite 'dont touch' folder
                source_dont_touch = os.path.join(extracted_root, "dont touch")
                if os.path.exists(source_dont_touch):
                    for item in os.listdir(source_dont_touch):
                        s = os.path.join(source_dont_touch, item)
                        d = os.path.join(os.getcwd(), item)
                        if os.path.isdir(s):
                            shutil.copytree(s, d, dirs_exist_ok=True)
                        else:
                            shutil.copy2(s, d)
                            
                # Overwrite parent folder (e.g., Omega OS.bat)
                parent_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
                for item in os.listdir(extracted_root):
                    if item != "dont touch":
                        s = os.path.join(extracted_root, item)
                        d = os.path.join(parent_dir, item)
                        if os.path.isdir(s):
                            shutil.copytree(s, d, dirs_exist_ok=True)
                        else:
                            shutil.copy2(s, d)
                
            # Cleanup
            shutil.rmtree(extract_dir)
            os.remove(zip_path)
            
            # Update local version
            with open(version_file, "w") as f:
                f.write(remote_version)
                
            print("[SUCCESS] Omega OS has been updated successfully!")
            print("[INFO] Resuming boot sequence...")
            time.sleep(2)
        else:
            print("[INFO] Omega OS is up to date.")
    except urllib.error.URLError:
        print("[WARNING] Could not connect to the update server. Proceeding with current version.")
    except Exception as e:
        print(f"[WARNING] Failed to check for updates: {e}")

if __name__ == "__main__":
    check_for_updates()
