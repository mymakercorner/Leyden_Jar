# RP2350-compatible QSPI flash chips

Oct 28, 2026 · Rico

## Summary

Raspberry Pi officially supports any 3.3 V SPI NOR flash up to 16 MB that has the standard 03h read, but its boot code
runs fast quad mode only on three families: Winbond W25Q (the default), Renesas/Adesto AT25SF and ISSI IS25LP. Puya
P25Q64SH, Boya BY25Q64ES and Fudan FM25Q64 are not listed by Raspberry Pi, but their datasheets show they work with the
default Winbond boot code. GigaDevice GD25Q64E needs a different boot code.

- **Officially supported, quad:** Winbond W25Q, Renesas/Adesto AT25SF, ISSI IS25LP.
- **Compatible with the default boot code (datasheet-checked):** Puya P25Q64SH, Boya BY25Q64ES, Fudan FM25Q64.
- **Needs non-default boot code:** GigaDevice GD25Q64E.
- **Not checked:** Macronix, XTX, Zbit, XMC.

For Leyden Jar V2 (8 MB, 3.3 V), the cheapest compatible part is the Puya P25Q64SH-SSH-IT at $0.76 in SOP-8, against
$7.16 for the current Winbond in XSON 4x4. At 4 MB it is the Boya BY25Q32ESTIG at $0.42; the Pico 2's Winbond W25Q32RV
is the small-package choice (XSON 2x3, $3.90). Upstream QMK doesn't support the RP2350 yet
([qmk_firmware#25881](https://github.com/qmk/qmk_firmware/issues/25881)), so the V2 firmware port will choose its boot
code anyway.

## What decides compatibility

Raspberry Pi's official rule
([Hardware design with RP2350](https://pip-assets.raspberrypi.com/categories/1214-rp2350/documents/RP-008280-DS-2-hardware-design-with-rp2350.pdf),
section 3.3 "Supported flash chips"): the RP2350 can run from any flash that supports the 03h serial read with 24-bit
addressing, "which includes most 25-series flash devices". To be programmable through the bootrom it must also accept
02h (page program), 05h (status read), 06h (write enable) and 20h (4 kB sector erase). 16 MB (128 Mbit) is the largest
size it supports. Fast quad mode is a firmware matter: the boot code ("boot stage 2") has to enable it for the chip in
use.

1. The bootrom probes the flash with the `03h` serial read at about 1 MHz and loads the boot stage 2 code from it.
2. The boot stage 2 code then enables quad mode: it reads the status register and, if the Quad Enable (QE) bit is off,
   writes it.
3. From then on the RP2350 executes from flash with `EBh` quad I/O reads in continuous mode.

Raspberry Pi ships these boot stage 2 variants for the RP2350 in
[pico-sdk](https://github.com/raspberrypi/pico-sdk/tree/master/src/rp2350/boot_stage2):

| pico-sdk boot code | Written for | How it sets QE |
| --- | --- | --- |
| [`boot2_w25q080`](https://raw.githubusercontent.com/raspberrypi/pico-sdk/master/src/rp2350/boot_stage2/boot2_w25q080.S) (default) | Winbond W25Q | `01h` with two data bytes `00h, 02h` (QE = bit 1 of status register 2) |
| [`boot2_at25sf128a`](https://raw.githubusercontent.com/raspberrypi/pico-sdk/master/src/rp2350/boot_stage2/boot2_at25sf128a.S) | Adesto/Renesas AT25SF128A | `31h` with `02h` (writes status register 2 alone) |
| [`boot2_is25lp080`](https://raw.githubusercontent.com/raspberrypi/pico-sdk/master/src/rp2350/boot_stage2/boot2_is25lp080.S) | ISSI IS25LP080D | `01h` with `40h` (QE = bit 6 of the only status register) |
| `boot2_w25x10cl` | Winbond W25X10CL | dual-I/O part, no quad |
| [`boot2_generic_03h`](https://raw.githubusercontent.com/raspberrypi/pico-sdk/master/src/rp2350/boot_stage2/boot2_generic_03h.S) | "Anything which responds to 03h serial read" | no quad; pico-sdk puts it at about 3x slower than quad XIP |

In this doc, **officially supported** means Raspberry Pi ships boot code written for that chip family, or uses the
family on its own RP2350 board: the [Pico 2](https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf) uses a
Winbond W25Q32RV. **Compatible** means the chip's datasheet shows that one of those boot codes sets its QE bit
correctly. **Needs custom boot code** means none of them does, so a small boot stage 2 change is needed.

## Compatibility by family

Any 3.3 V chip up to 16 MB with the 03h read and the four programming commands is officially supported in plain serial
mode. The table is about fast quad mode: which boot code sets the chip's Quad Enable (QE) bit, checked against each
datasheet.

| Family (3.3 V) | Example 8 MB part | How the datasheet sets QE | Boot code that works | Status |
| --- | --- | --- | --- | --- |
| Winbond W25Q (JV, RV) | W25Q64JVXGIM | 01h + 2 bytes writes status registers 1 and 2; QE = bit 1 of SR2 | pico-sdk default (`boot2_w25q080`) | **Officially supported**: the default boot code is written for it; the [Pico 2](https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf) uses a W25Q32RV and the [minimal design](https://pip-assets.raspberrypi.com/categories/1214-rp2350/documents/RP-008280-DS-2-hardware-design-with-rp2350.pdf) a W25Q128JVS |
| Renesas/Adesto AT25SF | AT25SF128A (16 MB) | 31h writes SR2; QE = bit 1 | pico-sdk `boot2_at25sf128a` | **Officially supported** (boot code written for the AT25SF128A) |
| ISSI IS25LP | IS25LP080D (1 MB) | 01h writes the single SR; QE = bit 6 | pico-sdk `boot2_is25lp080` | **Officially supported** for the IS25LP080D; other densities not checked |
| Puya P25Q64SH | P25Q64SH-SSH-IT | 01h + 2 bytes writes SR0 and SR1, "to be backward compatible"; QE = S9, default 0 ([datasheet V1.5](https://www.puyasemi.com/download_path/%E6%95%B0%E6%8D%AE%E6%89%8B%E5%86%8C/Flash%20%E8%8A%AF%E7%89%87/P25Q64SH_Datasheet_V1.5.pdf), p. 35) | pico-sdk default | Compatible, not listed by Raspberry Pi |
| Boya BY25Q64ES | BY25Q64ESSIG | SR2 can be written by 01h or 31h; QE default 0 ([datasheet Rev 2.9](https://dfsimg1.hqewimg.com/group6/M00/06/85/wKhk6WpQPxKAblswAEnnmtKnVYs835.pdf), pp. 17 and 29) | pico-sdk default | Compatible, not listed by Raspberry Pi |
| Fudan FM25Q64 | FM25Q64AI3 | 01h takes 8 or 16 data bits; QE = S9, default 0; an 8-bit write clears QE ([datasheet Ver 1.0](https://mt-system.ru/upload/8.pdf), pp. 13 and 23) | pico-sdk default (it sends 16 bits) | Compatible, not listed by Raspberry Pi |
| GigaDevice GD25Q64E | GD25Q64ETIGR, GD25Q64EQIGR | 01h writes SR1 only and is ignored unless CS# rises after 8 bits; QE = S9 via 31h, default 0 ([datasheet Rev 1.4](https://www.gigadevice.com.cn/Public/Uploads/uploadfile/files/20220714/DS-00484-GD25Q64E-Rev1.4.pdf), pp. 13 and 19) | **Not** the default. The AT25SF128A boot code uses the same 31h write and should fit, but that is untested | Needs non-default boot code |
| Macronix MX25L, XTX XT25F, Zbit ZB25VQ, XMC XM25QH | — | not checked: datasheets not obtained | serial mode only until checked | Unverified |
| 1.8 V parts (W25Q64JW, GD25LQ64E, ...) | — | — | — | Not usable on Leyden Jar V2: its QSPI runs at 3.3 V |
| Anything above 16 MB (W25Q256, ...) | — | — | — | Not supported: the RP2350 uses 24-bit addressing, 16 MB maximum |

Winbond's -IM parts, like the current U1, leave QE off from the factory. That doesn't matter, because the default boot
code sets it. Raspberry Pi also warns that a chip must leave continuous-read mode on the bootrom's reset sequence, or the
RP2350 can't recover after a reset without a power cycle. Check this on the first prototype by pressing RUN while the
board stays powered.

## 8 MB parts you can buy

The cheapest 8 MB option that works with the default boot code is the Puya P25Q64SH at $0.76, in SOP-8. Every
compatible 8 MB part in a 4x4 mm package costs $2.23 or more. Prices are for 1 piece, read on 28 Oct 2026.

| Part | Package | Default boot code? | Where | Price (USD) | Stock |
| --- | --- | --- | --- | ---: | ---: |
| [P25Q64SH-SSH-IT](https://jlcpcb.com/partdetail/C5263845) (Puya) | SOP-8 150 mil | yes | JLCPCB C5263845 | 0.76 | 11,850 |
| [P25Q64SH-SSH-IR](https://jlcpcb.com/partdetail/C18185312) (Puya) | SOP-8 150 mil | yes | JLCPCB C18185312 | 0.78 | 5,331 |
| [BY25Q64ESSIG(R)](https://jlcpcb.com/partdetail/C22471254) (Boya) | SOP-8 208 mil | yes | JLCPCB C22471254 | 0.87 | 3,450 |
| [FM25Q64AI3-SOB-T-G](https://jlcpcb.com/partdetail/C19626526) (Fudan) | SOP-8 208 mil | yes | JLCPCB C19626526 | 1.04 | 11,766 |
| [W25Q64JVSSIM](https://jlcpcb.com/partdetail/C5362615) (Winbond) | SOIC-8 208 mil | yes | JLCPCB C5362615 | 2.97 | 9,073 |
| [W25Q64JVZEIQ](https://jlcpcb.com/partdetail/C571262) (Winbond) | WSON-8 6x8 | yes | JLCPCB C571262 | 3.66 | 6,700 |
| [W25Q64JVXGIQ](https://www.digikey.com/en/products/detail/winbond-electronics/W25Q64JVXGIQ-TR/15181863) (Winbond) | XSON-8 4x4 | yes | DigiKey | 4.53 | 35,041, supply constrained |
| [W25Q64JVXGIM](https://jlcpcb.com/partdetail/C6604688) (Winbond, current U1) | XSON-8 4x4 | yes | JLCPCB C6604688 | 7.16 | 4,876 |
| [GD25Q64ESIGR](https://jlcpcb.com/partdetail/C2831359) (GigaDevice) | SOP-8 208 mil | no | JLCPCB C2831359 | 1.00 | 17,512 |
| [GD25Q64ETIGR](https://jlcpcb.com/partdetail/C2976334) (GigaDevice) | SOP-8 150 mil | no | JLCPCB C2976334 | 1.30 | 9,305 |
| [GD25Q64EQIGR](https://www.digikey.com/en/products/detail/gigadevice-electronics-singapore-pte-ltd/GD25Q64EQIGR/20531989) (GigaDevice) | USON-8 4x4 | no | DigiKey | 2.23 | 5,774, purchase limit |

Puya's datasheet also lists the P25Q64SH in USON 4x4 and 3x2 mm, but no distributor I checked stocks those versions.

## 4 MB parts you can buy

At 4 MB the cheapest part that works with the default boot code is the Boya BY25Q32ESTIG at $0.42 in SOP-8 150 mil.
The smallest is the Pico 2's own Winbond W25Q32RVXHJQ, XSON 2x3 mm at $3.90. Prices are for 1 piece at JLCPCB, read on
28 Oct 2026; all parts are 3.3 V.

| Part | Package | Default boot code? | JLCPCB # | Price (USD) | Stock |
| --- | --- | --- | --- | ---: | ---: |
| [BY25Q32ESTIG](https://jlcpcb.com/partdetail/C22391875) (Boya) | SOP-8 150 mil | yes | C22391875 | 0.42 | 1,341 |
| [BY25Q32ESTIG(R)](https://jlcpcb.com/partdetail/C53426826) (Boya) | SOP-8 150 mil | yes | C53426826 | 0.57 | 417 |
| [BY25Q32ESSIG](https://jlcpcb.com/partdetail/C22391874) (Boya) | SOP-8 208 mil | yes | C22391874 | 0.66 | 5,899 |
| [W25Q32JVZPIQ](https://jlcpcb.com/partdetail/C571260) (Winbond) | WSON-8 5x6 | yes | C571260 | 1.43 | 8,182 |
| [W25Q32JVSSIQ](https://jlcpcb.com/partdetail/C179173) (Winbond) | SOIC-8 208 mil | yes | C179173 | 1.48 | 3,178 |
| [W25Q32JVSNIQ](https://jlcpcb.com/partdetail/C5355146) (Winbond) | SOIC-8 150 mil | yes | C5355146 | 1.55 | 14,533 |
| [W25Q32RVCSJQ](https://jlcpcb.com/partdetail/C54442318) (Winbond) | SOP-8 208 mil | yes | C54442318 | 1.81 | 403 |
| [W25Q32RVSNJQ](https://jlcpcb.com/partdetail/C35516971) (Winbond) | SOIC-8 150 mil | yes | C35516971 | 2.12 | 2,000 |
| [W25Q32JVUUIQ](https://jlcpcb.com/partdetail/C2999380) (Winbond) | USON-8 3x4 | yes | C2999380 | 2.52 | 2,207 |
| [W25Q32RVXHJQ](https://jlcpcb.com/partdetail/C32246052) (Winbond, used on Pico 2) | XSON-8 2x3 | yes | C32246052 | 3.90 | 1,563 |
| [W25Q32JVXGIQ](https://jlcpcb.com/partdetail/C2456238) (Winbond) | XSON-8 4x4 | yes | C2456238 | 8.88 | 66 |
| [P25Q32SH-SSH-IT](https://jlcpcb.com/partdetail/C2833294) (Puya) | SOP-8 150 mil | unclear | C2833294 | 0.74 | 6,626 |
| [GD25Q32ESIGR](https://jlcpcb.com/partdetail/C2832998) (GigaDevice) | SOP-8 208 mil | likely no | C2832998 | 0.84 | 20,550 |
| [GD25Q32ETIGR](https://jlcpcb.com/partdetail/C2986328) (GigaDevice) | SOP-8 150 mil | likely no | C2986328 | 1.04 | 10,917 |
| [GD25Q32EWIGR](https://jlcpcb.com/partdetail/C2928892) (GigaDevice) | WSON-8 5x6 | likely no | C2928892 | 1.12 | 1,294 |
| [GD25Q32EEIGR](https://jlcpcb.com/partdetail/C2973794) (GigaDevice) | USON-8 2x3 | likely no | C2973794 | 1.23 | 6,720 |

- **Boya BY25Q32ES:** its [datasheet](https://cdn.sparkfun.com/assets/2/0/b/3/1/2024-ESP-01S_Flash-BY25Q32ES.pdf)
  (p. 30) says 01h followed by 2 bytes writes status registers 1 and 2, like Winbond.
- **Puya P25Q32SH is unclear:** Puya's
  [migration note P25Q32H to P25Q32SH](https://www.lcsc.com/datasheet/C2833294.pdf) (p. 5) lists 01h with only 1 data
  byte and QE in SR2, written by 31h. Unlike the 8 MB P25Q64SH, that points to the AT25SF128A-style boot code; check
  the full datasheet before using it.
- **GigaDevice GD25Q32E:** the 32 Mbit datasheet was not checked. It is the same E generation as the GD25Q64E, so expect
  the same 31h requirement.
- **Winbond W25Q32RV** is the exact chip on Raspberry Pi's Pico 2, so it is the most proven 4 MB option. Its XSON 2x3
  size matches the 2x3 mm class of Rev 3's W25Q16JVUXIQ; compare the land patterns before reusing that footprint.

## Sources

- Raspberry Pi, [Hardware design with RP2350](https://pip-assets.raspberrypi.com/categories/1214-rp2350/documents/RP-008280-DS-2-hardware-design-with-rp2350.pdf), sections 3.1 and 3.3
- Raspberry Pi, [Pico 2 datasheet](https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf)
- Raspberry Pi, [pico-sdk RP2350 boot stage 2 sources](https://github.com/raspberrypi/pico-sdk/tree/master/src/rp2350/boot_stage2)
- GigaDevice, [GD25Q64E datasheet Rev 1.4](https://www.gigadevice.com.cn/Public/Uploads/uploadfile/files/20220714/DS-00484-GD25Q64E-Rev1.4.pdf)
- Puya, [P25Q64SH datasheet V1.5](https://www.puyasemi.com/download_path/%E6%95%B0%E6%8D%AE%E6%89%8B%E5%86%8C/Flash%20%E8%8A%AF%E7%89%87/P25Q64SH_Datasheet_V1.5.pdf)
- Boya, [BY25Q64ES datasheet Rev 2.9](https://dfsimg1.hqewimg.com/group6/M00/06/85/wKhk6WpQPxKAblswAEnnmtKnVYs835.pdf)
- Boya, [BY25Q32ES datasheet](https://cdn.sparkfun.com/assets/2/0/b/3/1/2024-ESP-01S_Flash-BY25Q32ES.pdf)
- Puya, [Migration from P25Q32H to P25Q32SH application note](https://www.lcsc.com/datasheet/C2833294.pdf)
- Fudan, [FM25Q64 datasheet Ver 1.0](https://mt-system.ru/upload/8.pdf)
- QMK, [issue #25881: RP2350 support](https://github.com/qmk/qmk_firmware/issues/25881)
- Prices and stock: [JLCPCB parts library](https://jlcpcb.com/parts), [LCSC](https://www.lcsc.com/search?q=P25Q64SH),
  DigiKey pages linked in the table, read on 28 Oct 2026
