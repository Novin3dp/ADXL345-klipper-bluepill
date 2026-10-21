# نصب آفلاین

پیش‌نیاز روی Pi: Klipper + Moonraker، `python3` و `sudo` (روی Raspberry Pi OS / MainsailOS به‌صورت پیش‌فرض هست). اینترنت لازم نیست.

## ۱. دانلود (روی کامپیوتر دارای اینترنت)

از صفحه‌ی ریپازیتوری: **Code → Download ZIP** (فایل `ADXL345-klipper-bluepill-main.zip`).

## ۲. انتقال به Pi

کاربر Pi: `biqu` (پوشه‌ی home: `/home/biqu`). یکی از سه راه زیر را انجام دهید.

### راه الف: فلش USB (بدون شبکه)

ZIP را در ریشه‌ی فلش بریزید، فلش را به USB خود Pi بزنید، با PuTTY (آی‌پی پرینتر، پورت 22، کاربر `biqu`) وصل شوید:

```bash
lsblk                                  # پارتیشن فلش را پیدا کنید، معمولاً sda1
sudo mkdir -p /mnt/usb
sudo mount /dev/sda1 /mnt/usb
ls /mnt/usb                            # باید فایل ZIP دیده شود
cp /mnt/usb/ADXL345-klipper-bluepill-main.zip /home/biqu/
sudo umount /mnt/usb                   # سپس فلش را بکشید
```

فلش FAT32 یا exFAT باشد (NTFS ممکن است mount نشود).

### راه ب: pscp (همراه PuTTY)، در Command Prompt ویندوز

مسیر دارای فاصله (`hello hamid`) باید داخل کوتیشن باشد:

```
pscp "C:\Users\hello hamid\Downloads\ADXL345-klipper-bluepill-main.zip" biqu@<IP-پرینتر>:/home/biqu/
```

### راه ج: WinSCP

با آی‌پی پرینتر و کاربر `biqu` وصل شوید و ZIP را با drag & drop داخل `/home/biqu` بیندازید.

## ۳. استخراج (در ترمینال PuTTY)

```bash
cd /home/biqu
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
cd /home/biqu/ADXL345-klipper-bluepill-main
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
grep -n "include adxl" /home/biqu/printer_data/config/printer.cfg   # باید بالای SAVE_CONFIG باشند
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
cd /home/biqu/ADXL345-klipper-bluepill-main && bash uninstall.sh
```
