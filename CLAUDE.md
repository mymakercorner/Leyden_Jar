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
- Manufacturing target is **JLCPCB** assembly; every assembled part needs an LCSC number. Choose parts from the
  JLCPCB assembly library (jlcpcb.com/parts, in stock), not the wider LCSC catalog. Buttons and the two 2x3
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
- **Core supply: external 1.1 V LDO, on-chip switching regulator unused** (EMI decision, deviates from the plan).
  Per RP2350 datasheet section 6.3.7, "External core supply with on-chip regulator disabled": no inductor, VREG_FB
  to GND, and VREG_VIN + VREG_AVDD still powered (they feed POR/brownout). The internal regulator still starts at
  power-up (~400 uA) until firmware writes 1 to the VREG register's HIZ field. VREG_PGND to GND (pin description:
  "tie to ground externally"), VREG_LX unconnected. Core voltage is fixed, which is fine: no overclocking is planned.
  - Core LDO: **TLV74311PDBVR** (JLCPCB C485147, 1.1 V fixed, 300 mA, SOT-23-5), **fed from +5V**, not 3V3, so core
    current steps stay off the 3V3 reference rail (about 0.2 W at 50 mA, fine in SOT-23-5; input max 5.5 V).
    The RP2350 allows any supply order except VREG_VIN/VREG_AVDD, which must rise together (both on 3V3).
    DVDD spec: 1.05-1.16 V, transients within ±100 mV.
  - 3V3 LDO: **TPS7A2033PDBVR** (JLCPCB C2862740, 300 mA, 7 µVrms, 95 dB PSRR at 1 kHz, ±1.5% over line, load and
    temperature). Same SOT-23-5 pinout as the ADP122 (IN, GND, EN, NC, OUT), which JLCPCB barely stocks any more.
    3V3 is the sense chain's reference: row bias, V_REF and the column pulses are all ratiometric to it, so noise,
    PSRR and load transients matter more than absolute accuracy. Keep switching loads (TFT backlight) off 3V3 if
    possible. Fallback if more current is ever needed: LP5912-3.3DRVR (C524780, 500 mA, WSON-6 2x2).
- USB input protection: the **mSMD110 polyfuse (F1) is replaced by an AP22653W6-7** current-limited power switch
  (JLCPCB C2158037, SOT-26, 65 mΩ). Use the non-"A" version: it limits current and recovers by itself, while the "A"
  version latches off. Path: VBUS -> AP22653 -> +5V.
  - EN (active high) tied to IN. RLIM about 20k gives a limit of about 1.29 A (1.20-1.38 A at 25 °C), close to
    Rev 3's 1.1 A fuse hold current. FAULT is open-drain and can be left unconnected.
  - Caps: ≥ 0.1 µF on IN next to the IC, keeping VBUS-side capacitance ≤ 10 µF for USB attach. On OUT, 0.1 µF plus
    ≥ 10 µF bulk (Rev 3 had 4.7 µF on +5V); soft-start (about 0.5 ms) limits the inrush.
  - With VIN below UVLO (USB unplugged: PS/2-only mode, or the split half powered over J7) it blocks reverse current
    (≤ 1 µA). The 600 Ω output discharge is only active while disabled, and only for a limited time.
  - While enabled, reverse current is only limited (trips at VOUT - VIN about 65 mV, 0.32 A, off after 2-20 ms).
    Accepted: a little back-feed if both split halves are on USB, or PS/2 and USB are both live. No extra ORing part.
  - VIN abs max 6.0 V. Check the SOT-26 pin numbering against the datasheet when drawing.
- Flash: **W25Q64JVXGIM**, 8 MB, XSON-8 4x4 (JLCPCB C6604688; replaces the 2 MB USON-8 W25Q16). Smallest package
  JLCPCB stocks for 64 Mbit at 3.3 V (the plan's ZD25Q64DSIGT isn't in their library). "IM" = QE bit 0 from the
  factory. Check the exposed-pad size against Winbond's XSON drawing before routing (U1 currently uses
  `WSON-8-1EP_4x4mm_P0.8mm_EP2.2x3mm`).
- Crystal: **ABM8-272-T3** (JLCPCB C20625731), the part the RP2350 datasheet recommends (12 MHz, CL 10 pF,
  ESR ≤ 50 Ω). Use the Pico 2 loading: 15 pF caps and a 1k series resistor on XOUT.
