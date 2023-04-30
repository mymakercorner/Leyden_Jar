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

#include "i2c_master.h"
#include "io_expander.h"

#define IO_EXPANDER_I2C_ADDR    (0x18<<1)
#define IO_EXPANDER_I2C_READ    (IO_EXPANDER_I2C_ADDR | 1)
#define IO_EXPANDER_I2C_WRITE   (IO_EXPANDER_I2C_ADDR | 0)
#define IO_EXPANDER_I2C_TIMEOUT 100

#define SOLENOID_LED0_VAL   (1<<4)
#define SOLENOID_LED1_VAL   (1<<5)
#define SOLENOID_LED2_VAL   (1<<6)

static uint8_t s_current_io_expander_state;
static bool s_led0;
static bool s_led1;
static bool s_led2;

static int io_expander_set_output_pins_level(uint8_t pins_level) {
    /* Write Output Port Register command is 2 bytes
     * First byte contains 0x01 that tell that we will update the Output Port Register
     * Second byte contains the output port register value, each bit (LSb is O0, Msb is O7) telling if output level is high or low */
    uint8_t write_data[2];
    write_data[0] = 0x01;
    write_data[1] = pins_level;

    i2c_status_t ret = i2c_transmit(IO_EXPANDER_I2C_WRITE, write_data, 2, IO_EXPANDER_I2C_TIMEOUT);
    if (ret != I2C_STATUS_SUCCESS)
        return 0;

    return 1;
}

int io_expander_init()
{
    i2c_init();

    /* We check that the I2C device is recognized */
    uint8_t dummy;
    i2c_status_t ret = i2c_receive(IO_EXPANDER_I2C_READ, &dummy, 1, IO_EXPANDER_I2C_TIMEOUT);
    if (ret != I2C_STATUS_SUCCESS)
        return 0;

    /* We set all pins to output type
     * Write Control Register command is 2 bytes
     * First byte contains 0x03 that tell that we will update the Control Register
     * Second byte contains the control register value, here 0x00 to tell that all IO pins are configured as output */
    uint8_t write_data[2];
    write_data[0] = 0x03;
    write_data[1] = 0x00;
    ret = i2c_transmit(IO_EXPANDER_I2C_WRITE, write_data, 2, IO_EXPANDER_I2C_TIMEOUT);
    if (ret != I2C_STATUS_SUCCESS)
        return 0;

    /* We set all pins to output 0 */
    if (io_expander_set_output_pins_level(0) != 1)
        return 0;

    s_current_io_expander_state = 0;
    s_led0 = false;
    s_led1 = false;
    s_led2 = false;

    return 1;
}

void io_expander_set_led0_status(bool enable) {
    s_led0 = enable;
}

void io_expander_set_led1_status(bool enable) {
    s_led1 = enable;
}

void io_expander_set_led2_status(bool enable) {
    s_led2 = enable;
}

void io_expander_update_state(void) {
    uint8_t new_state = 0;

    if (s_led0) {
        new_state |= SOLENOID_LED0_VAL;
    }
    if (s_led1) {
        new_state |= SOLENOID_LED1_VAL;
    }
    if (s_led2) {
        new_state |= SOLENOID_LED2_VAL;
    }

    if (new_state != s_current_io_expander_state)
    {
        s_current_io_expander_state = new_state;
        io_expander_set_output_pins_level(s_current_io_expander_state);
    }
}

