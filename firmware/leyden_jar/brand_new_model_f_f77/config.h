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

#pragma once

/*
* Key matrix size
* Although columns 10 to 14 are not used by the F77 keyboard we define all 16 columns here.
* This allow for a more generic matrix scanning code that can be used by both F77 and F62 keyboards
*/
#define MATRIX_ROWS 8
#define MATRIX_COLS 16

/* Use 1000hz polling */
#define USB_POLLING_INTERVAL_MS 1

/* RP2040 I2C device 0 is used by QMK API.
 * It is used to drive the the DAC chip that gives the voltage theshold value for the capsense management
 * and the IO expander thats drives the status leds.
*/
#define I2C_DRIVER I2CD1
#define I2C1_SDA_PIN GP16
#define I2C1_SCL_PIN GP17
#define I2C1_CLOCK_SPEED 400000

#define HAPTIC_ENABLE_PIN GP28
#define SOLENOID_PIN GP29
#define SOLENOID_DEFAULT_DWELL 15
#define SOLENOID_MIN_DWELL 4
#define SOLENOID_MAX_DWELL 100

#define RP2040_BOOTLOADER_DOUBLE_TAP_RESET // Activates the double-tap behavior
#define RP2040_BOOTLOADER_DOUBLE_TAP_RESET_TIMEOUT 200U // Timeout window in ms in which the double tap can occur.

#define ACTIVATION_OFFSET   10

// Dynamic EEPROM
#define DYNAMIC_KEYMAP_EEPROM_MAX_ADDR 4095

