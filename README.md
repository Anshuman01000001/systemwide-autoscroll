# autoscroll

Hold a mouse button, scroll continuously. Built for reading long-strip content (manhwa, webtoons, etc.) without manually spinning a mouse wheel — works on **Wayland**, where most existing auto-scroll tools (which rely on X11) don't.

## How it works

Most input automation tools (`xdotool`, etc.) only work on X11. This script instead:

- **Grabs your mouse's input device exclusively** via `python-evdev`, reading raw events straight from `/dev/input` — works regardless of compositor (X11 or Wayland), and means the trigger button (e.g. the middle button) never reaches the rest of the system. That's what stops things like middle-click-paste from firing while the script runs.
- **Recreates a virtual mouse via `uinput`**, forwarding every event except the trigger button untouched — so normal movement, clicks, and the native scroll wheel keep working exactly as before.
- Writes synthetic scroll-wheel ticks directly to that virtual device while the trigger button is held.

Release the button and scrolling stops; the trigger button itself is simply swallowed and does nothing else.

## Requirements

- Linux with a Wayland (or X11) compositor
- [`python-evdev`](https://github.com/gvalkov/python-evdev)
- Membership in the `input` group, plus write access to `/dev/uinput`

### Install (Arch Linux)

```bash
sudo pacman -S python-evdev
sudo usermod -aG input $USER

# allow the input group to write to /dev/uinput (needed to create the
# virtual passthrough mouse):
echo 'KERNEL=="uinput", GROUP="input", MODE="0660"' | sudo tee /etc/udev/rules.d/99-uinput.rules
sudo udevadm control --reload-rules && sudo udevadm trigger
```

Log out and back in (or reboot) for the group change to take effect.

> On other distros, install `python-evdev` (or `pip install evdev --break-system-packages`) via your package manager of choice, and adjust the udev rule path as needed.

## Usage

**1. List your input devices** to find your mouse:

```bash
python3 autoscroll.py --list
```

```
/dev/input/event3   My Mechanical Keyboard
/dev/input/event5   Logitech G502
```

**2. Probe the device** to find the code for the button you want to use as a trigger:

```bash
python3 autoscroll.py --probe /dev/input/event5
```

Press the button physically — the script will print its code and name, e.g.:

```
code=276  name=BTN_EXTRA  state=DOWN
code=276  name=BTN_EXTRA  state=UP
```

**3. Edit the config block** at the top of `autoscroll.py`:

```python
DEVICE_PATH = "/dev/input/event5"     # from step 1
TRIGGER_CODE = ecodes.BTN_EXTRA       # from step 2
SCROLL_DIRECTION = -1                 # -1 = down, 1 = up
SCROLL_INTERVAL = 0.05                # seconds between ticks; lower = faster
```

**4. Run it:**

```bash
python3 autoscroll.py
```

Hold the configured button to scroll; release to stop. `Ctrl+C` to quit the script entirely.

## Configuration reference

| Variable | Description |
|---|---|
| `DEVICE_PATH` | Path to your mouse's input device (`/dev/input/eventX`) |
| `TRIGGER_CODE` | evdev button/key code that starts/stops scrolling |
| `SCROLL_DIRECTION` | `-1` scrolls down, `1` scrolls up |
| `SCROLL_INTERVAL` | Delay (seconds) between scroll ticks — lower is faster |

## Troubleshooting

- **Permission denied on `/dev/input/eventX` or `/dev/uinput`** — confirm you're in the `input` group (`groups $USER`), that the `99-uinput.rules` udev rule was applied, and that you've logged out/in since adding yourself to the group.
- **Mouse seems "dead" while the script runs** — check the terminal for errors; if the script crashed without reaching the `finally` block, the grab is released automatically once the process exits, but if it somehow doesn't, unplug/replug the mouse (or log out and back in) to reset it.
- **Wrong device picked up** — re-run `--list` to double check the device path; some mice expose multiple event nodes (one for movement, one for buttons/extra keys).

## Limitations

- Scrolling is tick-based (discrete wheel events), not a smooth pixel-by-pixel glide.
- Scrolls whatever window currently has input focus, system-wide — not limited to one app.
- While running, this script has exclusive control of the mouse device; if it's killed forcefully (e.g. `kill -9`) the grab is still released by the kernel once the file descriptor closes, but expect a brief hiccup in mouse responsiveness during a crash.

## License

MIT
