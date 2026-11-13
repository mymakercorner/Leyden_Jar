# Porting the RP2350 support to the Leyden Jar Vial fork

Nov 13, 2026 · Rico

## Summary

The early RP2350 support in emolitor's QMK fork can be brought into the Leyden Jar Vial fork
(`mymakercorner/vial-qmk`, branch `leyden_jar`) without waiting for official QMK or Vial support. The workable path is
to **cherry-pick its 15 commits** onto a new branch, not to merge QMK `develop` into Vial. Vial's own changes don't
touch the files involved, so the risk is integration and testing, not design.

- The 15 commits touch 48 files: 29 apply cleanly or are new, 4 meet trivial Vial edits, 15 meet small QMK changes
  made since the Vial fork's base (about 120 lines of drift in total).
- Three QMK pieces outside the 15 commits are needed. The `halconf.h` template update is mandatory: without it the
  build stops with `#error`.
- The Leyden Jar keyboard code (PIO matrix scan, PS/2 device driver) uses pico-sdk calls and must move to the ChibiOS
  PIO API: about 1-2 days of mechanical work.
- Rev 3 settings stored in flash should survive the change (same EEPROM location and format), to be checked on a board.
- Nothing was built: no ARM toolchain is installed on this PC. This is a reading of both git histories and the files.

## The two code bases

