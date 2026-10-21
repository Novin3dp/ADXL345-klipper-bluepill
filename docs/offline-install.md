# نصب آفلاین

پیش‌نیاز روی Pi: Klipper + Moonraker، `python3` و `sudo` (روی Raspberry Pi OS / MainsailOS به‌صورت پیش‌فرض هست). اینترنت لازم نیست.

## ۱. دانلود (روی کامپیوتر دارای اینترنت)

از صفحه‌ی ریپازیتوری: **Code → Download ZIP** (فایل `ADXL345-klipper-bluepill-main.zip`).

## ۲. انتقال به Pi

```bash
scp ADXL345-klipper-bluepill-main.zip pi@<IP-پرینتر>:~
```

(یا با فلش USB کپی کنید.)

## ۳. استخراج

```bash
cd ~
unzip ADXL345-klipper-bluepill-main.zip     # اگر unzip نبود: python3 -m zipfile -e ADXL345-klipper-bluepill-main.zip .
cd ADXL345-klipper-bluepill-main
```

## ۴. فلش Blue Pill (فقط بار اول)

سیم‌کشی و تنظیمات `make menuconfig` در [bluepill-setup.md](bluepill-setup.md). سپس:

```bash
cd ~/klipper && make clean && make
# فلش out/klipper.bin با ST-Link یا dfu-util
ls /dev/serial/by-id/        # باید usb-Klipper_stm32f103xb_... دیده شود
```

## ۵. نصب

```bash
cd ~/ADXL345-klipper-bluepill-main
bash install.sh --yes
```

اگر بردتان خودکار شناسایی نشد یا `printer.cfg` در مسیر پیش‌فرض نیست:

```bash
ADXL_MCU_SERIAL=/dev/serial/by-id/usb-Klipper_stm32f103xb_XXXX \
ADXL_PRINTER_CFG=/path/to/printer.cfg bash install.sh --yes
```

## ۶. بررسی

```bash
systemctl status adxl-toggle-watcher.service --no-pager
grep -n "include adxl" ~/printer_data/config/printer.cfg   # باید بالای SAVE_CONFIG باشند
```

اگر `adxl345.cfg` را خودکار ساخته است، مقدار `serial:` داخل آن را بررسی کنید.

## ۷. استفاده

ابتدا سنسور را وصل کنید، سپس در Console:

```
ENABLE_ADXL
ACCELEROMETER_QUERY
SHAPER_CALIBRATE
DISABLE_ADXL
```

## حذف

```bash
cd ~/ADXL345-klipper-bluepill-main && bash uninstall.sh
```
