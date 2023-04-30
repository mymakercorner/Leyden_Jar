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

#include "quantum.h"

/*
* Although columns 9 to 14 are not used by the F62 keyboard we define all 16 columns here.
* This allow for a more generic matrix scanning code that can be used by F77, F62, Beamspring SSK and Beamspring Full Size keyboards.
* VIA json file reflects this exact column/row physical disposition.
* Only the generic 'all layouts' as defined in the VIA json file is defined here.
* Please use VIA/VIAL software to select the layout options you want.
*/

#define LAYOUT_all( \
    k_grv,    k_1,    k_2,    k_3,    k_4, k_5, k_6, k_7, k_8, k_9,     k_0,         k_minus,   k_equals,  k_bslash, k_backsp,\
    k_tab,    k_q,    k_w,    k_e,    k_r, k_t, k_y, k_u, k_i, k_o,     k_p,         k_lbrc,    k_rbrc,    k_backspace,       \
    k_lctrl,  k_a,    k_s,    k_d,    k_f, k_g, k_h, k_j, k_k, k_l,     k_semicolon, k_quote,   k_hashtag, k_return,          \
    k_lshift, k_nubs, k_z,    k_x,    k_c, k_v, k_b, k_n, k_m, k_comma, k_period,    k_slash,   k_rshift,  k_fn,              \
    k_caps,   k_lgui, k_lalt,         k_space,                          k_ralt,      k_numlock, k_rctrl                       \
) \
{ \
    { k_lctrl , k_lalt, k_v, k_space, k_m, k_comma    , KC_NO    , k_numlock, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, k_rctrl},\
    { k_lgui  , k_z   , k_c, k_b    , k_n, k_period   , k_ralt   , k_rshift , KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO  },\
    { k_nubs  , k_x   , k_d, k_g    , k_k, k_l        , k_slash  , k_fn     , KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO  },\
    { k_lshift, k_s   , k_f, k_h    , k_j, k_semicolon, k_quote  , k_return , KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO  },\
    { k_caps  , k_a   , k_e, k_t    , k_u, k_o        , k_hashtag, k_bslash , KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO  },\
    { k_tab   , k_w   , k_r, k_y    , k_i, k_p        , k_lbrc   , k_rbrc   , KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO  },\
    { k_grv   , k_q   , k_3, k_5    , k_7, k_9        , k_minus  , KC_NO    , KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO  },\
    { k_1     , k_2   , k_4, k_6    , k_8, k_0        , k_equals , k_backsp , KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO, KC_NO  }\
}
