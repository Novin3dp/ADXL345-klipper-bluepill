#!/usr/bin/env bash
# Removes the watcher service and the include of adxl_toggle.cfg.
# adxl345.cfg and your sensor config are never touched.
set -euo pipefail

INSTALL_DIR="/opt/novin3dp-adxl-toggle"
[[ "$(id -u)" -ne 0 ]] || { echo "Run as a normal user."; exit 1; }
USER_HOME="$(getent passwd "${USER:-$(id -un)}" | cut -d: -f6)"
PRINTER_CFG="${ADXL_PRINTER_CFG:-}"
if [[ -z "$PRINTER_CFG" ]]; then
    for c in "$USER_HOME/printer_data/config/printer.cfg" "$USER_HOME/klipper_config/printer.cfg"; do
        [[ -f "$c" ]] && { PRINTER_CFG="$c"; break; }
    done
fi
sudo -v

sudo systemctl disable --now adxl-toggle-watcher.service 2>/dev/null || true
sudo rm -f /etc/systemd/system/adxl-toggle-watcher.service
sudo systemctl daemon-reload
sudo rm -rf "$INSTALL_DIR"

if [[ -n "$PRINTER_CFG" && -f "$PRINTER_CFG" ]]; then
    mkdir -p "$USER_HOME/adxl-toggle-backups"
    cp -a "$PRINTER_CFG" "$USER_HOME/adxl-toggle-backups/printer.cfg.$(date +%Y%m%d-%H%M%S).preuninstall.bak"
    sed -i '/^\s*\[include adxl_toggle\.cfg\]\s*$/d' "$PRINTER_CFG"
    rm -f "$(dirname "$PRINTER_CFG")/adxl_toggle.cfg"
fi

echo "Removed. Restart Klipper (sudo systemctl restart klipper) to drop the macros."
echo "adxl345.cfg and its include line in printer.cfg were left as-is; backups are in ~/adxl-toggle-backups/."
