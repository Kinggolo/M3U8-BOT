#!/usr/bin/env python3
"""
Telegram M3U8 Downloader - GitHub-ready bot.py (V3)
Features:
 - Queue system (multiple links)
 - Retry mechanism (3 attempts)
 - Custom filename support: "My Lecture | https://.../file.m3u8"
 - Ignore old messages at start
 - Google Drive save (Colab auto-mount)
 - Installs aria2c & ffmpeg if missing (Colab/Ubuntu)
 - Clean workspace after each download
Requirements:
 - Set environment variables BOT_TOKEN and CHAT_ID before running.
   Example (Colab shell): 
     !BOT_TOKEN="..." CHAT_ID="..." python3 bot.py
"""

import os
import sys
import time
import requests
import re
import shutil
import subprocess
from datetime import datetime

# -------------------------
# Configuration / Defaults
# -------------------------
# Destination folder inside Google Drive (default as you asked)
DRIVE_FOLDER = "/content/drive/MyDrive/M3U8"

# How many retry attempts per link
MAX_RETRIES = 3

# aria2c parallel options
ARIA2_OPTIONS = ["-x", "16", "-s", "16", "--continue=true", "--auto-file-renaming=false"]

# Poll interval (seconds)
POLL_INTERVAL = 5

# -------------------------
# Helper utilities
# -------------------------
def get_env_secret(name):
    v = os.environ.get(name)
    if v:
        return v
    return None

def install_package(pkg):
    """Install apt-get package if not present (works in Colab)."""
    try:
        subprocess.run(["command", "-v", pkg], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)
        return True
    except Exception:
        # try apt-get install
        print(f"[installer] Installing {pkg} (may ask for permissions)...")
        subprocess.run(["apt-get", "update"], check=False)
        subprocess.run(["apt-get", "install", "-y", pkg], check=True)
        return True

def safe_run(cmd, shell=False):
    """Run subprocess, raise on error."""
    print(f"[run] {cmd if isinstance(cmd, str) else ' '.join(cmd)}")
    res = subprocess.run(cmd, shell=shell)
    if res.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}")

def clean_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]',"", name).strip()