| | Leyden Jar Vial fork | emolitor RP2350 branch |
| --- | --- | --- |
| Repository, branch | `mymakercorner/vial-qmk`, `leyden_jar` (head `761cb1c1b7`, 24 Oct 2026) | `emolitor/qmk_firmware`, `em-rp2350` (head `431ed9ade0`, 22 Jul 2026) |
| QMK base | QMK master of 21 Mar 2025 (`6a947fa534`, via Vial's `merge-2025-03-22`), then `origin/vial` merged on 1 Jun 2025 | QMK develop of 19 Jul 2026 (`e2fd609ebf`) |
| ChibiOS | `qmk/ChibiOS` `2365f84`, HAL config 8.4, RT config 7.0 | `chibios-upstream/chibios` master `61f5799`, HAL config 9.1, RT config 8.0 |
| ChibiOS-Contrib | `3ac181e` | `5a9ad82` |
| pico-sdk | used (`a3398d8`) | removed |

The gap between the two QMK bases is **1,102 QMK commits**. Upstream vial-qmk's last QMK merge is `merge-2025-06-21`,
so it is not close to emolitor's base either. Vial carries 169 commits of its own outside `keyboards/`, mostly in
QMK core files (`action.c`, `keyboard.c`, `quantum.c`, `dynamic_keymap.c`, `process_*`). Merging QMK 2026 into Vial
would mean redoing a full Vial maintainer merge; cherry-picking the 15 commits avoids those files entirely.

## Files touched by the 15 commits

Each file was compared three ways: Vial fork head, QMK at the Vial base (`6a947fa534`), and QMK at emolitor's base
(`e2fd609ebf`). `keyboards/handwired/onekey/rp2350*` test boards are left out.

| Status | Files | Work |
| --- | --- | --- |
| Apply cleanly | 22: `.gitmodules`, RP2040 board configs (`GENERIC_RP_RP2040`, `GENERIC_PROMICRO_RP2040`, `QMK_BLOK`, `QMK_PM2040`), `_wait.h`, `wait.c`, `hardware_id.c`, the serial and WS2812 vendor drivers, deleted pico-sdk files (`pico_sdk_shims.c`, `RP2040_FLASH_TIMECRIT.ld`, ...), docs | none |
| New in the series | 7: `GENERIC_RP_RP2350` board, `bootloaders/rp2350.c`, `vendors/RP/RP2350.mk`, `docs/platformdev_rp2350.md` | none |
| Edited by Vial | 4: `builddefs/common_features.mk` (Vial build rules), `platforms/chibios/bootloader.mk` and `data/schemas/keyboard.jsonschema` (Vial's `vibl` STM32F103 bootloader), `wear_leveling_efl_config.h` (Vial's 8 kB default) | trivial: the edits are in different places from the series' changes |
| Changed by QMK since 2025-03 | 15: `mcu_selection.mk` (STM32G0x1 block added), `chibios_config.h`, `platform.mk`, `vendors/RP/RP2040.mk`, `drivers/analog.c`, `boards/common/configs/chconf.h`, `bootloaders/rp2040.c`, `flash.mk`, the RP PS/2 host driver, `wear_leveling_rp2040_flash.c`, `wear_leveling_drivers.h`, `lib/python/qmk/constants.py`, two docs, the `lib/chibios` pin | small: about 120 lines of unrelated context drift |

Vial changes nothing in `tmk_core/` or in the RP platform code. Its only platform additions are the STM32F103 `vibl`
bootloader and board, and none of its `quantum/` code is MCU-specific. Vial's GUI talks to the keyboard over raw HID,
which the change doesn't touch.

## Prerequisites outside the 15 commits

1. **`platforms/chibios/boards/common/configs/halconf.h`, HAL config 9.1** (QMK #26079, "ChibiOS, ChibiOS-Contrib
   updates (redux)", Apr 2026). Mandatory: the new ChibiOS `hal.h` checks `#if !defined(_CHIBIOS_HAL_CONF_VER_9_1_)`
   and the Vial fork's template is 8.4, so the build stops with `#error`. The series itself only updates `chconf.h`
   to RT 8.0.
2. **ChibiOS-Contrib at `5a9ad82`** (same QMK change). The Vial fork's `3ac181e` predates HAL 9.1; RP builds no longer
   use Contrib's RP port, but compiling the old Contrib against the new HAL is a risk.
3. **`quantum/compiler_support.h`** (QMK #25274, May 2025, 15 lines). The series' `chibios_config.h` includes it.
4. Optional: QMK #24776, "Fix flash wear leveling sector calculation" (Dec 2025). With the RP flash descriptor sized to
   `RP_FLASH_SIZE` it lands the EEPROM in the same place with or without the fix.

QMK's other ChibiOS-side changes between the two bases (USB endpoint and Plover HID work, SPI lock fix, I2C transmit/
receive, suspend wake-up) are features or fixes, not requirements of the new ChibiOS. The ChibiOS update itself
(#26079) only touched board configs, `platform.mk` and the submodules.

## Leyden Jar keyboard code to port

The pico-sdk is no longer built, so every pico-sdk call in `keyboards/leyden_jar/` must move to the ChibiOS RP HAL.
All of it is mechanical.

| Code | pico-sdk use | ChibiOS replacement |
| --- | --- | --- |
| `pio_matrix_scan.c`, `col_0_7_pio.pio.h`, `col_8_15_pio.pio.h`, `col_16_17_pio.pio.h` | `hardware/pio.h`, `pio_add_program`, `pio_sm_config` helpers, `clock_get_hz`, `pio_sm_put_blocking` / `pio_sm_get_blocking`, `pio_gpio_init` | `pioProgramLoad`, `pioSmConfig*X` builders, `pioSmConfigSetFrequencyX`, blocking put/get helpers in `rp_pio.h`, `palSetLineMode` with `PAL_MODE_ALTERNATE_PIO0`. The PIO programs themselves stay unchanged |
| `ps2/ps2_platform_chibios.c`, `ps2/ps2out.pio.h`, `ps2/hid_to_ps2.h` | `hardware/pio.h`, `PIO` and `uint` types, `pio0`/`pio1` | `rp_pio_block_t` / `rp_pio_sm_t`, `RP_PIO1_BLOCK` |
| `ps2/ps2_glue.c` | `time_us_64()`, `gpio_get()` | `TIMER->TIMERAWL` (RP2040) / `TIMER0->TIMERAWL` (RP2350) or the ChibiOS system time, `palReadLine` |
| `pio_matrix_scan.c`, `ps2_platform_chibios.c` | `hal_lld_peripheral_unreset(RESETS_ALLREG_PIOx)` | `rp_peripheral_unreset`, or nothing: `pioSmAlloc` releases the block from reset |

- **PIO allocation:** claim state machines and instruction memory through `pioSmAlloc` / `pioProgramLoad`. QMK's own
  PIO drivers (for example the split serial on PIO1 in `impostor_full`) now use that bookkeeping, and raw register use
  would collide with it. `ps2out` still fills all 32 instructions of PIO1.
- **Unchanged:** the keyboard-level `mcuconf.h` / `halconf.h` overrides (`RP_I2C_USE_I2C0`, `HAL_USE_I2C` keep their
  names); `WEAR_LEVELING_DRIVER = rp2040_flash` in the `rules.mk` files (remapped to `embedded_flash` with a notice);
  `WEAR_LEVELING_BACKING_SIZE 32768`; the `wait_us()` calls (now a busy wait on the 1 MHz timer).

## Rev 3 compatibility

| Item | Current Vial fork | After the change | Effect |
| --- | --- | --- | --- |
| EEPROM location | top of 2 MB (`PICO_FLASH_SIZE_BYTES`, pico-sdk `pico.h`) minus the backing size | top of `RP_FLASH_SIZE`, 2 MB by default on RP2040, minus the backing size | same place |
| EEPROM format | wear-leveling, 2-byte writes | same, `BACKING_STORE_WRITE_SIZE` 2 | stored keymaps and settings kept |
| System clock | 125 MHz (pico-sdk `clocks_init`, PLL 1500/6/2) | 125 MHz (ChibiOS RP2040 default, same PLL) | unchanged |
| Boot stage 2 | QMK W25Q080 image, SSI divider 4 | same image | unchanged |
| Crystal start-up delay | pico-sdk default multiplier 1 | ChibiOS default `RP_XOSC_STARTUP_DELAY_MULTIPLIER` 6 | longer wait, harmless |

To check on a Rev 3 board before any release: settings kept across the update, matrix detection, PS/2, split serial,
DAC/IO expander on I2C, the RUN and BOOTSEL paths.

## Risks

- **Untested combination:** QMK core of March 2025, ChibiOS master of 2026 and RP platform files written against QMK
  of July 2026. Nobody else builds this mix, so a few compile fixes are likely.
- **Other keyboards in the fork:** non-Leyden keyboards (STM32, the Vial `vibl` board) may stop building with the new
  ChibiOS. Keep the work on its own branch (for example `leyden_jar_v2`) and keep releasing Rev 3 firmware from
  `leyden_jar` until the new base is tested.
- **Upstream moves:** emolitor's branch hasn't moved since 22 Jul 2026 and its author calls it a proof of concept
  ([qmk/qmk_firmware#25881](https://github.com/qmk/qmk_firmware/issues/25881)). Official QMK support waits for the
  next ChibiOS major release. When QMK or Vial ship their own RP2350 support, the branch will need a rebase; the
  Leyden Jar code ported to the ChibiOS PIO API carries over.
- **Future Vial syncs:** pulling newer vial-qmk will conflict in the same platform files each time.
- **Build environment:** none on this PC yet (QMK MSYS or WSL with the ARM toolchain).
- **RP2350B:** the series only covers the RP2350A package. V2 still needs the QFN-80 board definition, GP31-47 pin
  names and PIO2 with the GP16-47 window for the split serial on GP45 (estimated 3-5 days, see the review of the
  emolitor branch).

## Suggested order

1. Set up a build environment and build the current `leyden_jar` branch as a baseline.
2. Create the new branch from `leyden_jar`. Bring in the `halconf.h` 9.1 template, the ChibiOS-Contrib pin and
   `compiler_support.h`, then cherry-pick the 15 commits and resolve the conflicts listed above.
3. Port the Leyden Jar PIO and PS/2 code to the ChibiOS PIO API. Build Rev 3 and test it on a board.
4. Add the RP2350B pieces (board, pin names, PIO2 for the split serial) and bring up the V2 prototype.

## Sources

- Leyden Jar Vial fork: [mymakercorner/vial-qmk, branch `leyden_jar`](https://github.com/mymakercorner/vial-qmk/tree/leyden_jar)
- emolitor's RP2350 branch: [emolitor/qmk_firmware, branch `em-rp2350`](https://github.com/emolitor/qmk_firmware/tree/em-rp2350)
- ChibiOS: [chibios-upstream/chibios](https://github.com/chibios-upstream/chibios)
- Upstream Vial: [vial-kb/vial-qmk](https://github.com/vial-kb/vial-qmk)
- QMK: [issue #25881, RP2350 support](https://github.com/qmk/qmk_firmware/issues/25881); pull requests #26079 (ChibiOS
  update), #25274 (`compiler_support.h`), #24776 (wear-leveling sector fix)
