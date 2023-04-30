#include QMK_KEYBOARD_H

const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
    [0] = LAYOUT(
        KC_1, KC_2,
        KC_3, KC_4
    ),

    [1] = LAYOUT(
        KC_A, KC_B,
        KC_C, KC_D
    )
};
