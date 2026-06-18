#!/usr/bin/env python3
"""
Hold-a-button-to-autoscroll, for Wayland.

Setup (Arch):
  sudo pacman -S ydotool python-evdev
  sudo usermod -aG input $USER     # then log out & back in
  sudo systemctl enable --now ydotool.service   # or run ydotoold manually, see below

If there's no ydotool.service unit on your system, just run the daemon by hand
in another terminal first:
  sudo ydotoold --socket-path="$HOME/.ydotool_socket" --socket-own="$(id -u):$(id -g)"
  export YDOTOOL_SOCKET="$HOME/.ydotool_socket"   # put this in your shell rc too

Usage:
  1. Find your mouse's device path:
       python3 autoscroll.py --list
  2. Find the exact code for the button you want to hold (press it while this runs):
       python3 autoscroll.py --probe /dev/input/eventX
  3. Edit DEVICE_PATH and TRIGGER_CODE below to match, then just run:
       python3 autoscroll.py
"""

import subprocess
import sys
import threading
import time

import evdev
from evdev import InputDevice, ecodes, list_devices

# ---------------- CONFIG ----------------
DEVICE_PATH = "/dev/input/event2"     # set after running --list
TRIGGER_CODE = 274                    # the button you'll hold down, set after --probe
SCROLL_DIRECTION = -1                 # -1 = scroll down, 1 = scroll up
SCROLL_INTERVAL = 0.05                # seconds between scroll ticks (lower = faster)
# -----------------------------------------

stop_flag = threading.Event()


def list_input_devices():
    for path in list_devices():
        dev = InputDevice(path)
        print(f"{path}\t{dev.name}")


def probe_device(path):
    dev = InputDevice(path)
    print(f"Listening on {dev.name} ({path}) -- press the button, Ctrl+C to quit")
    for event in dev.read_loop():
        if event.type == ecodes.EV_KEY:
            name = ecodes.BTN.get(event.code) or ecodes.KEY.get(event.code) or event.code
            state = {1: "DOWN", 0: "UP", 2: "HOLD"}.get(event.value, event.value)
            print(f"code={event.code}  name={name}  state={state}")


def scroll_loop():
    while not stop_flag.is_set():
        subprocess.run(
            ["ydotool", "mousemove", "-w", "--", "0", str(SCROLL_DIRECTION)],
            check=False,
        )
        time.sleep(SCROLL_INTERVAL)


def main():
    dev = InputDevice(DEVICE_PATH)
    print(f"Watching {dev.name} for trigger code {TRIGGER_CODE}. Ctrl+C to quit.")
    scroll_thread = None
    for event in dev.read_loop():
        if event.type == ecodes.EV_KEY and event.code == TRIGGER_CODE:
            if event.value == 1 and (scroll_thread is None or not scroll_thread.is_alive()):
                stop_flag.clear()
                scroll_thread = threading.Thread(target=scroll_loop, daemon=True)
                scroll_thread.start()
            elif event.value == 0:
                stop_flag.set()


if __name__ == "__main__":
    try:
        if "--list" in sys.argv:
            list_input_devices()
        elif "--probe" in sys.argv:
            idx = sys.argv.index("--probe")
            probe_device(sys.argv[idx + 1])
        else:
            main()
    except KeyboardInterrupt:
        stop_flag.set()
        print("\nStopped.")
