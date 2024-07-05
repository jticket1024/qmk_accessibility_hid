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

#ifndef ACCESSIBILITY_EVENTS_H
#define ACCESSIBILITY_EVENTS_H

#include "raw_hid.h"

void accessibility_send_layer_change(uint8_t layer);

#ifdef CAPS_WORD_ENABLE
void accessibility_send_caps_word_on(void);
void accessibility_send_caps_word_off(void);
#endif // CAPS_WORD_ENABLE

#endif // ACCESSIBILITY_EVENTS_H
