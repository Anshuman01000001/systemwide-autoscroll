# autoscroll

Hold a mouse button, scroll continuously. Built for reading long-strip content (manhwa, webtoons, etc.) without manually spinning a mouse wheel — works on **Wayland**, where most existing auto-scroll tools (which rely on X11) don't.

## How it works

Most input automation tools (`xdotool`, etc.) only work on X11. This script instead:

- Listens for raw button press/release events via **`python-evdev`**, reading directly from `/dev/input`, which works regardless of compositor (X11 or Wayland).
- Simulates mouse wheel scroll events via **`ydotool`**, which also works on both X11 and Wayland since it operates through the kernel's `uinput` interface.

While your chosen button is held down, the script repeatedly fires scroll-wheel ticks. Release the button and it stops.

## Requirements

- Linux with a Wayland (or X11) compositor
- [`ydotool`](https://github.com/ReimuNotMoe/ydotool) + the `ydotoold` daemon
- [`python-evdev`](https://github.com/gvalkov/python-evdev)
- Membership in the `input` group (to read input devices without root)

### Install (Arch Linux)

```bash
sudo pacman -S ydotool python-evdev
sudo usermod -aG input $USER
```

Log out and back in for the group change to take effect.

> On other distros, install `ydotool` and `python-evdev` (or `pip install evdev --break-system-packages`) via your package manager of choice.

## Quick start (recommended)

Use the included `run.sh` wrapper — it starts `ydotoold` for you (only if it isn't already running), waits for it to be ready, launches `autoscroll.py`, and cleans up the daemon when you quit:

```bash
chmod +x run.sh
./run.sh
```

This still asks for your `sudo` password to start `ydotoold` the first time in a session, but you won't need a second terminal or to remember the daemon command yourself.

## Manual setup (alternative)

If you'd rather manage things yourself instead of using `run.sh`:

**1. Start the `ydotoold` daemon** (does the actual input simulation):

```bash
sudo ydotoold --socket-path="$HOME/.ydotool_socket" --socket-own="$(id -u):$(id -g)"
```

Leave this running in a terminal.

**2. Point `ydotool` at that socket:**

```bash
export YDOTOOL_SOCKET="$HOME/.ydotool_socket"
```

**3. Run the script directly:**

```bash
python3 autoscroll.py
```

## Configuring your trigger button

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

Then run via `./run.sh` (or `python3 autoscroll.py` if you set up `ydotoold` manually).

## Configuration reference

| Variable | Description |
|---|---|
| `DEVICE_PATH` | Path to your mouse's input device (`/dev/input/eventX`) |
| `TRIGGER_CODE` | evdev button/key code that starts/stops scrolling |
| `SCROLL_DIRECTION` | `-1` scrolls down, `1` scrolls up |
| `SCROLL_INTERVAL` | Delay (seconds) between scroll ticks — lower is faster |

## A note on using the actual middle mouse button as the trigger

If your trigger button is the physical middle button, you may notice it still performs its normal OS-level action (e.g. "paste primary selection") in addition to triggering scroll, since this script only listens to the device — it doesn't intercept/suppress the event system-wide. The simplest workaround is picking a different physical button (a side button, etc.) that doesn't have a conflicting default action.

## Troubleshooting

- **Permission denied on `/dev/input/eventX`** — confirm you're in the `input` group (`groups $USER`) and have logged out/in since adding yourself.
- **Script runs but nothing scrolls** — make sure `ydotoold` is running (or use `run.sh`, which handles this) and `YDOTOOL_SOCKET` is exported in the same terminal you're running the script from.
- **Wrong device picked up** — re-run `--list` to double check the device path; some mice expose multiple event nodes (one for movement, one for buttons/extra keys).

## Limitations

- Scrolling is tick-based (discrete wheel events), not a smooth pixel-by-pixel glide.
- Scrolls whatever window currently has input focus, system-wide — not limited to one app.
- The trigger button's normal default action (if it has one) isn't suppressed — see the note above.

## License

MIT
