# Raspberry Pi utility - launches Chromium in fullscreen for camera feed
# Used during early RPi-based hardware testing (later switched to laptop)

import time
import subprocess
import requests

def check_connection(url):
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def open_chromium(url):
    subprocess.Popen(["chromium-browser", "--start-fullscreen", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

url = "http://192.168.43.1:8080"

while not check_connection(url):
    print("Trying to connect...")
    open_chromium(url)
    time.sleep(5)  # Wait before retrying

print("Connected successfully!")
