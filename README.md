
# QMK Accessibility HID Module

Written by Jeremiah Ticket

This module provides accessibility features for QMK firmware, including handling layer changes and `Caps Word` functionality. The module is designed to be included in your keymap.

## What it does

The module on the keyboard sends a hid event using raw_hid_send when a layer state changes, or when caps_word is turned on or off via your configured method. 
The python script listens for these events, but also keeps track of the layer for layer up/down, so as to avoid double sounds.

### Why sounds, and not speech?

Sounds are simply faster. If I'm typing, I don't want to hear other things speaking, or if I'm using my screen reader, and a layer event happens, this could cause interruptions in speech.

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
   git clone https://git.terrible.fail/jticket/qmk_accessibility_hid.git
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

## Running as a Service

### Systemd (Linux)

1. Create a service file `/etc/systemd/system/qmk_accessibility.service`:

   ```ini
   [Unit]
   Description=QMK Accessibility HID Service
   After=network.target

   [Service]
   ExecStart=/path/to/venv/bin/python /path/to/accessibility_watcher.py
   WorkingDirectory=/path/to/
   User=your_username
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

2. Enable and start the service:

   ```bash
   sudo systemctl enable qmk_accessibility
   sudo systemctl start qmk_accessibility
   ```

### launchd (macOS)

1. Create a plist file `~/Library/LaunchAgents/com.qmk.accessibility.plist`:

   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
       <key>Label</key>
       <string>com.qmk.accessibility</string>
       <key>ProgramArguments</key>
       <array>
           <string>/path/to/venv/bin/python</string>
           <string>/path/to/accessibility_watcher.py</string>
       </array>
       <key>RunAtLoad</key>
       <true/>
       <key>WorkingDirectory</key>
       <string>/path/to/</string>
       <key>StandardOutPath</key>
       <string>/tmp/qmk_accessibility.out</string>
       <key>StandardErrorPath</key>
       <string>/tmp/qmk_accessibility.err</string>
   </dict>
   </plist>
   ```

2. Load the service:

   ```bash
   launchctl load ~/Library/LaunchAgents/com.qmk.accessibility.plist
   ```

### Windows Service

1. Install the `pywin32` package:

   ```bash
   pip install pywin32
   ```

2. Create a Python script to install the service (e.g., `install_service.py`):

   ```python
   import win32serviceutil
   import win32service
   import win32event
   import servicemanager
   import sys

   class QMKAccessibilityService(win32serviceutil.ServiceFramework):
       _svc_name_ = "QMKAccessibilityService"
       _svc_display_name_ = "QMK Accessibility HID Service"

       def __init__(self, args):
           win32serviceutil.ServiceFramework.__init__(self, args)
           self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

       def SvcStop(self):
           self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
           win32event.SetEvent(self.hWaitStop)

       def SvcDoRun(self):
           servicemanager.LogMsg(
               servicemanager.EVENTLOG_INFORMATION_TYPE,
               servicemanager.PYS_SERVICE_STARTED,
               (self._svc_name_, "")
           )
           self.main()

       def main(self):
           # Add the path to your script
           exec(open(r'C:\path\to\accessibility_watcher.py').read())

   if __name__ == '__main__':
       win32serviceutil.HandleCommandLine(QMKAccessibilityService)
   ```

3. Install and start the service:

   ```bash
   python install_service.py install
   python install_service.py start
   ```

## License

This project is licensed under the terms of the GNU General Public License v2. See the [LICENSE](LICENSE) file for details.
