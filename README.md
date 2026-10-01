# ADXL345 + Blue Pill Toggle برای Klipper

فعال/غیرفعال‌کردن `[include adxl345.cfg]` در `printer.cfg` با یک دکمه (HelixScreen، Mainsail، Fluidd یا Console)، بدون ویرایش دستی. مناسب وقتی سنسور شتاب (ADXL345 روی Blue Pill) فقط برای کالیبراسیون input shaper وصل می‌شود.

## نصب (چند دستور ساده)

روی دستگاهی که Klipper و Moonraker دارد (Raspberry Pi و...)، با کاربر معمولی (نه root):

```bash
cd ~
git clone https://github.com/Novin3dp/ADXL345-klipper-bluepill.git
cd ADXL345-klipper-bluepill
bash install.sh
```

همین. نصب‌کننده:

- مسیر `printer.cfg` را خودکار پیدا می‌کند (`~/printer_data/config` یا `~/klipper_config`)؛ برای مسیر دیگر: `ADXL_PRINTER_CFG=/path/printer.cfg bash install.sh`
- قبل از هر ویرایش از `printer.cfg` بکاپ می‌گیرد (`~/adxl-toggle-backups/`)
- ماکروها را در فایل جدا `adxl_toggle.cfg` می‌گذارد و فقط یک خط `[include adxl_toggle.cfg]` **قبل از بلوک `SAVE_CONFIG`** در `printer.cfg` اضافه می‌کند (Klipper هرچه بعد از آن باشد را بازنویسی می‌کند؛ خطوطی که از نصب قبلی آن پایین مانده‌اند خودکار بالا منتقل می‌شوند)
- اگر `adxl345.cfg` ندارید، از روی قالب می‌سازد (برد Blue Pill را خودکار پیدا می‌کند؛ در غیر این صورت `ADXL_MCU_SERIAL=...` بدهید)
- خط `#[include adxl345.cfg]` را غیرفعال اضافه می‌کند و سرویس systemd را نصب و Klipper را ری‌استارت می‌کند

اگر هنوز Blue Pill را فلش و سیم‌کشی نکرده‌اید: [docs/bluepill-setup.md](docs/bluepill-setup.md)

## استفاده

در Console یا با ویجت‌های HelixScreen ([راهنما](docs/helixscreen-widget.md)):

| ماکرو | کار |
|-------|-----|
| `ENABLE_ADXL`  | فعال‌کردن include + `firmware_restart` |
| `DISABLE_ADXL` | غیرفعال‌کردن include + `firmware_restart` |
| `ADXL_STATUS`  | گزارش وضعیت (بدون ری‌استارت) |

حین پرینت یا پاز، هر دو ماکرو رد می‌شوند (`ADXL_TOGGLE_REFUSED`) تا پرینت قطع نشود.

## نحوه‌ی کار

```
ENABLE_ADXL / DISABLE_ADXL  ->  RESPOND "ADXL_TOGGLE_EVENT:..."
      ▼
adxl_toggle_watcher.py (polling از Moonraker gcode_store)
      ├─ بررسی وضعیت پرینت
      ├─ بکاپ + ویرایش خط include در printer.cfg
      └─ firmware_restart و انتظار تا آماده‌شدن Klipper
```

## عیب‌یابی

```bash
systemctl status adxl-toggle-watcher.service --no-pager
journalctl -u adxl-toggle-watcher.service -n 50 --no-pager
```

- **`ADXL_TOGGLE_REFUSED`**: پرینتر در حال پرینت/پاز است.
- **Klipper بعد از Enable خطای MCU می‌دهد**: سنسور را وصل کنید و `serial:` را در `adxl345.cfg` بررسی کنید (`ls /dev/serial/by-id/`).

## حذف

```bash
cd ~/ADXL345-klipper-bluepill && bash uninstall.sh
```

سرویس، `adxl_toggle.cfg` و include آن حذف می‌شوند؛ `adxl345.cfg` دست‌نخورده می‌ماند.

## توسعه

```bash
python3 -m unittest discover -s tests -v
```

مجوز: MIT
