/* SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

/* USB Device descriptor parameter */
//#define VENDOR_ID 0x1209
//#define PRODUCT_ID 0x4704
//#define DEVICE_VER 0x0002
//#define MANUFACTURER Rico
//#define PRODUCT modelfkeyboards.com Brand New F77 Model F Keyboard by Model F Labs

/*
* Key matrix size
* Although columns 10 to 14 are not used by the F77 keyboard we define all 16 columns here.
* This allow for a more generic matrix scanning code that can be used by both F77 and F62 keyboards
*/
#define MATRIX_ROWS 8
#define MATRIX_COLS 16

/* Mechanical locking support. Use KC_LCAP, KC_LNUM or KC_LSCR instead in keymap */
//#define LOCKING_SUPPORT_ENABLE
/* Locking resynchronize hack */
//#define LOCKING_RESYNC_ENABLE

/* Use 1000hz polling */
#define USB_POLLING_INTERVAL_MS 1

#define I2C_DRIVER I2CD1
#define I2C1_SDA_PIN GP16
#define I2C1_SCL_PIN GP17
#define I2C1_CLOCK_SPEED 400000

#define HAPTIC_ENABLE_PIN GP28
#define SOLENOID_PIN GP29
#define SOLENOID_DEFAULT_DWELL 15
#define SOLENOID_MIN_DWELL 4
#define SOLENOID_MAX_DWELL 100

// Dynamic EEPROM
#define DYNAMIC_KEYMAP_EEPROM_MAX_ADDR 4095
