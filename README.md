
# QMK Accessibility HID Module

Written by Jeremiah Ticket

This module provides accessibility features for QMK firmware, including handling layer changes and `Caps Word` functionality. The module is designed to be included in your keymap.

## What it does

The module on the keyboard sends a hid event using raw_hid_send when a layer state changes, or when caps_word is turned on or off via your configured method. 
The python script listens for these events, but also keeps track of the layer for layer up/down, so as to avoid double sounds.

### Why sounds, and not speech?

Not all keyboards have speakers. I have a moonlander, and a Planck EZ. They have speakers. But I have friends who have keyboards that do not. Also, sounds are simply faster. If I'm typing, I don't want to hear other things speaking, or if I'm using my screen reader, and a layer event happens, this could cause interruptions in speech.

### To do:

- Add support for dynamic_macros, when recording starts, ends, etc. 
- Refactor for latency.

For some reason, when writing this initially, I got multiple events on layer change, which is why there's a layer check and some timing on the keyboard side that add a small amount of delay. I'd really love to fix this, but am at a loss for a better way to go about this.

## Features

- Handles layer changes and notifies via HID
- Notifies `Caps Word` state via HID

## Requirements

- QMK Firmware
- `raw_hid` enabled
- `caps_word` feature enabled [Optional]
- `console` feature enabled for debug [Optional]

## Setup

1. **Clone the module repository**

   Clone or download the `qmk_accessibility_hid` folder from the repository and place it in the same directory as your `keymap.c`.

   ```bash
   git clone https://github.com/jticket1024/qmk_accessibility_hid.git
   ```

2. **Modify `rules.mk`**

   Add the following lines to your `rules.mk` to include the accessibility module:

   ```makefile
   RAW_ENABLE = yes
   SRC += qmk_accessibility/accessibility_events.c
   ```

3. **Modify `keymap.c`**

   Include the accessibility module header and update your keymap as shown in the example below:

   ```c
   #include "qmk_accessibility/accessibility_events.h"

   layer_state_t layer_state_set_user(layer_state_t state) {
       uint8_t current_layer = get_highest_layer(state);
       accessibility_send_layer_change(current_layer);
       return state;
   }

   void caps_word_set_user(bool active) {
       if (active) {
           accessibility_send_caps_word_on();
       } else {
           accessibility_send_caps_word_off();
       }
   }
   ```

4. **Compile your keymap**

Compile your QMK keymap and flash your firmware.

5. **Setup python**

   This module includes a Python script to handle HID events. Set up a virtual environment and install the required dependencies:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scriptsctivate`
   pip install -r requirements.txt
   ```

## Configuration

1. **Generate the Configuration File**

   Run the script to generate a configuration file:

   ```bash
   python accessibility_watcher.py
   ```

2. **Edit the Configuration File**

   After generating the configuration file, edit it to supply the `vid`, `pid`, `usage page`, and `usage`. The configuration file will be located in the same directory as the script and will be named `accessibility_watcher.ini`.

   Usage

If everything has gone well and your firmware flashed, run the script to start listening for HID events.

   ```bash
   python accessibility_watcher.py
   ```

## License

This project is licensed under the terms of the GNU General Public License v2. See the [LICENSE](LICENSE) file for details.
