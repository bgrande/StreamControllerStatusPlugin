import os
import subprocess
import threading
import time
import urllib.request
import urllib.error
from typing import Optional

from src.backend.PluginManager.ActionCore import ActionCore
from src.backend.PluginManager.InputBases import KeyAction

from GtkHelper.GenerativeUI.EntryRow import EntryRow
from GtkHelper.GenerativeUI.SpinRow import SpinRow
from GtkHelper.GenerativeUI.ComboRow import ComboRow
from GtkHelper.GenerativeUI.ColorButtonRow import ColorButtonRow
from GtkHelper.GenerativeUI.FileDialogRow import FileDialogRow
from GtkHelper.GenerativeUI.ExpanderRow import ExpanderRow
from GtkHelper.GenerativeUI.SwitchRow import SwitchRow

class StatusAction(KeyAction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_configuration = True
        
        self.settings = self.get_settings()
        
        # Initialize default settings if not present
        defaults = {
            "check_type": "API/Website",
            "target": "https://google.com",
            "interval": 60,
            "periodic_enabled": True,
            "match_value": "200",
            "match_mode": "Status Code",
            "match_bg_color": [0, 255, 0, 255],
            "match_text_color": [255, 255, 255, 255],
            "match_label": "Online",
            "match_image": "",
            "nomatch_bg_color": [255, 0, 0, 255],
            "nomatch_text_color": [255, 255, 255, 255],
            "nomatch_label": "Offline",
            "nomatch_image": ""
        }
        
        for key, value in defaults.items():
            if key not in self.settings:
                self.settings[key] = value
        
        self.last_check_time = 0
        self.is_checking = False

    def on_ready(self):
        self.perform_check_async()

    def on_tick(self):
        if not self.settings.get("periodic_enabled", False):
            return
            
        interval = self.settings.get("interval", 60)
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
        
        check_type = self.settings.get("check_type", "API/Website")
        target = self.settings.get("target", "")
        
        result = ""
        success = False
        status_code = -1
        
        try:
            if check_type == "API/Website":
                try:
                    with urllib.request.urlopen(target, timeout=10) as response:
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
        match_mode = self.settings.get("match_mode", "Status Code")
        match_value = self.settings.get("match_value", "")
        
        is_match = False
        
        if match_mode == "Status Code":
            is_match = str(status_code) == match_value
        elif match_mode == "Contains":
            is_match = match_value in result
        elif match_mode == "Equals":
            is_match = result == match_value
        elif match_mode == "Success":
            is_match = success
        elif match_mode == "Regex":
            import re
            try:
                is_match = bool(re.search(match_value, result))
            except:
                is_match = False
            
        self.update_ui(is_match)

    def update_ui(self, is_match: bool):
        prefix = "match_" if is_match else "nomatch_"
        
        bg_color = self.settings.get(f"{prefix}bg_color", [0, 0, 0, 255])
        text_color = self.settings.get(f"{prefix}text_color", [255, 255, 255, 255])
        label = self.settings.get(f"{prefix}label", "")
        image_path = self.settings.get(f"{prefix}image", "")
        
        self.set_background_color(bg_color)
        self.set_center_label(label, color=text_color)
        
        if image_path and os.path.exists(image_path):
            self.set_media(media_path=image_path)
        else:
            self.set_media(None)

    def get_config_rows(self) -> list:
        # Check Config
        self.type_combo = ComboRow(self, "check_type", self.settings["check_type"], ["API/Website", "Local Script"], title="Check Type")
        self.target_entry = EntryRow(self, "target", self.settings["target"], title="Target (URL or Path)")
        self.periodic_switch = SwitchRow(self, "periodic_enabled", self.settings["periodic_enabled"], title="Periodic Check")
        self.interval_spin = SpinRow(self, "interval", self.settings["interval"], 1, 3600, title="Interval (seconds)")
        
        # Match Config
        self.match_mode_combo = ComboRow(self, "match_mode", self.settings["match_mode"], ["Status Code", "Contains", "Equals", "Success", "Regex"], title="Match Mode")
        self.match_value_entry = EntryRow(self, "match_value", self.settings["match_value"], title="Match Value")
        
        # Match Behavior
        self.match_expander = ExpanderRow(self, "match_expander", True, title="Match Behavior", start_expanded=False)
        self.match_bg_color = ColorButtonRow(self, "match_bg_color", self.settings["match_bg_color"], title="Background Color")
        self.match_text_color = ColorButtonRow(self, "match_text_color", self.settings["match_text_color"], title="Text Color")
        self.match_label_entry = EntryRow(self, "match_label", self.settings["match_label"], title="Label")
        self.match_image_file = FileDialogRow(self, "match_image", self.settings["match_image"], title="Image")
        
        self.match_expander.add_row(self.match_bg_color.widget)
        self.match_expander.add_row(self.match_text_color.widget)
        self.match_expander.add_row(self.match_label_entry.widget)
        self.match_expander.add_row(self.match_image_file.widget)
        
        # No Match Behavior
        self.nomatch_expander = ExpanderRow(self, "nomatch_expander", True, title="No Match Behavior", start_expanded=False)
        self.nomatch_bg_color = ColorButtonRow(self, "nomatch_bg_color", self.settings["nomatch_bg_color"], title="Background Color")
        self.nomatch_text_color = ColorButtonRow(self, "nomatch_text_color", self.settings["nomatch_text_color"], title="Text Color")
        self.nomatch_label_entry = EntryRow(self, "nomatch_label", self.settings["nomatch_label"], title="Label")
        self.nomatch_image_file = FileDialogRow(self, "nomatch_image", self.settings["nomatch_image"], title="Image")
        
        self.nomatch_expander.add_row(self.nomatch_bg_color.widget)
        self.nomatch_expander.add_row(self.nomatch_text_color.widget)
        self.nomatch_expander.add_row(self.nomatch_label_entry.widget)
        self.nomatch_expander.add_row(self.nomatch_image_file.widget)
        
        return [
            self.type_combo.widget,
            self.target_entry.widget,
            self.periodic_switch.widget,
            self.interval_spin.widget,
            self.match_mode_combo.widget,
            self.match_value_entry.widget,
            self.match_expander.widget,
            self.nomatch_expander.widget
        ]
