#!/usr/bin/env bash
# ADXL345 (Blue Pill) include toggle for Klipper -- installer.
#
# Usage:  bash install.sh [--yes]
# Env:    ADXL_PRINTER_CFG   path to printer.cfg (auto-detected otherwise)
#         ADXL_MCU_SERIAL    /dev/serial/by-id/... of the Blue Pill (optional)
set -euo pipefail

REPO_URL="https://github.com/Novin3dp/ADXL345-klipper-bluepill"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/opt/novin3dp-adxl-toggle"
SERVICE="adxl-toggle-watcher.service"
ASSUME_YES=0
[[ "${1:-}" == "--yes" || "${1:-}" == "-y" ]] && ASSUME_YES=1

log()  { printf '\n[ADXL Toggle] %s\n' "$*"; }
fail() { echo "ERROR: $*" >&2; exit 1; }

[[ "$(id -u)" -ne 0 ]] || fail "Run as a normal user, not root (sudo is used when needed)."
USER_NAME="${USER:-$(id -un)}"
USER_HOME="$(getent passwd "$USER_NAME" | cut -d: -f6)"
BACKUP_DIR="$USER_HOME/adxl-toggle-backups"

# ---- locate printer.cfg ----------------------------------------------------
PRINTER_CFG="${ADXL_PRINTER_CFG:-}"
if [[ -z "$PRINTER_CFG" ]]; then
    for c in "$USER_HOME/printer_data/config/printer.cfg" "$USER_HOME/klipper_config/printer.cfg"; do
        [[ -f "$c" ]] && { PRINTER_CFG="$c"; break; }
    done
fi
[[ -n "$PRINTER_CFG" && -f "$PRINTER_CFG" ]] || fail "printer.cfg not found.
Re-run with: ADXL_PRINTER_CFG=/path/to/printer.cfg bash install.sh"
CFG_DIR="$(dirname "$PRINTER_CFG")"

command -v systemctl >/dev/null || fail "systemd is required."
sudo -v

# ---- warn if the local clone is behind upstream -----------------------------
if [[ -d "$PROJECT_DIR/.git" ]] && command -v git >/dev/null 2>&1 \
   && git -C "$PROJECT_DIR" fetch --quiet 2>/dev/null; then
    behind="$(git -C "$PROJECT_DIR" rev-list --count 'HEAD..@{u}' 2>/dev/null || echo 0)"
    if [[ "$behind" -gt 0 ]]; then
        echo "WARNING: this clone is $behind commit(s) behind upstream; run 'git pull' first."
        if [[ $ASSUME_YES -eq 0 && -t 0 ]]; then
            read -r -p "Continue with the local copy anyway? [y/N] " a
            [[ "$a" =~ ^[Yy]$ ]] || exit 1
        fi
    fi
fi

command -v python3 >/dev/null || { log "Installing python3"; sudo apt-get update && sudo apt-get install -y python3; }

# ---- backup ----------------------------------------------------------------
log "Backing up printer.cfg"
mkdir -p "$BACKUP_DIR"
cp -a "$PRINTER_CFG" "$BACKUP_DIR/printer.cfg.$(date +%Y%m%d-%H%M%S).preinstall.bak"

# ---- macros (separate file, included from printer.cfg) ----------------------
log "Installing macros -> $CFG_DIR/adxl_toggle.cfg"
cp "$PROJECT_DIR/klipper/adxl_toggle.cfg" "$CFG_DIR/adxl_toggle.cfg"
# Klipper rewrites everything below "SAVE_CONFIG", so includes must go ABOVE it.
# (This also moves lines from an older install out of the SAVE_CONFIG block.)
python3 "$PROJECT_DIR/scripts/adxl_toggle_watcher.py" --ensure-lines "$PRINTER_CFG" \
    "[include adxl_toggle.cfg]"

# ---- adxl345.cfg (only created if missing) ----------------------------------
if [[ ! -f "$CFG_DIR/adxl345.cfg" ]]; then
    SERIAL="${ADXL_MCU_SERIAL:-}"
    if [[ -z "$SERIAL" ]]; then
        mapfile -t found < <(ls /dev/serial/by-id/*stm32f103* 2>/dev/null || true)
        [[ ${#found[@]} -eq 1 ]] && SERIAL="${found[0]}"
    fi
    log "Creating $CFG_DIR/adxl345.cfg from the example template"
    sed "s#__ADXL_MCU_SERIAL__#${SERIAL:-REPLACE_WITH_/dev/serial/by-id/usb-Klipper_stm32f103xb_...}#" \
        "$PROJECT_DIR/klipper/adxl345.cfg.example" > "$CFG_DIR/adxl345.cfg"
    [[ -n "$SERIAL" ]] || echo "NOTE: Blue Pill not detected. Edit 'serial:' in $CFG_DIR/adxl345.cfg" \
        "(find it with: ls /dev/serial/by-id/)."
else
    log "adxl345.cfg already exists; leaving it untouched."
fi

# ---- include line (added DISABLED if absent) --------------------------------
log "Ensuring '[include adxl345.cfg]' exists in printer.cfg (added disabled if absent)"
python3 "$PROJECT_DIR/scripts/adxl_toggle_watcher.py" --ensure-lines "$PRINTER_CFG" \
    "#[include adxl345.cfg]"

# ---- watcher + service ------------------------------------------------------
log "Installing watcher service"
sudo mkdir -p "$INSTALL_DIR/scripts"
sudo cp "$PROJECT_DIR/scripts/adxl_toggle_watcher.py" "$INSTALL_DIR/scripts/"
sudo chmod 755 "$INSTALL_DIR/scripts/adxl_toggle_watcher.py"
sudo chown -R "$USER_NAME:$USER_NAME" "$INSTALL_DIR"
sed -e "s#__ADXL_USER__#$USER_NAME#g" \
    -e "s#__ADXL_USER_HOME__#$USER_HOME#g" \
    -e "s#__ADXL_PRINTER_CFG__#$PRINTER_CFG#g" \
    -e "s#__ADXL_BACKUP_DIR__#$BACKUP_DIR#g" \
    "$PROJECT_DIR/services/$SERVICE" | sudo tee "/etc/systemd/system/$SERVICE" >/dev/null
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE" >/dev/null
sudo systemctl restart "$SERVICE"

# ---- restart klipper so the macros load -------------------------------------
if systemctl is-active --quiet klipper 2>/dev/null; then
    log "Restarting Klipper to load the new macros"
    sudo systemctl restart klipper
else
    echo "NOTE: restart Klipper manually to load the new macros."
fi

cat <<MSG

Done.  Backups:  $BACKUP_DIR
Run ENABLE_ADXL / DISABLE_ADXL / ADXL_STATUS from the console or bind them to
HelixScreen "Favorite Macro" widgets (docs/helixscreen-widget.md).
Status:  systemctl status $SERVICE --no-pager
Project: $REPO_URL
MSG
