#!/usr/bin/env bash
#
# Starts ydotoold (if it isn't already running) and then launches
# autoscroll.py. Cleans up the daemon on exit if this script started it.
set -euo pipefail

SOCKET_PATH="$HOME/.ydotool_socket"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/autoscroll.py"

YDOTOOLD_PID=""

cleanup() {
    if [[ -n "$YDOTOOLD_PID" ]]; then
        echo "Stopping ydotoold (pid $YDOTOOLD_PID)..."
        sudo kill "$YDOTOOLD_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT INT TERM

if pgrep -x ydotoold > /dev/null 2>&1; then
    echo "ydotoold already running, reusing it."
else
    echo "Starting ydotoold..."
    sudo ydotoold --socket-path="$SOCKET_PATH" --socket-own="$(id -u):$(id -g)" &
    YDOTOOLD_PID=$!

    # wait up to ~4s for the socket to actually appear
    for _ in $(seq 1 20); do
        [[ -S "$SOCKET_PATH" ]] && break
        sleep 0.2
    done
    if [[ ! -S "$SOCKET_PATH" ]]; then
        echo "ydotoold socket never appeared, aborting." >&2
        exit 1
    fi
fi

export YDOTOOL_SOCKET="$SOCKET_PATH"
python3 "$PYTHON_SCRIPT" "$@"
