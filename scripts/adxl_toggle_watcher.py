#!/usr/bin/env python3
"""
Novin3dp ADXL345 include toggle watcher.

Watches Moonraker's gcode_store for RESPOND messages emitted by the
ENABLE_ADXL / DISABLE_ADXL / ADXL_STATUS Klipper macros, then:

  - ENABLE_ADXL  -> uncomments "[include adxl345.cfg]" in printer.cfg,
                    then firmware_restart and waits for Klipper to be ready.
  - DISABLE_ADXL -> comments out the same line, firmware_restart, waits.
  - ADXL_STATUS  -> RESPONDs with the current state (no restart).

Refuses to touch printer.cfg or trigger a firmware_restart while a print
is active or paused, to avoid aborting a running job. A timestamped
backup of printer.cfg is written before every edit.
"""
import json
import os
import re
import shutil
import time
import urllib.request
import urllib.parse

USER_HOME = os.environ.get("ADXL_USER_HOME", os.path.expanduser("~"))
PRINTER_CFG = os.environ.get(
    "ADXL_PRINTER_CFG", os.path.join(USER_HOME, "printer_data/config/printer.cfg")
)
BACKUP_DIR = os.environ.get(
    "ADXL_BACKUP_DIR", os.path.join(USER_HOME, "adxl-toggle-backups")
)
INCLUDE_LINE = "[include adxl345.cfg]"
MOONRAKER_BASE = os.environ.get("ADXL_MOONRAKER_URL", "http://localhost:7125")
GCODE_STORE_URL = f"{MOONRAKER_BASE}/server/gcode_store?count=10"
GCODE_SCRIPT_URL = f"{MOONRAKER_BASE}/printer/gcode/script"
FIRMWARE_RESTART_URL = f"{MOONRAKER_BASE}/printer/firmware_restart"
PRINTER_INFO_URL = f"{MOONRAKER_BASE}/printer/info"
PRINT_STATS_URL = f"{MOONRAKER_BASE}/printer/objects/query?print_stats"

ENABLE_MARKER = "ADXL_TOGGLE_EVENT:ENABLE"
DISABLE_MARKER = "ADXL_TOGGLE_EVENT:DISABLE"
STATUS_MARKER = "ADXL_STATUS_REQUEST"

POLL_INTERVAL = 0.5
READY_TIMEOUT = 30


SAVE_CONFIG_RE = re.compile(r"^#\*#\s*<-+\s*SAVE_CONFIG\s*-+>")
ADXL_INCLUDE_RE = re.compile(r"^#?\s*" + re.escape(INCLUDE_LINE) + r"\s*$")


def save_config_index(lines):
    """Index of the SAVE_CONFIG marker line, or len(lines) if absent."""
    for i, line in enumerate(lines):
        if SAVE_CONFIG_RE.match(line.strip()):
            return i
    return len(lines)


def insert_before_save_config(lines, new_line):
    """Klipper rewrites everything after SAVE_CONFIG, so user lines must go before it."""
    idx = save_config_index(lines)
    block = [new_line + "\n"]
    if idx < len(lines):
        block.append("\n")  # keep a blank line before the marker
    elif lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    lines[idx:idx] = block
    return lines


def http_get(url, timeout=3):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.load(response)


def http_post(url, timeout=5):
    req = urllib.request.Request(url, method="POST", data=b"")
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read()


def run_gcode(script):
    qs = urllib.parse.urlencode({"script": script})
    http_post(f"{GCODE_SCRIPT_URL}?{qs}")


def respond(message):
    # Quote-escape for a G-code string literal.
    safe = message.replace('"', "'")
    try:
        run_gcode(f'RESPOND MSG="{safe}"')
    except Exception as exc:
        print(f"respond() failed: {exc}", flush=True)


def is_printing():
    try:
        data = http_get(PRINT_STATS_URL)
        state = data.get("result", {}).get("status", {}).get("print_stats", {}).get("state", "")
        return state in ("printing", "paused")
    except Exception as exc:
        print(f"is_printing() check failed, assuming NOT printing: {exc}", flush=True)
        return False


def backup_printer_cfg():
    if not os.path.isfile(PRINTER_CFG):
        return None
    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    dest = os.path.join(BACKUP_DIR, f"printer.cfg.{stamp}.bak")
    shutil.copy2(PRINTER_CFG, dest)
    return dest


def include_is_active():
    if not os.path.isfile(PRINTER_CFG):
        return None
    with open(PRINTER_CFG, "r") as f:
        for line in f:
            stripped = line.strip()
            if stripped == INCLUDE_LINE:
                return True
            if re.match(r"^#\s*" + re.escape(INCLUDE_LINE) + r"\s*$", stripped):
                return False
    return None  # line not present at all


def _matcher(text):
    if text.lstrip("#") == INCLUDE_LINE:
        return lambda t: bool(ADXL_INCLUDE_RE.match(t))
    return lambda t: t == text