# -------------------------
# Telegram helpers
# -------------------------
BOT_TOKEN = get_env_secret("BOT_TOKEN")
CHAT_ID = get_env_secret("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    print("ERROR: BOT_TOKEN and CHAT_ID must be provided as environment variables.")
    print('Example (Colab shell): !BOT_TOKEN="123:abc" CHAT_ID="9876543" python3 bot.py')
    sys.exit(1)

try:
    CHAT_ID = int(CHAT_ID)
except Exception:
    print("ERROR: CHAT_ID must be an integer.")
    sys.exit(1)

API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_telegram_message(text: str):
    try:
        url = API_BASE + "/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text}, timeout=10)
    except Exception as e:
        print(f"[telegram] Failed to send message: {e}")

def get_updates():
    url = API_BASE + "/getUpdates"
    resp = requests.get(url, timeout=15)
    return resp.json()

# -------------------------
# Drive mount (Colab) attempt
# -------------------------
def mount_drive_if_colab():
    """Try to mount Google Drive if running inside Google Colab."""
    try:
        # dynamic import to avoid errors outside Colab
        from google.colab import drive
        print("[drive] Mounting Google Drive...")
        drive.mount('/content/drive', force_remount=False)
        # ensure folder exists
        os.makedirs(DRIVE_FOLDER, exist_ok=True)
        print(f"[drive] Using folder: {DRIVE_FOLDER}")
    except Exception as e:
        print(f"[drive] Not running in Colab or mount failed: {e}")
        # ensure local folder fallback
        os.makedirs(DRIVE_FOLDER, exist_ok=True)
        print(f"[drive] Created/using folder: {DRIVE_FOLDER}")

# -------------------------
# Core: parse messages into (link, filename) pairs
# -------------------------
def parse_message_text(text: str):
    """
    Accepts:
     - "Custom Name | LINK"
     - "LINK" (just link)
    Returns:
     - (link, filename_or_None)
    """
    if "|" in text:
        parts = text.split("|", 1)
        name = clean_filename(parts[0])
        link = parts[1].strip()
        if link.startswith("http") and link.endswith(".m3u8"):
            return link, f"{name}.mp4"
        else:
            return None, None
    else:
        link = text.strip()
        if link.startswith("http") and link.endswith(".m3u8"):
            return link, None
    return None, None

# -------------------------
# Prepare environment: install aria2c & ffmpeg if missing
# -------------------------
def ensure_tools():
    # aria2c
    try:
        subprocess.run(["aria2c", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        print("[installer] aria2c not found, installing...")
        install_package("aria2")

    # ffmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        print("[installer] ffmpeg not found, installing...")
        install_package("ffmpeg")

# -------------------------
# Download & merge workflow
# -------------------------
def download_and_merge(m3u8_url: str, out_path: str):
    """
    Returns True on success, False on failure.
    """
    try:
        # fetch playlist
        r = requests.get(m3u8_url, timeout=30)
        r.raise_for_status()
        m3u8_content = r.text

        with open("playlist.m3u8", "w", encoding="utf-8") as f:
            f.write(m3u8_content)

        base_url = m3u8_url.rsplit("/", 1)[0] + "/"
        chunk_urls = []
        for line in m3u8_content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("http"):
                chunk_urls.append(line)
            else:
                chunk_urls.append(base_url + line)

        if not chunk_urls:
            raise RuntimeError("No chunks found in playlist")

        # write chunks file for aria2
        with open("chunks.txt", "w", encoding="utf-8") as f:
            for url in chunk_urls:
                f.write(url + "\n")

        print(f"[download] {len(chunk_urls)} chunks found.")

        # call aria2c
        aria_cmd = ["aria2c"] + ARIA2_OPTIONS + ["-i", "chunks.txt", "-d", "chunks"]
        safe_run(aria_cmd)

        # merge chunks (cat)
        # Using shell to expand wildcard
        safe_run("cat chunks/*.ts > temp.ts", shell=True)

        # ffmpeg merge to mp4
        safe_run(["ffmpeg", "-y", "-i", "temp.ts", "-c", "copy", "-bsf:a", "aac_adtstoasc", "output.mp4"])

        # copy to out_path
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        shutil.copy("output.mp4", out_path)
        return True

    except Exception as e:
        print(f"[error] download_and_merge failed: {e}")
        return False
    finally:
        # cleanup in any case
        try:
            if os.path.exists("chunks"):
                shutil.rmtree("chunks")
            for f in ["temp.ts", "playlist.m3u8", "chunks.txt", "output.mp4"]:
                if os.path.exists(f):
                    os.remove(f)
        except Exception:
            pass

# -------------------------
# Main loop (queue + retries)
# -------------------------
def main_loop():
    ensure_tools()
    mount_drive_if_colab()

    # ignore old updates: set last_update_id to the latest existing update_id (if any)
    try:
        updates = get_updates()
        if updates.get("result"):
            last_update_id = updates["result"][-1]["update_id"]
        else:
            last_update_id = None
    except Exception:
        last_update_id = None

    send_telegram_message("🤖 Bot is active! Send new M3U8 links. Format for custom name: 'Lecture | https://.../file.m3u8'")

    queue = []  # list of (link, filename_or_None)

    while True:
        # fetch updates
        try:
            updates = get_updates()
            for msg in updates.get("result", []):
                update_id = msg.get("update_id")
                if last_update_id is None or update_id > last_update_id:
                    last_update_id = update_id
                    if "message" in msg and "text" in msg["message"]:
                        text = msg["message"]["text"]
                        link, fname = parse_message_text(text)
                        if link:
                            queue.append((link, fname))
                            pos = len(queue)
                            send_telegram_message(f"🆕 Link added to queue: {link}\n📌 Position: {pos} | Total Pending: {len(queue)}")
        except Exception as e:
            print(f"[telegram] getUpdates error: {e}")

        # process queue
        if queue:
            m3u8_url, custom_filename = queue.pop(0)
            if custom_filename:
                filename = custom_filename
            else:
                filename = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

            dest_path = os.path.join(DRIVE_FOLDER, filename)
            send_telegram_message(f"🎯 Starting download: {m3u8_url}\nQueue Remaining: {len(queue)}")
            print(f"[queue] Downloading -> {m3u8_url}")

            success = False
            for attempt in range(1, MAX_RETRIES + 1):
                send_telegram_message(f"📦 Found chunks. Attempt {attempt}/{MAX_RETRIES}...")
                ok = download_and_merge(m3u8_url, dest_path)
                if ok:
                    send_telegram_message(f"🎉 Download & merge complete! Saved as {filename}\nQueue Remaining: {len(queue)}")
                    print(f"[success] Saved to {dest_path}")
                    success = True
                    break
                else:
                    send_telegram_message(f"⚠️ Attempt {attempt} failed for link: {m3u8_url}")
                    time.sleep(5)

            if not success:
                send_telegram_message(f"❌ All attempts failed for link: {m3u8_url}\nQueue Remaining: {len(queue)}")

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("Exiting on user interrupt.")
        send_telegram_message("🛑 Bot stopped manually.")
    except Exception as ex:
        print(f"Fatal error: {ex}")
        try:
            send_telegram_message(f"❌ Bot stopped due to error: {ex}")
        except Exception:
            pass
        raise
