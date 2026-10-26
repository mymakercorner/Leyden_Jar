# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project

The **Leyden Jar** is an open-source (GPLv3) capacitive-sense keyboard controller PCB replacing the Xwhatsit
controller in Model F Labs' Brand New Model F and Beam Spring keyboards. Author: Rico (mymakercorner).

- Current released hardware: **Revision 3** (RP2040).
- Work in progress: **Leyden Jar V2**, a new design based on the **RP2350**, developed on branch
  `leyden-jar-v2-work` (base branch: `main`).
- Firmware lives elsewhere (vial-qmk fork, `leyden_jar` branch:
  https://github.com/mymakercorner/vial-qmk/tree/leyden_jar, code in `keyboards/leyden_jar/`: PIO matrix scan,
  DAC, IO expander, custom PS/2 *device* driver in `ps2/`). Diagnostic tool:
  https://github.com/mymakercorner/Leyden_Jar_Diagnostic_Tool. This repo is hardware only.

## Repository layout

```
pcb/leyden_jar_controller/      KiCad project of the controller (Leyden_Jar.kicad_pro/.kicad_sch/.kicad_pcb)
  library/Leyden_Jar.kicad_sym  project symbol library  (sym-lib-table -> ${KIPRJMOD}/library/...)
  library/Leyden_Jar.pretty/    project footprint library (fp-lib-table)
  library/3d_models/            STEP models (SnapEDA, CC BY-SA 4.0 + Design Exception, see README)
pcb/ps2_at_daughterboard/       KiCad project of the PS/2 AT daughterboard (ps2_pcb.*), Rev 2
production_files/<project>/     JLCPCB outputs (GERBER-*.zip, BOM-*.csv, CPL-*.csv) and bom/ibom.html
images/                         renders used by README.md
```

`*-backups/`, `.history/`, `jlcpcb/` (inside pcb/), and the daughterboard `.kicad_prl` are git-ignored.

## Tooling and rules for KiCad files

- KiCad version: **KiCad 10**. Both the controller and the daughterboard projects (schematic, PCB and project
  files) are in KiCad 10 format.
- Modify KiCad projects **only through the Konnect MCP tools** (load the `konnect` skill first, then the relevant
  `kicad-schematic` / `kicad-pcb` / `kicad-library` / `kicad-review` / `kicad-manufacture` skill). Never hand-edit
  `.kicad_sch` / `.kicad_pcb` / `.kicad_sym` / `.kicad_mod` with text tools. Reading them for analysis is fine.
- `~*.lck` files mean the project is open in KiCad right now. Don't write to a project while the user has it open
  without telling them; their next save would overwrite the change. Lock files are git-ignored (`~*.lck`).
- Prefer project-local library parts (`Leyden_Jar:` prefix). New symbols/footprints go into the project libraries,
  not the global KiCad libraries, so the repo stays self-contained.
- On the Rev 3 schematic, some symbol `lib_id`s are the original parts (e.g. `MCP4725`, `ADP7142`, `W25Q32JVSS`) while
  the **Value** field and BOM carry the actually fitted part (MCP4716, ADP122, W25Q16JVUX). Trust Value/BOM/LCSC.
- Manufacturing target is **JLCPCB** assembly; every assembled part needs an LCSC number. Buttons and the two 2x3
  headers are deliberately left out of the assembly BOM.

## Rev 3 design reference (starting point for V2)

4-layer board: F.Cu carries the critical matrix traces with no vias, In1.Cu is solid GND, In2.Cu/B.Cu carry power
and non-critical routing. Matrix traces are curved to limit reflections when columns are pulsed. Keep this
philosophy in V2. Passives are 0402 except the bulk caps/ferrite bead (0805) and fuse (1210).

Main parts (LCSC): RP2040 (C2040), W25Q16JVUXIQ 2 MB QSPI flash USON-8 (C2843335), 12 MHz crystal 3225 (C9002),
ADP122AUJZ-3.3 LDO (C143910), USBLC6-2SC6 ESD (C7519), mSMD110 polyfuse (C70102), CBW201209U121T ferrite (C139186),
HRO TYPE-C-31-M-12 USB-C (C165948), 2x LMV339 quad comparator (C273648), MCP4716 10-bit I2C DAC for the comparator
threshold `V_REF` (C110057), PCA9557PW I2C IO expander for LEDs/PS2_ENABLE (C141380).

Sense chain: `A_ROWn` (matrix connector J2) -> LMV339 comparator vs `V_REF` (from the DAC) -> `ROWn` into the MCU.
Columns are driven directly from MCU GPIO through 1k series resistors. Scanning runs entirely in PIO.

RP2040 GPIO map (all 30 GPIOs used):

| GPIO | Net | GPIO | Net |
|---|---|---|---|
| 0-7 | ROW0-ROW7 (comparator outputs) | 18-27 | COL8-COL17 |
| 8-15 | COL0-COL7 | 28 | SOLENOID_ENABLE |
| 16 | SDA (DAC, IO expander, J3) | 29 | SOLENOID_PULSE |
| 17 | SCL | | |

Connectors:
- **J1** USB-C (USB 2.0, 5.1k CC pull-downs, 27R series on D+/D-).
- **J2** 33-pin switch matrix connector: GND, rows `A_ROW0-7`, `LED0-2` (from the PCA9557), and the 18 columns
  (each `COLn` reaches J2 through its 1k series resistor, so the J2-side nets are unnamed).
