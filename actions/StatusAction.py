import os
import subprocess
import threading
import time
import urllib.request
import urllib.error
import base64

from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.PluginManager.PluginBase import PluginBase

# Import gtk modules
import gi

MATCH_VALUE_DEFAULT = "200"

MATCH_MODE_REGEX = "Regex"

MATCH_MODE_SUCCESS = "Success"

MATCH_MODE_EQUALS = "Equals"

MATCH_MODE_CONTAINS = "Contains"

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio, Gdk

NOMATCH_BG_COLOR = "nomatch_bg_color"
MATCH_BG_COLOR = "match_bg_color"
INTERVAL = "interval"
HEADERS = "headers"
TARGET = "target"
MATCH_VALUE = "match_value"
MATCH_MODE = "match_mode"
MATCH_MODE_STATUS_CODE = "Status Code"
TYPE = "type"
TYPE_WEB = "web"
TYPE_LOCAL = "local"

class StatusAction(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.has_configuration = True
        
        self.last_check_time = 0
        self.is_checking = False

    def on_ready(self):
        # Initialize default settings if not present
        defaults = {
            TYPE: TYPE_WEB,  # web, local
            TARGET: "https://google.com",
            INTERVAL: 0,
            MATCH_VALUE: MATCH_VALUE_DEFAULT,
            MATCH_MODE: MATCH_MODE_STATUS_CODE,
            MATCH_BG_COLOR: [0, 255, 0, 255],
            "match_text_color": [255, 255, 255, 255],
            "match_label": "Online",
            "match_image": "",
            NOMATCH_BG_COLOR: [255, 0, 0, 255],
            "nomatch_text_color": [255, 255, 255, 255],
            "nomatch_label": "Offline",
            "nomatch_image": "",
            "return_type": "background_color",  # background_color, text, text_color, background_image
            "return_handler": "",
            HEADERS: "{}",
        }

        self.settings = self.get_settings()

        for key, value in defaults.items():
            if key not in self.settings:
                self.settings[key] = value;

        self.set_settings(self.settings)

        #self.perform_check_async()

    def on_tick(self):
        interval = self.get_settings().get("interval", 0)

        if interval <= 0:
            return
            
        current_time = time.time()
        if current_time - self.last_check_time >= interval:
            self.perform_check_async()

    def on_key_down(self):
        self.perform_check_async()

    def perform_check_async(self):
        if self.is_checking:
            return
        
        thread = threading.Thread(target=self.perform_check, daemon=True)
        thread.start()

    def perform_check(self):
        self.is_checking = True
        self.last_check_time = time.time()

        settings = self.get_settings()
        command_type = settings.get(TYPE, TYPE_WEB)
        target = settings.get(TARGET, "")
        headers = settings.get(HEADERS, "{}")

        result = ""
        success = False
        status_code = -1
        
        try:
            if command_type == TYPE_WEB:
                try:
                    request = urllib.request.Request(target, headers=headers)
                    with urllib.request.urlopen(request, timeout=10) as response:
                        status_code = response.getcode()
                        result = response.read().decode('utf-8')
                        success = True
                except urllib.error.HTTPError as e:
                    status_code = e.code
                    result = str(e)
                except Exception as e:
                    result = str(e)
            else: # Local Script
                try:
                    process = subprocess.run(target, shell=True, capture_output=True, text=True, timeout=10)
                    result = process.stdout.strip()
                    status_code = process.returncode
                    success = True
                except Exception as e:
                    result = str(e)
        finally:
            self.evaluate_result(result, status_code, success)
            self.is_checking = False

    def evaluate_result(self, result: str, status_code: int, success: bool):
        match_mode = self.settings.get(MATCH_MODE, MATCH_MODE_STATUS_CODE)
        match_value = self.settings.get(MATCH_VALUE, "")
        
        is_match = False

        if match_mode == MATCH_MODE_STATUS_CODE:
            is_match = str(status_code) == match_value
        elif match_mode == MATCH_MODE_CONTAINS:
            is_match = match_value in result
        elif match_mode == MATCH_MODE_EQUALS:
            is_match = result == match_value
        elif match_mode == MATCH_MODE_SUCCESS:
            is_match = success
        elif match_mode == MATCH_MODE_REGEX:
            import re
            try:
                is_match = bool(re.search(match_value, result))
            except:
                is_match = False
            
        self.update_ui(is_match, result)

    def update_ui(self, is_match: bool, result: str):
        prefix = "match_" if is_match else "nomatch_"

        settings = self.get_settings()

        bg_color = settings.get(f"{prefix}bg_color", [0, 0, 0, 255])
        text_color = settings.get(f"{prefix}text_color", [255, 255, 255, 255])
        label = settings.get(f"{prefix}label", "")
        image_path = settings.get(f"{prefix}image", "")
        return_type = settings.get("return_type", "")

        # todo rework this
        if return_type == "string":
            self.set_center_label(text=f"{result}%", font_size=24, color=text_color)
        elif return_type == "background_color":
            self.set_background_color(bg_color)
        elif return_type == "background_image":
            # todo: set background image: set_media(self, image = None, media_path=None, size: float = None, valign: float = None, halign: float = None, fps: int = 30, loop: bool = True, update: bool = True):
            if image_path and os.path.exists(image_path):
                # this needs to copy the image somewhere, first, probably better use image=image_file (from request)
                self.set_media(media_path=image_path)
            else:
                self.set_media(None)

    def load_config_defaults(self):
        settings = self.get_settings()

        # Set dropdown index: 0 for web, 1 for local
        selected_type = settings.get(TYPE, TYPE_WEB)
        self.type_dropdown.set_selected(0 if selected_type == TYPE_WEB else 1)

        # target
        self.target_entry.set_text(settings.get(TARGET, ""))  # Does not accept None

        # headers
        self.headers_entry.set_text(settings.get(HEADERS, "{}"))

        # interval
        self.auto_fetch.set_value(settings.get(INTERVAL, 0))

        # Set match mode index
        current_mode = settings.get(MATCH_MODE, MATCH_MODE_STATUS_CODE)
        if current_mode in self.match_modes:
            index = self.match_modes.index(current_mode)
            self.match_mode_dropdown.set_selected(index)

        # match value
        self.match_value_entry.set_text(settings.get(MATCH_VALUE, MATCH_VALUE_DEFAULT))  # Does not accept None

        # match/success background color
        color_list = settings.get(MATCH_BG_COLOR, [0, 255, 0, 255])
        rgba = Gdk.RGBA()
        rgba.red = color_list[0] / 255.0
        rgba.green = color_list[1] / 255.0
        rgba.blue = color_list[2] / 255.0
        rgba.alpha = color_list[3] / 255.0
        self.match_bg_button.set_rgba(rgba)

        # no match/error background color
        color_list = settings.get(NOMATCH_BG_COLOR, [0, 255, 0, 255])
        rgba = Gdk.RGBA()
        rgba.red = color_list[0] / 255.0
        rgba.green = color_list[1] / 255.0
        rgba.blue = color_list[2] / 255.0
        rgba.alpha = color_list[3] / 255.0
        self.nomatch_bg_button.set_rgba(rgba)

    def get_custom_config_area(self):
        return Gtk.Label(label="Add your custom status calls here")

    def get_config_rows(self) -> list:
        # dropdown for type selection (web/local)
        self.type_list = Gtk.StringList.new([TYPE_WEB, TYPE_LOCAL])
        self.type_dropdown = Adw.ComboRow(
            title="Target Type",
            model=self.type_list
        )

        # set target url/path
        self.target_entry = Adw.EntryRow(title="URL (i.e. https://google.com) or application path (i.e. /usr/bin/myscript)")

        # set headers for request
        self.headers_entry = Adw.EntryRow(title="Header (json)")

        # set auto fetch interval
        self.auto_fetch = Adw.SpinRow.new_with_range(step=1, min=0, max=3600)
        self.auto_fetch.set_title("Auto Interval (s)")
        self.auto_fetch.set_subtitle("0 to disable")

        # dropdown for result handling selection (web/local)
        self.match_mode = Gtk.StringList.new([
            MATCH_MODE_STATUS_CODE,
            MATCH_MODE_CONTAINS,
            MATCH_MODE_EQUALS,
            MATCH_MODE_SUCCESS,
            MATCH_MODE_REGEX
        ])
        self.match_mode_dropdown = Adw.ComboRow(
            title="Result Handling Type",
            model=self.type_list
        )

        # set match value
        self.match_value_entry = Adw.EntryRow(title="Expected value (depends on <i>Result Handling Type</i>)")

        # select background color for success
        self.match_bg_row = Adw.ActionRow(title="Success Background Color")
        color_dialog = Gtk.ColorDialog(with_alpha=True)
        self.match_bg_button = Gtk.ColorDialogButton(dialog=color_dialog)
        self.match_bg_button.set_valign(Gtk.Align.CENTER)
        self.match_bg_row.add_suffix(self.match_bg_button)

        # select background color for failure
        self.nomatch_bg_row = Adw.ActionRow(title="Error Background Color")
        color_dialog = Gtk.ColorDialog(with_alpha=True)
        self.nomatch_bg_button = Gtk.ColorDialogButton(dialog=color_dialog)
        self.nomatch_bg_button.set_valign(Gtk.Align.CENTER)
        self.nomatch_bg_row.add_suffix(self.nomatch_bg_button)

        # now loading default config
        self.load_config_defaults()

        # Connect signals
        self.type_dropdown.connect("notify::selected", self.on_type_changed)
        self.target_entry.connect("notify::text", self.on_target_changed)
        self.headers_entry.connect("notify::text", self.on_headers_changed)
        self.auto_fetch.connect("notify::value", self.on_interval_changed)
        self.match_bg_button.connect("notify::rgba", self.on_match_bg_changed)
        self.nomatch_bg_button.connect("notify::rgba", self.on_nomatch_bg_changed)
        self.match_mode_dropdown.connect("notify::selected", self.on_match_mode_changed)
        self.match_value_entry.connect("notify::text", self.on_match_value_changed)

        return [
            self.type_dropdown,
            self.target_entry,
            self.headers_entry,
            self.auto_fetch,
            self.match_mode_dropdown,
            self.match_value_entry,
            self.match_bg_row,
            self.nomatch_bg_row
        ]

    def on_match_mode_changed(self, widget, *args):
        settings = self.get_settings()
        selected_index = widget.get_selected()
        if 0 <= selected_index < len(self.match_modes):
            settings[MATCH_MODE] = self.match_modes[selected_index]
            self.set_settings(settings)

    def on_type_changed(self, widget, *args):
        settings = self.get_settings()
        # 0 is Web, 1 is Local based on the StringList order
        settings[TYPE] = TYPE_WEB if widget.get_selected() == 0 else TYPE_LOCAL
        self.set_settings(settings)

    def on_match_value_changed(self, entry, *args):
        self.on_text_changed(entry, MATCH_VALUE)

    def on_target_changed(self, entry, *args):
        self.on_text_changed(entry, TARGET)

    def on_headers_changed(self, entry, *args):
        self.on_text_changed(entry, HEADERS)

    def on_interval_changed(self, entry, *args):
        settings = self.get_settings()
        settings[INTERVAL] = entry.get_value()
        self.set_settings(settings)

    def on_match_bg_changed(self, entry, *args):
        self.color_changed(entry, MATCH_BG_COLOR)

    def on_nomatch_bg_changed(self, entry, *args):
        self.color_changed(entry, NOMATCH_BG_COLOR)

    def color_changed(self, entry, key):
        rgba = entry.get_rgba()
        settings = self.get_settings()
        # Store as [R, G, B, A] in 0-255 range to match your defaults
        settings[key] = [
            int(rgba.red * 255),
            int(rgba.green * 255),
            int(rgba.blue * 255),
            int(rgba.alpha * 255)
        ]
        self.set_settings(settings)

    def on_text_changed(self, entry, key):
        settings = self.get_settings()
        settings[key] = entry.get_text()
        self.set_settings(settings)
