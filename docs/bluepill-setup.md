# Blue Pill (STM32F103) as a Klipper ADXL345 board

Do this once, before installing the toggle.

## 1. Wiring (ADXL345 is 3.3 V only)

| Blue Pill | ADXL345 |
|-----------|---------|
| 3V3       | VCC (and CS pull-up if your board needs it) |
| GND       | GND     |
| PA4       | CS      |
| PA5       | SCL/SCK |
| PA6       | SDO/MISO|
| PA7       | SDA/MOSI|

USB to the Raspberry Pi goes on the Blue Pill's USB port (PA11/PA12).

## 2. Build and flash Klipper

```bash
cd ~/klipper && make menuconfig
```

- Micro-controller: `STMicroelectronics STM32`
- Processor model: `STM32F103`
- Bootloader offset: `No bootloader` (or `28KiB` if you flash a bootloader)
- Communication interface: `USB (on PA11/PA12)`

```bash
make clean && make
```

Flash `out/klipper.bin` (ST-Link, or `dfu-util`/serial with the BOOT0 jumper
set to 1, then back to 0). After a reset:

```bash
ls /dev/serial/by-id/      # usb-Klipper_stm32f103xb_...
```

## 3. Install the toggle

The installer auto-detects a single `stm32f103` board and writes its path to
`adxl345.cfg`. Otherwise: `ADXL_MCU_SERIAL=/dev/serial/by-id/usb-Klipper_... bash install.sh`

## 4. Calibrate

```
ENABLE_ADXL        # firmware_restart with the sensor included
ACCELEROMETER_QUERY
SHAPER_CALIBRATE
DISABLE_ADXL       # when you are done
```
