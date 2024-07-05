#!/usr/bin/env python

# Copyright 2024  Jeremiah Ticket <jticket@terrible.fail>
# This file is part of qmk_accessibility_hid.

# qmk_accessibility_hid is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation,
# either version 2 of the License, or (at your option) any later version.

# qmk_accessibility_hid is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with qmk_accessibility_hid. If not, see <https://www.gnu.org/licenses/>.


import hid
import os
import time
import signal
import sys
import configparser
import pyaudio
import wave
import logging
from threading import Thread, Lock, Event
import argparse
from queue import Queue

DEFAULT_CONFIG = """
[Device]
vid = 0x1234
pid = 0x5678
usage_page = 0x1
usage = 0x6

[Sounds]
volume = 0.5
layer_up = sounds/layer_up.wav
layer_down = sounds/layer_down.wav
caps_word_on = sounds/caps_word_on.wav
caps_word_off = sounds/caps_word_off.wav
program_start = sounds/program_start.wav
program_exit = sounds/program_exit.wav
error = sounds/error.wav
keyboard_connect = sounds/keyboard_connect.wav
keyboard_disconnect = sounds/keyboard_disconnect.wav

[EnabledSounds]
layer_up = true
layer_down = true
caps_word_on = true
caps_word_off = true
program_start = true
program_exit = true
error = true
keyboard_connect = true
keyboard_disconnect = true

[Logging]
loglevel = INFO
logfile = accessibility_watcher.log
"""

