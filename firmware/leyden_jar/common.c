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

#include <stdlib.h>
#include "quantum.h"
#include "haptic.h"
#include "common.h"
#include "dac.h"
#include "io_expander.h"
#include "pio_matrix_scan.h"

extern haptic_config_t haptic_config;

#define UNCONNECTED_LEVEL 380

static uint16_t s_matrix_levels[MATRIX_COLS][MATRIX_ROWS];
static uint16_t s_sorted_levels[MATRIX_COLS * MATRIX_ROWS];
static uint16_t s_dac_threshold;

enum leyden_jar_keyboard_value_id {
  id_leyden_jar_offset = 0x80, //Sufficiently high value to be safe to use
  id_leyden_jar_col_levels,
  id_leyden_jar_dac_threshold
};

#ifdef VIA_ENABLE
void raw_hid_receive_kb(uint8_t *data, uint8_t length)
{
  uint8_t *command_id = &(data[0]);

  switch ( *command_id )
  {
    case id_get_keyboard_value:
    {
        uint8_t *command_data = &(data[1]);

        switch( command_data[0])
        {
            case id_leyden_jar_col_levels:
            {
                uint16_t col_index = *(uint16_t *)(data + 2);
                if (col_index >= MATRIX_COLS) {
                    *command_id = id_unhandled;
                }
                else {
                    uint16_t *col_level_ptr = (uint16_t *)(data + 4);
                    for (int i=0; i<MATRIX_ROWS; i++) {
                        col_level_ptr[i] = s_matrix_levels[col_index][i];
                    }
                }
                break;
            }
            case id_leyden_jar_dac_threshold:
            {
                uint16_t *threshold_ptr = (uint16_t *)(data + 2);
                *threshold_ptr = s_dac_threshold;
                break;
            }
            default:
            {
                *command_id = id_unhandled;
                break;
            }
        }
        break;
    }
    case id_set_keyboard_value:
    {
        uint8_t *command_data = &(data[1]);

        switch( command_data[0])
        {
            case id_leyden_jar_dac_threshold:
            {
                uint16_t threshold = *(uint16_t *)(data + 2);
                if (threshold > 1023) {
                    *command_id = id_unhandled;
                }
                else {
                    s_dac_threshold = threshold;
                    dac_write_val(s_dac_threshold);
                    wait_us(100);
                }
                break;
            }
            default:
            {
                *command_id = id_unhandled;
                break;
            }
        }
        break;
    }
    default:
    {
      // Unhandled message.
      *command_id = id_unhandled;
      break;
    }
  }
}
#endif


static void leyden_jar_detect_levels(void) {
    for (int col = 0; col < 16; col++) {
        for (int row=0; row<8; row++) {
            s_matrix_levels[col][row] = 0;
        }
    }

    for (uint16_t dac_val=300; dac_val < 500; dac_val++) {
        dac_write_val(dac_val);
        wait_us(100);
        pio_raw_scan();

        const uint8_t* p_raw_vals = pio_get_scan_vals();

        for (int col = 0; col < MATRIX_COLS; col++) {
            for (int row = 0; row < MATRIX_ROWS; row++) {
                if (p_raw_vals[col] & (uint8_t)(1<<row)) {
                    s_matrix_levels[col][row] = dac_val;
                }
            }
        }
    }
}

static int leyden_jar_compare_vals(const void* pVal1, const void* pVal2) {
    if (*(uint16_t*)pVal1 < *(uint16_t*)pVal2) {
        return -1;
    }
    else if (*(uint16_t*)pVal1 > *(uint16_t*)pVal2) {
        return 1;
    }
    else {
        return 0;
    }

}

static void leyden_jar_sort_level_values(void) {
    for (int col = 0; col < MATRIX_COLS; col++) {
        for (int row = 0; row < MATRIX_ROWS; row++) {
            s_sorted_levels[col * MATRIX_ROWS + row] = s_matrix_levels[col][row];
        }
    }

    qsort((void*)s_sorted_levels, MATRIX_COLS * MATRIX_ROWS, sizeof(uint16_t), leyden_jar_compare_vals);
}

/* We compute the threshold to were we consider that a key has been pressed.
 *
 * First step:
 * We detect the maximum level for all keys in the switch matrix and we sort those values in ascending order.
 * This will later be useful to retrieve the median and maximum values.
 *
 * Scenario 1:
 *   We try to manage the case were the controller is powered on while no columns/rows are soldered to a key matrix.
 *   This happens when you want to pre-flash the controller firmware before soldering the controller PCB
 *   to the key matrix.
 *   If we do nothing the controller can spam fake keypresses to the computer.
 *   We prevent this by taking the maximum detected level and comparing it to a low reference value.
 *   If the maximum detected level is equal or lower than this reference value then we know that no soldering to a
 *   key matrix have been done.
 *   We then configure the dac threshold with a value that will never trigger a key press:
 *     - 1023 for Model F keyboards.
 *     - 300 for Beamspring keyboards.
 *
 * Scenario  2:
 *   We detected that the controller PCB was properly soldered.
 *   The dac threshold value is then the median value of all detected levels with a fixed offset added to it.
 *   The offset value is defined by the ACTIVATION_OFFSET macro defined outside this file.
 *   The offset is positive for Model F keyboards and negative for Beamspring keyboards.
 *   Using the median value of all detected values has several advantages:
 *     - It gives close to an average value of levels.
 *     - It allows to ignore uninstalled flippers in the key matrix (lowest values).
 *     - It allows to ignore calibration pads in the key matrix (lowest or highest values).
 *     - It allows to ignore several pressed keys during boot up (does not work if all keys are pressed).
 *     - Consequently allows to use QMK BOOT_MAGIC lite feature. */

static void leyden_jar_compute_dac_threshold(int16_t activation_offset) {
    uint16_t median_val = s_sorted_levels[MATRIX_COLS * MATRIX_ROWS / 2];
    uint16_t max_val = s_sorted_levels[(MATRIX_COLS * MATRIX_ROWS) - 1];

    if (max_val <= UNCONNECTED_LEVEL) {
        if (activation_offset > 0) {
            s_dac_threshold = 1023;
        } else {
            s_dac_threshold = 300;
        }

    } else {
        s_dac_threshold = (uint16_t)((int16_t)median_val + activation_offset);
    }

}

void leyden_jar_init(void) {
    dac_init();
    io_expander_init();
    pio_matrix_scan_init();
}

void leyden_jar_calibrate(int16_t activation_offset)
{
    leyden_jar_detect_levels();
    leyden_jar_sort_level_values();
    leyden_jar_compute_dac_threshold(activation_offset);
    dac_write_val(s_dac_threshold);
    wait_us(100);
}

void leyden_jar_update(void)
{
    io_expander_update_state();
}