- **J3** 2x3 SWD/I2C: 1 GND, 2 3V3, 3 SWCLK, 4 SDA, 5 SWIO, 6 SCL.
- **J4** 2x3 Ext (solenoid / PS2 daughterboard): 1 +5V, 2 SOLENOID_ENABLE, 3 PS2_ENABLE (from PCA9557), 4 SOLENOID_PULSE,
  5 3V3, 6 GND. The PS/2 AT daughterboard plugs in here; solenoid and PS/2 can't be used together.
- 4 RUN/BOOTSEL buttons (B3U-1000P top-press or B3U-3000P side-press, top and bottom side), not populated by default.

## V2 (RP2350B) target design

"V2" here is called **Rev 4** in the external plan document the user shares (read-only, kept outside this repo).
The plan is a starting point, and technical changes are expected during development. When the plan and good
engineering disagree, raise it with the user rather than silently following either.

Planned hardware changes from Rev 3:
- **RP2350B** (QFN-80, 48 GPIO) replaces the RP2040. The **PCA9557 IO expander is removed**; its LEDs and PS2_ENABLE
  move to native GPIOs. The I2C bus stays for the MCP4716 threshold DAC (and J3).
- Add the RP2350 core **switching regulator** (external inductor plus VREG_LX / VREG_FB / VREG_PGND / VREG_AVDD
  network per the Raspberry Pi hardware design guide). It is a new noise source next to the capacitive front end,
  so keep it away from the matrix traces and LMV339s.
- Flash: **ZD25Q64DSIGT**, 8 MB, SOP-8 208 mil (replaces the 2 MB USON-8 W25Q16).
- The matrix sense chain (LMV339s, DAC, ROW0-7 on GP0-7, COL0-15) stays untouched.
- New through-hole breakouts: TFT display (SPI), rotary encoder (with RC debounce: 10k pull-up + 100 nF per phase),
  free expansion pins, and a 3-pin split header (5V, GND, DATA) left of the USB-C connector.
- Possibly remove the through-hole row/column resistors in the 33-pin ribbon cable area (to be confirmed).

Planned GPIO map (Rev 3 assignments unchanged unless listed):

| GPIO | Net | Notes |
|---|---|---|
| 0-7 | ROW0-7 | unchanged |
| 8-15, 18-25 | COL0-15 | unchanged |
| 16 / 17 | SDA / SCL | unchanged (DAC, J3) |
| 26 / 27 | SOLENOID_ENABLE / SOLENOID_PULSE | moved from 28/29; also PS/2 clock/data via J4 |
| 28 / 29 | COL16 / COL17 | moved from 26/27 |
| 30 / 31 | TFT SPI_SCK / SPI_MOSI | SPI1 SCK / TX |
| 33 / 34 / 35 | TFT CS / DC / RST | |
| 36 | TFT_BLK | backlight, PWM |
| 37 / 38 / 39 | ENCODER_A / ENCODER_B / ENCODER_BUTTON | |
| 40 | PS2_ENABLE | was PCA9557 |
| 42 / 43 / 44 | LED1 / LED2 / LED3 | were PCA9557 LED0-2 (on J2) |
| 45 | UART_DATA | split link, half-duplex PIO serial |
| 32, 41, 46, 47 | free | through holes for expansion |

Points to verify while implementing (against the RP2350 datasheet / hardware design guide / QMK docs):
- Inductor value: the plan says 2.2 µH; check the value the current hardware design guide specifies.
- GP33 is an SPI0 function pin, not SPI1. That's harmless if CS is driven as a plain GPIO. No free pin in the
  plan has the SPI1 RX function, so the display must work with MISO unused.
- PIO blocks see a 32-GPIO window (base 0 or 16). Current firmware: PIO0 = matrix scanner, PIO1 = PS/2
  (its program fills all 32 instructions). The split serial on GP45 therefore needs **PIO2** with GPIOBASE 16,
  not PIO0 as the plan's firmware section says.
- PS/2 pin order is free: the firmware patches the `ps2out` program to wait on an absolute GPIO (`0x2080 | pin`),
  so clock = data - 1 on J4 works. On the RP2350 that index is relative to the PIO's GPIOBASE, which is fine
  while PS/2 stays below GP32.
- Moving COL16/17 to GP28/29 requires changing the `col_16_17` PIO pin base (26 today) in `pio_matrix_scan.c`.
- `PS2_ENABLE` (GP40) is actually a daughterboard **presence-detect input**: about 3.3 V from a divider on the
  daughterboard, with a 47k pull-down (R50) on this board. With erratum E9, a 47k pull-down may not pull the pad
  back low after it was high. Use about 8.2k or less, or confirm the silicon stepping.
- Split 5V header: avoid back-feeding VBUS between two boards that are both on USB (diode or power-path), and add
  ESD protection and a series resistor on DATA on this board too.
- GPIO LED drive current (PCA9557 previously sank the LED current), and the 3V3 budget of the ADP122 (300 mA) with
  the TFT and backlight added.
- **Erratum RP2350-E9** on input pads: the ROW inputs have 10k external pull-ups to 3V3, which should be safe.
  Check the silicon stepping JLCPCB stocks.

Still open (confirm with the user): whether V2 lives in a new `pcb/` folder or replaces the Rev 3 project in place,
and board outline/connector placement compatibility with existing Model F / Beam Spring cases.

## Git conventions

- Commit messages are prefixed with a tag: `[feature]`, `[bugfix]`, `[fix]`, `[cleanup]`, followed by a short sentence
  ending in a period. Example: `[bugfix] Wrong 0402 casings instead of 0603.`
- Commit or push only when the user asks.
- When a revision is released, regenerate `production_files/` and update `README.md` (feature list, revision history,
  images).
