# Leyden Jar V2 – JLCPCB BOM cost and stock

As of 2026-10-28 · Rico

## Summary

The assembled V2 components cost **$12.37 per board** at JLCPCB's single-piece prices, or **$8.54** at full-reel prices.
Current JLCPCB stock covers **135 boards**, limited by the LMV339 comparators (2 per board, 270 in stock).

| Item | Value |
| --- | --- |
| Assembled BOM lines / parts per board | 25 lines / 77 parts |
| Component cost per board, single-piece price | $12.37 |
| Component cost per board, full-reel price | $8.54 |
| Basic / Extended lines | 11 Basic / 14 Extended |
| Extended part loading fee | about $3 per Extended line per order, so about $42 per order (check at checkout) |
| Boards covered by current stock | 135 (LMV339IPWR); next limits: crystal 2,275, RP2350B 3,114 |

The 8 MB flash (W25Q64JVXGIM) is now the most expensive line at $7.16, 58% of the component cost and more than the
RP2350B ($1.28).

## Full BOM

Sorted by cost per board. Unit price = JLCPCB's single-piece price in USD; stock = JLCPCB's assembly stock on
28 Oct 2026; boards covered = stock ÷ quantity per board.

| Part (JLCPCB page) | Designators | Value | Type | Qty | Unit price (USD) | Cost/board (USD) | JLCPCB stock | Boards covered |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| [W25Q64JVXGIM](https://jlcpcb.com/partdetail/C6604688) (C6604688) | U1 | W25Q64JVXGIM | Extended | 1 | 7.1550 | 7.1550 | 4,876 | 4,876 |
| [RP2350B](https://jlcpcb.com/partdetail/C42415655) (C42415655) | U5 | RP2350B | Extended | 1 | 1.2840 | 1.2840 | 3,114 | 3,114 |
| [LMV339IPWR](https://jlcpcb.com/partdetail/C273648) (C273648) | U2, U6 | LMV339 | Extended | 2 | 0.5552 | 1.1104 | 270 | 135 |
| [MCP4716A0T-E/CH](https://jlcpcb.com/partdetail/C110057) (C110057) | U10 | MCP4716A0T-E/CH | Extended | 1 | 0.8926 | 0.8926 | 7,643 | 7,643 |
| [ABM8-272-T3](https://jlcpcb.com/partdetail/C20625731) (C20625731) | Y1 | ABM8-272-T3 | Extended | 1 | 0.6584 | 0.6584 | 2,275 | 2,275 |
| [AP22653W6-7](https://jlcpcb.com/partdetail/C2158037) (C2158037) | U8 | AP22653W6-7 | Extended | 1 | 0.2632 | 0.2632 | 8,401 | 8,401 |
| [TPS7A2033PDBVR](https://jlcpcb.com/partdetail/C2862740) (C2862740) | U4 | TPS7A2033PDBVR | Extended | 1 | 0.2092 | 0.2092 | 144,607 | 144,607 |
| [TYPE-C-31-M-12](https://jlcpcb.com/partdetail/C165948) (C165948) | J1 | USB_C_Receptacle_USB2.0 | Extended | 1 | 0.1871 | 0.1871 | 294,278 | 294,278 |
| [USBLC6-2SC6](https://jlcpcb.com/partdetail/C7519) (C7519) | U3 | USBLC6-2SC6 | Extended | 1 | 0.1798 | 0.1798 | 42,235 | 42,235 |
| [TLV74311PDBVR](https://jlcpcb.com/partdetail/C485147) (C485147) | U7 | TLV74311PDBVR | Extended | 1 | 0.0936 | 0.0936 | 10,216 | 10,216 |
| [CL21A475KAQNNNE](https://jlcpcb.com/partdetail/C1779) (C1779) | C2, C17 | 4.7u | Basic | 2 | 0.0343 | 0.0686 | 1,908,646 | 954,323 |
| [CL05B104KO5NNNC](https://jlcpcb.com/partdetail/C1525) (C1525) | C1, C4, C5, C6, C7, C8, C9, C10, C11, C12, C13, C19, C20, C21, C23, C26, C27, C28, C29, C31, C32 | 100n | Basic | 21 | 0.0031 | 0.0651 | 33,282,075 | 1,584,860 |
| [ESD9B3.3ST5G](https://jlcpcb.com/partdetail/C96512) (C96512) | D1 | ESD9B3.3ST5G | Extended | 1 | 0.0446 | 0.0446 | 64,565 | 64,565 |
| [CL21A106KAYNNNE](https://jlcpcb.com/partdetail/C15850) (C15850) | C16 | 10u | Basic | 1 | 0.0438 | 0.0438 | 8,614,775 | 8,614,775 |
| [0402WGF1002TCE](https://jlcpcb.com/partdetail/C25744) (C25744) | R1, R6, R8, R12, R17, R25, R33, R36, R38, R40, R41, R53, R54 | 10k | Basic | 13 | 0.0024 | 0.0312 | 17,652,570 | 1,357,890 |
| [CL05A105KA5NQNC](https://jlcpcb.com/partdetail/C52923) (C52923) | C3, C22, C24, C25 | 1u | Basic | 4 | 0.0064 | 0.0256 | 10,913,288 | 2,728,322 |
| [0402WGF4702TCE](https://jlcpcb.com/partdetail/C25792) (C25792) | R7, R9, R13, R19, R27, R35, R37, R39, R50 | 47k | Basic | 9 | 0.0020 | 0.0180 | 6,612,733 | 734,748 |
| [CBW201209U121T](https://jlcpcb.com/partdetail/C139186) (C139186) | FB1 | CBW201209U121T | Extended | 1 | 0.0143 | 0.0143 | 123,479 | 123,479 |
| [0402CG150J500NT](https://jlcpcb.com/partdetail/C1548) (C1548) | C14, C15 | 15p | Basic | 2 | 0.0038 | 0.0076 | 1,366,147 | 683,073 |
| [0402WGF1001TCE](https://jlcpcb.com/partdetail/C11702) (C11702) | R4, R5, R10, R11, R46 | 1k | Basic | 5 | 0.0013 | 0.0065 | 22,808,630 | 4,561,726 |
| [0402WGF5101TCE](https://jlcpcb.com/partdetail/C25905) (C25905) | R43, R44 | 5.1k | Basic | 2 | 0.0023 | 0.0046 | 4,026,608 | 2,013,304 |
| [0402WGF270JTCE](https://jlcpcb.com/partdetail/C25100) (C25100) | R2, R3 | 27 | Extended | 2 | 0.0013 | 0.0026 | 43,701 | 21,850 |
| [0402WGF4701TCE](https://jlcpcb.com/partdetail/C25900) (C25900) | R42 | 4.7k | Basic | 1 | 0.0021 | 0.0021 | 14,156,279 | 14,156,279 |
| [0402WGF7501TCE](https://jlcpcb.com/partdetail/C25918) (C25918) | R45 | 7.5k | Extended | 1 | 0.0021 | 0.0021 | 977,634 | 977,634 |
| [0402WGF2002TCE](https://jlcpcb.com/partdetail/C25765) (C25765) | R51 | 20k | Basic | 1 | 0.0011 | 0.0011 | 2,961,206 | 2,961,206 |
| **Total** | | | | **77** | | **12.37** | | **135** |

## Parts at risk

Two lines need watching before an order: the comparators for stock, the flash for cost.

| Part | Issue | Note |
| --- | --- | --- |
| [LMV339IPWR](https://jlcpcb.com/partdetail/C273648) (U2, U6) | 270 in stock = 135 boards | Active at TI. Kept on purpose: the scan firmware is tuned to it. The onsemi [LMV339DTBR2G](https://jlcpcb.com/partdetail/C154571) (C154571, 156 in stock) is pin-compatible but its timing would need checking. |
| [W25Q64JVXGIM](https://jlcpcb.com/partdetail/C6604688) (U1) | $7.16 each, 58% of the component cost | Every 8 MB W25Q64JV variant at JLCPCB costs $2.97 to $7.16 today. |
| [ABM8-272-T3](https://jlcpcb.com/partdetail/C20625731) (Y1) | 2,275 in stock | Next stock limit after the comparators; enough for any likely batch. |
| [0402WGF270JTCE](https://jlcpcb.com/partdetail/C25100) (R2, R3, 27 Ω) | Search page lists it as pre-order (min. 10,000) | The part page shows 43,701 in stock. Check it is selectable when you upload the BOM; another 27 Ω 0402 is an easy swap. |

## Not in the assembly BOM

These are not counted in the cost above.

| Designators | Part | Why |
| --- | --- | --- |
| SW1–SW4 | B3U-1000P ([C5362268](https://jlcpcb.com/partdetail/C5362268)) | RUN/BOOT buttons, deliberately not assembled. JLCPCB has 0 in stock (consign only, $0.04 est.). |
| J3, J4, J7, J9 | 2x3, 2x4, 1x17 and 1x5 pin headers | Through-hole, not assembled; no LCSC number. |
| J2 | Switch matrix connector | No LCSC number in the schematic. |
| JP1 | TFT VCC solder jumper | Copper only, bridged 1-2 by default. |
| H1–H3 | Mounting holes, logo | Copper/silkscreen only. |

## Method and sources

- BOM: the LCSC numbers on the V2 schematic, commit 31efe6f on branch `leyden-jar-v2-work`, grouped by LCSC number.
- Prices and stock: JLCPCB's parts library, read on 28 Oct 2026 from each part's search result or part page (linked in
  the BOM table). Full-reel prices come from the same results; for 4 lines (TPS7A2033, ABM8-272-T3, 5.1k, 27 Ω) only
  the single-piece price was shown, so it is used there too.
- Not included: PCB fabrication, assembly setup and stencil, Extended part loading fees, shipping, taxes, and the parts
  listed under "Not in the assembly BOM".
- JLCPCB stock moves daily. Recheck the LMV339IPWR and flash lines before ordering.

Sources: [JLCPCB parts library](https://jlcpcb.com/parts), [LMV339IPWR at JLCPCB](https://jlcpcb.com/partdetail/C273648),
[W25Q64JV search at JLCPCB](https://jlcpcb.com/parts/componentSearch?searchTxt=W25Q64JV).
