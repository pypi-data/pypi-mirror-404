import sounddevice as sd
import numpy as np
import psutil
import os
import time
import subprocess
import sys

# --- CONFIGURATION ---
THRESHOLD = 0.5    # Volume threshold for a "knock" (Increase if too sensitive)
COOLDOWN = 1.5     # Seconds to wait after triggering
KNOCK_WINDOW = 1.0 # Max seconds between two knocks (Double knock timing)
BROWSERS = ["chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "opera.exe"]
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OFFICE_FILE = os.path.join(SCRIPT_DIR, "data", "Work_Report_2024.xlsx")
# ---------------------

class BossSensor:
    def __init__(self):
        self.last_knock_time = 0
        self.trigger_cooldown_until = 0

    def hide_evidence(self):
        print("\n" + "!"*40)
        print("!!! BOSS DETECTED! PANIC MODE ON !!!")
        print("!"*40 + "\n")
        
        # 1. Kill Browsers immediately
        print("Closing browsers...")
        for proc in psutil.process_iter(['name']):
            try:
                name = proc.info['name'].lower()
                if any(browser in name for browser in BROWSERS):
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # 2. Open "Boring" Excel
        print(f"Opening {os.path.basename(OFFICE_FILE)}...")
        try:
            if os.path.exists(OFFICE_FILE):
                os.startfile(OFFICE_FILE)
            else:
                # Fallback: Just open Excel app
                subprocess.Popen(["cmd", "/c", "start", "excel"], shell=True)
        except Exception as e:
            # Fallback: Just open Excel app
            subprocess.Popen(["cmd", "/c", "start", "excel"], shell=True)
            
        self.trigger_cooldown_until = time.time() + 10 # 10s cooldown after trigger

    def audio_callback(self, indata, frames, time_info, status):
        if status:
            print(f"Error: {status}", file=sys.stderr)
        
        # Calculate maximum amplitude in this chunk
        amplitude = np.max(np.abs(indata))
        
        # Uncomment the line below to debug sensitivity:
        # print(f"Level: {amplitude:.4f}", end='\r')

        if amplitude > THRESHOLD:
            current_time = time.time()
            
            if current_time < self.trigger_cooldown_until:
                return

            time_since_last = current_time - self.last_knock_time
            
            # Print knock detection
            print(f"\nKnock detected! (Volume: {amplitude:.2f})")

            # Check for double knock within window
            if 0.15 < time_since_last < KNOCK_WINDOW:
                self.hide_evidence()
                self.last_knock_time = 0 # Reset
            else:
                self.last_knock_time = current_time
                print("First knock... waiting for second...")

    def start(self):
        print("========================================")
        print("           SHADOW KILL          ")
        print("========================================")
        print(f"Threshold: {THRESHOLD}")
        print(f"Target file: {OFFICE_FILE}")
        print("Listening for a QUICK DOUBLE KNOCK on the desk...")
        print("----------------------------------------")
        print("Press Ctrl+C to stop.")
        
        try:
            with sd.InputStream(callback=self.audio_callback, channels=1, samplerate=44100):
                while True:
                    time.sleep(0.1)
        except Exception as e:
            print(f"Could not start audio stream: {e}")
            print("Check if your microphone is connected and allowed.")

def main():
    """Main entry point for the shadowkill command."""
    sensor = BossSensor()
    try:
        sensor.start()
    except KeyboardInterrupt:
        print("\nExiting. Stay safe!")

if __name__ == "__main__":
    main()
