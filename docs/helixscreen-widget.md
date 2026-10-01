# ADXL345 toggle as HelixScreen widgets

This project installs three Klipper macros (in `adxl_toggle.cfg`): `ENABLE_ADXL`, `DISABLE_ADXL`,
and `ADXL_STATUS`. Add widgets for them by hand, once:

1. Open HelixScreen's home dashboard editor.
2. Add a **Favorite Macro** widget bound to `ENABLE_ADXL`.
3. Add a second **Favorite Macro** widget bound to `DISABLE_ADXL`.
4. (Optional) add a third bound to `ADXL_STATUS` if you want a quick way to
   ask for the current state without opening the Console.
5. Turning **Require confirmation** on for these is a reasonable choice,
   since each tap triggers a `firmware_restart`.

Tapping `ENABLE_ADXL` uncomments `[include adxl345.cfg]` in `printer.cfg`
and restarts the firmware; `DISABLE_ADXL` comments it back out and restarts
again. Both refuse to run while a print is active or paused.

## Why there are two widgets instead of one

An earlier, simpler design used a single `TOGGLE_ADXL` macro. This project
ships the two-macro (`ENABLE_ADXL` / `DISABLE_ADXL`) version instead,
because it is the version that has actually been tested end-to-end on
real hardware. If you prefer a single toggle button, you can merge the two
macros yourself in `klipper/adxl_toggle.cfg` -- the watcher script reacts
to the same `ADXL_TOGGLE_EVENT:ENABLE` / `ADXL_TOGGLE_EVENT:DISABLE`
console markers either way, so a single macro could alternate between
`RESPOND MSG="ADXL_TOGGLE_EVENT:ENABLE"` and `...DISABLE` based on a
Klipper variable if you want that instead.

## No live on/off indicator in HelixScreen

HelixScreen's "LED Settings -> Macro Devices" only recognizes real
`neopixel`/`dotstar`/`led`/WLED objects, not an arbitrary `output_pin`
(tested on real hardware), so this project does not add a status pin.
Use the `ADXL_STATUS` macro (or the Console) to check the current state.
