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
#include "dac.h"

#define DAC_I2C_ADDR    (0x60<<1)
#define DAC_I2C_READ    (DAC_I2C_ADDR | 1)
#define DAC_I2C_WRITE    (DAC_I2C_ADDR | 0)
#define DAC_I2C_TIMEOUT 100

int dac_init(void)
{
    i2c_init();

    uint8_t dummy;
    i2c_status_t ret = i2c_receive(DAC_I2C_READ, &dummy, 1, DAC_I2C_TIMEOUT);
    if (ret != I2C_STATUS_SUCCESS)
        return 0;
    return 1;
}

int dac_write_val(uint16_t dacVal)
{
    // Write Volatile DAC Register command is 2 bytes
    // First byte contains(MSb first):
    // - 2 bits for command type (both 0 for write volatile DAC register command)
    // - 2 bits PD0 and PD1 for power down (both 0 for normal operation)
    // - 4 bits contains the 4 MSb of the DAC register value
    // Second byte contains(MSb first):
    // - 6 bits contains the LSb of the DAC register value
    // - 2 bits (both 0).

    uint8_t data[2];
    data[0] = (uint8_t)(dacVal >> 6);
    data[1] = (uint8_t)((dacVal << 2) & 0xFF);

    i2c_status_t ret = i2c_transmit(DAC_I2C_WRITE, data, 2, DAC_I2C_TIMEOUT);
    if (ret != I2C_STATUS_SUCCESS)
        return 0;
    return 1;
}