def normalize_lines(lines, wanted):
    """Make sure each entry of `wanted` exists exactly once ABOVE SAVE_CONFIG.
    A plain copy found below the marker is moved up (keeping its text, so a
    commented include stays commented); otherwise the entry is added as given."""
    result = list(lines)
    for text in wanted:
        match = _matcher(text)
        idx = save_config_index(result)
        head, tail = result[:idx], result[idx:]
        moved = [l for l in tail if not l.startswith("#*#") and match(l.strip())]
        tail = [l for l in tail if l not in moved]
        result = head + tail
        if any(match(l.strip()) for l in head):
            continue
        insert_before_save_config(result, moved[-1].strip() if moved else text)
    return result


def write_cfg(new_lines):
    backup_path = backup_printer_cfg()
    if backup_path:
        print(f"Backed up printer.cfg -> {backup_path}", flush=True)
    tmp_path = PRINTER_CFG + ".tmp"
    with open(tmp_path, "w") as f:
        f.writelines(new_lines)
    os.replace(tmp_path, PRINTER_CFG)


def set_include(enable):
    if not os.path.isfile(PRINTER_CFG):
        print(f"printer.cfg not found at {PRINTER_CFG}", flush=True)
        return False

    with open(PRINTER_CFG, "r") as f:
        original = f.readlines()

    present = any(ADXL_INCLUDE_RE.match(l.strip()) for l in original if not l.startswith("#*#"))
    if not present and not enable:
        print(f"'{INCLUDE_LINE}' not present in printer.cfg; nothing to disable.", flush=True)
        return False

    # Pull the line above SAVE_CONFIG (adds it there if missing), then toggle it.
    lines = normalize_lines(original, [INCLUDE_LINE])
    target = INCLUDE_LINE if enable else "#" + INCLUDE_LINE
    lines = [target + "\n" if ADXL_INCLUDE_RE.match(l.strip()) and not l.startswith("#*#") else l
             for l in lines]

    if lines == original:
        print(f"ADXL include already {'enabled' if enable else 'disabled'}; no change.", flush=True)
        return True
    write_cfg(lines)
    return True


def wait_for_ready(timeout=READY_TIMEOUT):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            info = http_get(PRINTER_INFO_URL, timeout=2)
            if info.get("result", {}).get("state") == "ready":
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def handle_toggle(enable):
    if is_printing():
        respond("ADXL_TOGGLE_REFUSED: printer is printing or paused")
        print("Refusing ADXL toggle: a print is active or paused.", flush=True)
        return

    label = "ENABLE" if enable else "DISABLE"
    print(f"Handling {label}_ADXL ...", flush=True)
    if not set_include(enable):
        respond(f"ADXL_TOGGLE_FAILED: could not update printer.cfg for {label}")
        return

    try:
        http_post(FIRMWARE_RESTART_URL)
    except Exception as exc:
        print(f"firmware_restart request failed: {exc}", flush=True)
        respond("ADXL_TOGGLE_FAILED: firmware_restart request failed")
        return

    if wait_for_ready():
        respond(f"ADXL_TOGGLE_DONE: {label}")
        print(f"{label}_ADXL complete, printer ready.", flush=True)
    else:
        print("Timed out waiting for printer to become ready after firmware_restart.", flush=True)
        respond("ADXL_TOGGLE_WARNING: restart timed out, check printer state")


def handle_status_request():
    active = include_is_active()
    if active is True:
        respond("ADXL_STATUS: ENABLED")
    elif active is False:
        respond("ADXL_STATUS: DISABLED")
    else:
        respond("ADXL_STATUS: NOT_CONFIGURED")


def main():
    print("Novin3dp ADXL345 toggle watcher running.", flush=True)
    # Do not replay old console messages from before this process started.
    last_seen_time = time.time()

    while True:
        try:
            data = http_get(GCODE_STORE_URL)
            entries = data.get("result", {}).get("gcode_store", [])
            newest = last_seen_time
            for entry in sorted(entries, key=lambda item: item.get("time", 0)):
                timestamp = float(entry.get("time", 0) or 0)
                message = str(entry.get("message", ""))
                if timestamp > last_seen_time:
                    if ENABLE_MARKER in message:
                        handle_toggle(True)
                    elif DISABLE_MARKER in message:
                        handle_toggle(False)
                    elif STATUS_MARKER in message:
                        handle_status_request()
                newest = max(newest, timestamp)
            last_seen_time = newest
        except Exception as exc:
            print(f"watcher error: {exc}", flush=True)
        time.sleep(POLL_INTERVAL)


def ensure_lines_cli(path, lines):
    """install.sh helper: ensure `lines` exist above SAVE_CONFIG in `path`."""
    global PRINTER_CFG
    PRINTER_CFG = path
    with open(path) as f:
        original = f.readlines()
    updated = normalize_lines(original, lines)
    if updated != original:
        with open(path, "w") as f:
            f.writelines(updated)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2 and sys.argv[1] == "--ensure-lines":
        ensure_lines_cli(sys.argv[2], sys.argv[3:])
    else:
        main()
