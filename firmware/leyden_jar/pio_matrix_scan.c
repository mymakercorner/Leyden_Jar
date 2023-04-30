/* Copyright 2022 Eric Becourt (Rico https://mymakercorner.com)
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#include "quantum.h"
#include "hardware/pio.h"
#include "hardware/clocks.h"
#include "pio_matrix_scan.h"
#include "col_0_7_pio.pio.h"
#include "col_8_15_pio.pio.h"

const uint8_t s_TxColScanData[16] =
{
    0x01, 0x00,
    0x02, 0x00,
    0x04, 0x00,
    0x08, 0x00,
    0x10, 0x00,
    0x20, 0x00,
    0x40, 0x00,
    0x80, 0x00,
};

static uint8_t s_RawMatrixScanValues[16];

void pio_matrix_scan_init()
{
    /* Get PIO0 peripheral out of reset state. */
    hal_lld_peripheral_unreset(RESETS_ALLREG_PIO0);

    /* Configuration of column pins using ChibiOS hal */

    iomode_t colums_pin_mode = PAL_RP_GPIO_OE | PAL_RP_PAD_SLEWFAST | PAL_RP_PAD_DRIVE8 | PAL_MODE_ALTERNATE_PIO0;
    for (int i=0; i<8; i++)
    {
        palSetLineMode(i+8, colums_pin_mode);
        wait_us(50);
        palSetLineMode(i+18, colums_pin_mode);
        wait_us(50);
    }

    /* Configuration of row pins using ChibiOS hal */

    iomode_t rows_pin_mode = PAL_RP_PAD_IE | PAL_RP_PAD_SCHMITT | PAL_MODE_ALTERNATE_PIO0;
    for (int i=0; i<8; i++)
    {
        palSetLineMode(i, rows_pin_mode);
    }

    /* Load and start PIO programs */

    uint32_t offset0 = pio_add_program(pio0, &col_0_7_pio_program);
    uint32_t offset1 = pio_add_program(pio0, &col_8_15_pio_program);
    col_0_7_pio_init(pio0, 0, offset0, 0, 8);
    col_8_15_pio_init(pio0, 1, offset1, 0, 18);

    pio_sm_set_enabled(pio0, 0, true);
    pio_sm_set_enabled(pio0, 1, true);
}

void pio_raw_scan()
{
    /* We push FIFO data to the PIO state machine that handles column 8 to 15 first,
     that is the state machine that runs the col_8_15_pio program.
     As this program waits col_0_7_pio to finish no data will be immediately consumed. */

    pio_sm_put_blocking(pio0, 1, *(uint32_t*)(s_TxColScanData + 0));
    pio_sm_put_blocking(pio0, 1, *(uint32_t*)(s_TxColScanData + 4));
    pio_sm_put_blocking(pio0, 1, *(uint32_t*)(s_TxColScanData + 8));
    pio_sm_put_blocking(pio0, 1, *(uint32_t*)(s_TxColScanData + 12));

    /* We push FIFO data to the PIO state machine that handles column 0 to 7,
     that is the state machine that runs the col_0_7_pio program.
     As soon as data is pushed the program will resume it's execution and consume data.
     This program will awaken the col_8_15_pio program when all columns will be scanned. */

    pio_sm_put_blocking(pio0, 0, *(uint32_t*)(s_TxColScanData + 0));
    pio_sm_put_blocking(pio0, 0, *(uint32_t*)(s_TxColScanData + 4));
    pio_sm_put_blocking(pio0, 0, *(uint32_t*)(s_TxColScanData + 8));
    pio_sm_put_blocking(pio0, 0, *(uint32_t*)(s_TxColScanData + 12));

    /* Read results send by col_0_7_pio program to the FIFO */

    *(uint32_t*)(s_RawMatrixScanValues + 0) = pio_sm_get_blocking(pio0, 0);
    *(uint32_t*)(s_RawMatrixScanValues + 4) = pio_sm_get_blocking(pio0, 0);

    /* Read results send by col_8_15_pio program to the FIFO */

    *(uint32_t*)(s_RawMatrixScanValues + 8) = pio_sm_get_blocking(pio0, 1);
    *(uint32_t*)(s_RawMatrixScanValues + 12) = pio_sm_get_blocking(pio0, 1);
}

const uint8_t* pio_get_scan_vals(void)
{
    return s_RawMatrixScanValues;
}