- The matrix sense chain (LMV339s, DAC, ROW0-7 on GP0-7, COL0-15) stays untouched.
- New through-hole breakouts: rotary encoder (J9, with RC debounce: 10k pull-up + 100 nF per phase; no debounce on
  the encoder button), and a single-row 1x17 **breakout header J7** left of the USB-C connector that merges the free
  expansion pins, the split link (5V, GND, DATA) and the TFT display (SPI), so a ribbon cable can be soldered in one
  row (connector-placement feedback, 2026-10-26; J8 and J10 no longer exist). J7 pinout, blocks kept in their
  original order with a GND per block:

  | Pin | Net | Pin | Net |
  |---|---|---|---|
  | 1 | 3V3 | 10 | GND (display) |
  | 2-5 | EXP_GP32, EXP_GP41, EXP_GP46, EXP_GP47 | 11 | TFT_VCC (JP1) |
  | 6 | GND | 12 / 13 | TFT_SCK / TFT_MOSI |
  | 7 | +5V (split) | 14 / 15 | TFT_RST / TFT_DC |
  | 8 | GND (split) | 16 / 17 | TFT_CS / TFT_BLK |
  | 9 | UART_DATA (split) | | |

  Pins 10-17 keep the ST7789 module order, so a display can plug straight onto them.
- The 18 column 1k series resistors (Rev 3: R14-R16, R18, R20-R24, R26, R28-R32, R34, R47, R48) are removed:
  COLn goes straight from the MCU to J2. This frees the band above J2 so the RP2350B can sit lower. The 47k
  A_ROW bias resistors (R7, R9, R13, R19, R27, R35, R37, R39, to `ROW_PULLUP`, a 7.5k/1k divider from 3V3 at about
  0.39 V) stay.
- LEDs on GPIOs directly: they draw a few mA each, well within GPIO drive.
- **J4 Ext Port, 2x4:** pins 3-8 keep the Rev 3 order (+5V, SOLENOID_ENABLE, PS2_ENABLE, SOLENOID_PULSE, 3V3, GND).
  Pins 1-2 are **USB D+/D-** coming from the PS/2 AT daughterboard Rev 3 (its USB-C port can then carry USB too):
  **pin 1 = D-, pin 2 = D+**, chosen for routing (D+ runs north of D- at U3, so D+ passes above pin 1 to reach
  pin 2 without crossing; the daughterboard adapts).
  They join the controller's protected USB lines `F_D+`/`F_D-`: after the USBLC6 (U3), before the 27R series
  resistors to the MCU. Route them as a 90 Ω pair and keep the branch short (USB full speed tolerates a short
  stub). Never connect J1 and the daughterboard's USB port to hosts at the same time.

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
| 42 / 43 / 44 | LED0 / LED1 / LED2 | were PCA9557 LED0-2 (on J2); schematic keeps the J2 net names |
| 45 | UART_DATA | split link, half-duplex PIO serial |
| 32, 41, 46, 47 | free | through holes for expansion |

Points to verify while implementing (against the RP2350 datasheet / hardware design guide / QMK docs):
- VREG_LX in datasheet Figure 24 (page 410) looks unconnected but the figure couldn't be rendered to confirm.
- Rev 3's DAC symbol is an MCP4725, whose pin 6 is A0, so the fitted MCP4716's VREF pin floats. Check what the
  MCP4716 datasheet wants for VREF when VDD is the selected reference.
- J9 encoder, 1x5 in module order: 1 ENCODER_A, 2 ENCODER_B, 3 ENCODER_BUTTON, 4 3V3, 5 GND. RC debounce on A/B
  only (10k pull-up + 100 nF each); the button uses the internal pull-up.
- Display pins (J7 10-17, 8-pin ST7789 module order: GND, VCC, SCL, SDA, RES, DC, CS, BLK): VCC goes through a 3-pad solder
  jumper selecting 3V3 or +5V (decided for now; a dedicated 3.3 V LDO from +5V was the alternative). Default it
  bridged to 3V3, which is safe for every module. 5V keeps the backlight current off the 3V3 reference rail, but only
  modules with their own regulator accept it. BLK is GP36 (PWM); on most modules it only switches a transistor.
- GP33 is an SPI0 function pin, not SPI1. That's harmless if CS is driven as a plain GPIO. No free pin in the
  plan has the SPI1 RX function, so the display must work with MISO unused.
- PIO blocks see a 32-GPIO window (base 0 or 16). Current firmware: PIO0 = matrix scanner, PIO1 = PS/2
  (its program fills all 32 instructions). The split serial on GP45 therefore needs **PIO2** with GPIOBASE 16,
  not PIO0 as the plan's firmware section says.
- PS/2 pin order is free: the firmware patches the `ps2out` program to wait on an absolute GPIO (`0x2080 | pin`),
  so clock = data - 1 on J4 works. On the RP2350 that index is relative to the PIO's GPIOBASE, which is fine
  while PS/2 stays below GP32.
