# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project

The **Leyden Jar** is an open-source (GPLv3) capacitive-sense keyboard controller PCB replacing the Xwhatsit
controller in Model F Labs' Brand New Model F and Beam Spring keyboards. Author: Rico (mymakercorner).

- Current released hardware: **Revision 3** (RP2040).
- Work in progress: **Leyden Jar V2**, a new design based on the **RP2350**, developed on branch
  `leyden-jar-v2-work` (base branch: `main`).
- Firmware lives elsewhere (vial-qmk fork, `leyden_jar` branch:
  https://github.com/mymakercorner/vial-qmk/tree/leyden_jar). Diagnostic tool:
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

## V2 (RP2350) design notes

Things that differ from the RP2040 and must be handled in the new schematic. Check every one against the current
RP2350 datasheet and hardware design guide before relying on it:

- Package choice: **RP2350A** (QFN-60, 30 GPIO) keeps the Rev 3 pin budget; **RP2350B** (QFN-80, 48 GPIO) frees pins
  for more columns or for removing the I2C IO expander. Not decided yet.
- The core supply comes from an on-chip **switching regulator** (needs an external inductor and specific
  layout around VREG_LX / VREG_FB / VREG_PGND / VREG_AVDD), not the RP2040's linear regulator. Its layout needs
  care because it is a new noise source next to the capacitive sense front end.
- Same 12 MHz crystal, QSPI flash, USB, and SWD concept as RP2040; pin numbers and decoupling differ.
- The RP2350 has a second QSPI chip select available on a GPIO (e.g. for optional PSRAM).
- **Erratum RP2350-E9** (GPIO input with pull-down can latch at an intermediate voltage on early steppings):
  relevant for the ROW inputs fed by the LMV339 open-drain outputs. Check which silicon stepping JLCPCB stocks.
- Firmware impact: the vial-qmk port must move to the RP2350 (QMK/ChibiOS support and PIO program changes).

Open decisions should be confirmed with the user, not assumed. Examples: RP2350A vs B, whether V2 lives in a new
`pcb/` folder or replaces the Rev 3 project in place, flash size, keeping the PCA9557/LMV339/MCP4716 parts, and
board outline/connector placement compatibility with existing Model F / Beam Spring cases.

## Git conventions

- Commit messages are prefixed with a tag: `[feature]`, `[bugfix]`, `[fix]`, `[cleanup]`, followed by a short sentence
  ending in a period. Example: `[bugfix] Wrong 0402 casings instead of 0603.`
- Commit or push only when the user asks.
- When a revision is released, regenerate `production_files/` and update `README.md` (feature list, revision history,
  images).