class AccessibilityWatcher:
    def __init__(self, config_file):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

        self.VENDOR_ID = int(self.config['Device']['vid'], 16)
        self.PRODUCT_ID = int(self.config['Device']['pid'], 16)
        self.USAGE_PAGE = int(self.config['Device']['usage_page'], 16)
        self.USAGE = int(self.config['Device']['usage'], 16)
        self.VOLUME = self.config.getfloat('Sounds', 'volume', fallback=0.5)  # Global volume control

        self.SOUNDS = {
            "layer_up": self.config.get('Sounds', 'layer_up', fallback='sounds/layer_up.wav'),
            "layer_down": self.config.get('Sounds', 'layer_down', fallback='sounds/layer_down.wav'),
            "caps_word_on": self.config.get('Sounds', 'caps_word_on', fallback='sounds/caps_word_on.wav'),
            "caps_word_off": self.config.get('Sounds', 'caps_word_off', fallback='sounds/caps_word_off.wav'),
            "program_start": self.config.get('Sounds', 'program_start', fallback='sounds/program_start.wav'),
            "program_exit": self.config.get('Sounds', 'program_exit', fallback='sounds/program_exit.wav'),
            "error": self.config.get('Sounds', 'error', fallback='sounds/error.wav'),
            "keyboard_connect": self.config.get('Sounds', 'keyboard_connect', fallback='sounds/keyboard_connect.wav'),
            "keyboard_disconnect": self.config.get('Sounds', 'keyboard_disconnect', fallback='sounds/keyboard_disconnect.wav')
        }

        self.ENABLED_SOUNDS = {
            "layer_up": self.config.getboolean('EnabledSounds', 'layer_up', fallback=True),
            "layer_down": self.config.getboolean('EnabledSounds', 'layer_down', fallback=True),
            "caps_word_on": self.config.getboolean('EnabledSounds', 'caps_word_on', fallback=True),
            "caps_word_off": self.config.getboolean('EnabledSounds', 'caps_word_off', fallback=True),
            "program_start": self.config.getboolean('EnabledSounds', 'program_start', fallback=True),
            "program_exit": self.config.getboolean('EnabledSounds', 'program_exit', fallback=True),
            "error": self.config.getboolean('EnabledSounds', 'error', fallback=True),
            "keyboard_connect": self.config.getboolean('EnabledSounds', 'keyboard_connect', fallback=True),
            "keyboard_disconnect": self.config.getboolean('EnabledSounds', 'keyboard_disconnect', fallback=True)
        }

        log_level_str = self.config.get('Logging', 'loglevel', fallback='INFO').upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
        logfile = self.config.get('Logging', 'logfile', fallback='accessibility_watcher.log')

        logging.basicConfig(level=log_level, format='%(asctime)s %(levelname)s: %(message)s', handlers=[
            logging.FileHandler(logfile),
            logging.StreamHandler(sys.stdout)
        ])

        self.device = None
        self.previous_layer = -1
        self.current_layer = -1
        self.layer_lock = Lock()  # Lock to manage concurrent access to layer state
        self.terminate_event = Event()  # Event to signal termination
        self.command_queue = Queue()
        self.initial_layer_retrieved = False  # Flag to indicate the first time the layer is retrieved

    def play_sound(self, file, enable=True):
        if not enable:
            logging.debug(f"Sound playback disabled for: {file}")
            return
        if not os.path.exists(file):
            logging.error(f"Sound file does not exist: {file}")
            return
        def play():
            try:
                logging.info(f"Attempting to play sound: {file}")
                wf = wave.open(file, 'rb')
                p = pyaudio.PyAudio()
                stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                                channels=wf.getnchannels(),
                                rate=wf.getframerate(),
                                output=True)
                data = wf.readframes(1024)
                while data and not self.terminate_event.is_set():
                    stream.write(data)
                    data = wf.readframes(1024)
                stream.stop_stream()
                stream.close()
                p.terminate()
                logging.info(f"Played sound: {file}")
            except Exception as e:
                logging.error(f"Error playing sound: {e}")
        Thread(target=play).start()

    def handle_layer_change(self, layer):
        with self.layer_lock:
            self.previous_layer = self.current_layer
            self.current_layer = layer
            logging.info(f"Layer changed from {self.previous_layer} to {self.current_layer}")
            if self.initial_layer_retrieved:
                if self.previous_layer != self.current_layer:
                    if self.current_layer > self.previous_layer:
                        self.play_sound(self.SOUNDS["layer_up"], self.ENABLED_SOUNDS["layer_up"])
                    else:
                        self.play_sound(self.SOUNDS["layer_down"], self.ENABLED_SOUNDS["layer_down"])
            else:
                self.initial_layer_retrieved = True

    def handle_caps_word(self, state):
        try:
            if state == 1:
                logging.info("Caps word on triggered")
                self.play_sound(self.SOUNDS["caps_word_on"], self.ENABLED_SOUNDS["caps_word_on"])
            elif state == 0:
                logging.info("Caps word off triggered")
                self.play_sound(self.SOUNDS["caps_word_off"], self.ENABLED_SOUNDS["caps_word_off"])
        except Exception as e:
            logging.error(f"Error handling caps word state: {e}")

    def handle_hid_event(self, data):
        logging.debug(f"Received HID event: {data}")
        if len(data) != 32:
            logging.warning(f"Unexpected HID event data length: {len(data)}")
            return False
        if data[0] in [1, 2, 99]:
            if data[0] == 1:  # Layer change event
                self.handle_layer_change(data[1])
            elif data[0] == 2:  # Caps Word state event
                self.handle_caps_word(data[1])
            elif data[0] == 99:  # Command to get current layer
                logging.info(f"Current layer: {data[1]}")
                self.handle_layer_change(data[1])
                return True
            else:
                logging.warning(f"Unexpected HID event data: {data}")
        else:
            logging.warning(f"Invalid HID event data: {data}")
        return False

    def connect_device(self):
        try:
            for device_info in hid.enumerate():
                if (device_info['vendor_id'] == self.VENDOR_ID and
                    device_info['product_id'] == self.PRODUCT_ID and
                    device_info['usage_page'] == self.USAGE_PAGE and
                    device_info['usage'] == self.USAGE):
                    self.device = hid.device()
                    self.device.open_path(device_info['path'])
                    logging.info("Connected to device")
                    self.play_sound(self.SOUNDS["keyboard_connect"], self.ENABLED_SOUNDS["keyboard_connect"])
                    self.request_current_layer()
                    return True
            logging.error("Failed to find matching device")
            return False
        except Exception as e:
            logging.error(f"Failed to connect to device: {e}")
            self.play_sound(self.SOUNDS["error"], self.ENABLED_SOUNDS["error"])
            return False

    def disconnect_device(self):
        if self.device:
            try:
                self.device.close()
            except Exception as e:
                logging.error(f"Error disconnecting device: {e}")
            logging.info("Disconnected from device")
            self.play_sound(self.SOUNDS["keyboard_disconnect"], self.ENABLED_SOUNDS["keyboard_disconnect"])
            self.device = None

    def request_current_layer(self):
        max_retries = 5
        for attempt in range(max_retries):
            try:
                time.sleep(0.1)  # Small delay before attempting to write
                data = [99] + [0] * 31  # Command to get current layer
                if len(data) < 32:
                    data.extend([0] * (32 - len(data)))
                self.device.write(bytes(data))  # Ensure data is in byte format
                logging.info("Requested current layer from device")
                return
            except Exception as e:
                logging.error(f"Failed to request current layer (attempt {attempt+1}/{max_retries}): {e}")
                time.sleep(0.2)  # Additional delay before retrying
        logging.error("Failed to request current layer after multiple attempts")

    def process_hid_events(self):
        while not self.terminate_event.is_set():
            try:
                if self.device:
                    data = self.device.read(32, timeout_ms=1000)
                    if data:
                        logging.debug(f"Data received: {data}")
                        self.handle_hid_event(data)
                    else:
                        time.sleep(0.1)  # Short sleep to reduce CPU usage
            except IOError as e:
                logging.error(f"IOError: {e}")
                time.sleep(1)  # Sleep before retrying
            except Exception as e:
                logging.error(f"Unexpected error: {e}")
                self.play_sound(self.SOUNDS["error"], self.ENABLED_SOUNDS["error"])
                time.sleep(1)  # Sleep before retrying

    def run(self):
        logging.info("Accessibility watcher started")
        self.play_sound(self.SOUNDS["program_start"], self.ENABLED_SOUNDS["program_start"])

        # Start HID event processing in a separate thread
        Thread(target=self.process_hid_events, daemon=True).start()

        while not self.terminate_event.is_set():
            if not self.device:
                if not self.connect_device():
                    time.sleep(10)  # Longer sleep when not connected to reduce CPU usage
                    continue
            time.sleep(1)  # Sleep to reduce CPU usage
            if self.terminate_event.is_set():
                break

        self.disconnect_device()
        self.play_sound(self.SOUNDS["program_exit"], self.ENABLED_SOUNDS["program_exit"])
        logging.info("Accessibility watcher exited")

    def sigterm_handler(self, signum, frame):
        logging.info("SIGTERM received, shutting down")
        self.terminate_event.set()

    def start(self):
        signal.signal(signal.SIGTERM, self.sigterm_handler)
        signal.signal(signal.SIGINT, self.sigterm_handler)  # Handle Control+C (SIGINT)

        print("Starting accessibility_watcher...")
        try:
            self.run()
        except KeyboardInterrupt:
            self.sigterm_handler(None, None)
            self.disconnect_device()
            sys.exit(0)

def create_default_config(config_file):
    with open(config_file, 'w') as f:
        f.write(DEFAULT_CONFIG)
    print(f"Default configuration file created at {config_file}.")
    print("Please edit the configuration file and run accessibility_watcher again.")
    sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Accessibility Watcher")
    parser.add_argument('-c', '--config', default='accessibility_watcher.conf', help="Configuration file")
    args = parser.parse_args()

    if not os.path.exists(args.config):
        create_default_config(args.config)

    watcher = AccessibilityWatcher(args.config)
    watcher.start()