- Moving COL16/17 to GP28/29 requires changing the `col_16_17` PIO pin base (26 today) in `pio_matrix_scan.c`.
- `PS2_ENABLE` (GP40) is actually a daughterboard **presence-detect input**: 3.33 V from the PS/2 host's 5 V through
  a 1k/2k divider on the daughterboard, with a 47k pull-down (R50) on this board. **Keep 47k.** Erratum E9 (A2
  silicon only, fixed from A3) could hold the pad at about 2.2 V only if the daughterboard were unplugged from J4
  while the board stays powered. With a PS/2 host off, the daughterboard's 2k still pulls the pin low hard, and
  firmware latches PS/2 mode at boot anyway.
- Split DATA: **no series resistor** (or a 0R footprint). QMK's RP PIO half-duplex driver has the receiver drive the
  line high at 2 mA while the transmitter pulls low at 12 mA. With RP2350 worst-case levels (VOH 2.62 V at 2 mA,
  VOL 0.5 V at 12 mA, VIL 0.8 V), the low level breaks at about 33R per board. Put ESD protection at the connector.
- Split link (J7 pins 7-9): 5V pin on the +5V rail (after the AP22653), so one board on USB powers both through its own
  current limit. ESD: a single bidirectional TVS on DATA, D1 ESD9B3.3ST5G (C96512, SOD-923, 3.3 V working).
  The 5V pin needs no TVS: the +5V bulk capacitance absorbs an ESD discharge. Don't move the split 5V to VBUS (it would
  tie two hosts' VBUS together, bypass the AP22653 current limit and leave live VBUS on an unplugged USB-C port).
  The PS/2 host's 5 V also lands on +5V (J4 pin 1, via the daughterboard's MIC2009 + Schottky).
- 3V3 budget: about 40 mA for the core design (RP2350 IO/USB, flash, comparators, DAC, LEDs; the core is on +5V
  now), plus the TFT and whatever hangs on J3's I2C. 300 mA leaves margin unless the backlight runs from 3V3.
- **Erratum RP2350-E9** on input pads: the ROW inputs have 10k external pull-ups to 3V3, which should be safe.
  Check the silicon stepping JLCPCB stocks.

V2 schematic status (2026-10-26): drawn in place on the flat A2 sheet, ERC clean (errors). New blocks have titles
but no dashed frames yet. Project-local symbols added: `AP22653W6`, `TLV743xxPDBV`, `MCP4716xxx-xCH`. The title
block still says Rev 3.

SWD/I2C: the V2 JST SH connectors (J5 Qwiic 4-pin, J6 SWD 3-pin, bottom side) were reverted on 2026-10-26 after
connector-placement feedback. **J3** is back: Rev 3's 2x3 SWD/I2C header with the same pinout and footprint
(`Leyden_Jar:PinHeader_2x03_P2.54mm_Horizontal`, not assembled). On the board it sits below the J7 breakout row with
pad 1 vertically aligned on J7 pad 1: footprint origin (12.821, 5.08), pad 1 at (12.761, 5.06), body pointing +x to
x 25.9.

RUN/BOOT buttons (2026-10-26 feedback): all four B3U-1000P are back as in Rev 3, a top-side pair (SW3 // SW1 on
RUN, SW4 // SW2 on USB_BOOT, F.Cu) and a bottom-side pair (SW1, SW2, B.Cu) at the same XY. Vertical (rot 90),
directly left of the USB-C and below the J7 row: RUN at (51.70, 5.6), BOOT at (55.00, 5.6). Pitch 3.3 mm (was
3.7), so the courtyards touch each other, J7's (y 3.2) and J1's (x 56.66). A button pair can't sit on the top edge
next to J7: H1-to-J1 is 47.2 mm and J7 + two buttons need 50.8 mm. The left button's courtyard corner overlaps the
flash U1's by 0.2 mm (bodies 0.45 mm apart), left for the layout cleanup.

Still open (confirm with the user): whether V2 lives in a new `pcb/` folder or replaces the Rev 3 project in place,
and board outline/connector placement compatibility with existing Model F / Beam Spring cases.

## Git conventions

- Commit messages are prefixed with a tag: `[feature]`, `[bugfix]`, `[fix]`, `[cleanup]`, followed by a short sentence
  ending in a period. Example: `[bugfix] Wrong 0402 casings instead of 0603.`
- Commit or push only when the user asks.
- When a revision is released, regenerate `production_files/` and update `README.md` (feature list, revision history,
  images).
