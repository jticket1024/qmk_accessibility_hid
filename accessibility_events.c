/* Copyright 2024  Jeremiah Ticket <jticket@terrible.fail>*
* This file is part of qmk_accessibility_hid. *
 * qmk_accessibility_hid is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 2 of the License, or
 * (at your option) any later version.
 *
 * qmk_accessibility_hid is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with qmk_accessibility_hid.  If not, see <http://www.gnu.org/licenses/>.
*/

#include "accessibility_events.h"
#include "print.h"
#include "raw_hid.h"
#include "quantum.h"

static uint8_t previous_layer = 255;  // Initialize to an invalid layer

#ifdef CAPS_WORD_ENABLE
static bool caps_word_state = false;  // Track Caps Word state
#endif

void raw_hid_receive(uint8_t *data, uint8_t length) {
    if (data[0] == 99) { // Command to get current layer
        uint8_t response[32] = {0};
        response[0] = 99;
        response[1] = get_highest_layer(layer_state);
        raw_hid_send(response, sizeof(response));
        #ifdef CONSOLE_ENABLE
        uprintf("Sent current layer: %d\n", response[1]);
        #endif
    }
}

void accessibility_send_layer_change(uint8_t layer) {
    static uint32_t last_time = 0;
    uint32_t current_time = timer_read();

    if (current_time - last_time < 200) { // Debounce
        return;
    }

    if (layer != previous_layer) {
        uint8_t data[32] = {0}; // RAW HID packet size is 32 bytes
        data[0] = 1; // Event type 1 for layer change
        data[1] = layer; // Store the current layer in the second byte
        raw_hid_send(data, sizeof(data));
        previous_layer = layer;  // Update previous layer
        #ifdef CONSOLE_ENABLE
        uprintf("Sent layer change event: %d\n", layer);
        #endif
    }

    last_time = current_time;  // Update last time
}

#ifdef CAPS_WORD_ENABLE
void accessibility_send_caps_word_on(void) {
    if (!caps_word_state) {
        uint8_t data[32] = {0}; // RAW HID packet size is 32 bytes
        data[0] = 2; // Event type 2 for Caps Word state
        data[1] = 1; // 1 for on
        raw_hid_send(data, sizeof(data));
        caps_word_state = true;  // Update Caps Word state
        #ifdef CONSOLE_ENABLE
        uprintf("Sent Caps Word on event\n");
        #endif
    }
}

void accessibility_send_caps_word_off(void) {
    if (caps_word_state) {
        uint8_t data[32] = {0}; // RAW HID packet size is 32 bytes
        data[0] = 2; // Event type 2 for Caps Word state
        data[1] = 0; // 0 for off
        raw_hid_send(data, sizeof(data));
        caps_word_state = false;  // Update Caps Word state
        #ifdef CONSOLE_ENABLE
        uprintf("Sent Caps Word off event\n");
        #endif
    }
}
#endif
