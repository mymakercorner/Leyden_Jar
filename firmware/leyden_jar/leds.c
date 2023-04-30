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
#include "io_expander.h"

/* Leds are not directly driven by the RP2040 IO pins, but with IO pins driven from
 * an I2C IO expander.
 * See io_expander.h and .cpp files for the io_expander implementation.
*/

bool led_update_kb(led_t led_state) {
    bool res = led_update_user(led_state);
    if(res) {
        io_expander_set_led0_status(led_state.num_lock);
        io_expander_set_led1_status(led_state.caps_lock);
        io_expander_set_led2_status(led_state.scroll_lock);
    }
    return res;
}
