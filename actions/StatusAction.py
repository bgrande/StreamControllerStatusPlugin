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
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

class StatusAction(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_configuration = True
        
        # Initialize default settings if not present
        defaults = {
            "type": "web", # web, local
            "target": "https://google.com",
            "interval": 60,
            "interval_enabled": True,
            "match_value": "200",
            "match_mode": "Status Code",
            "match_bg_color": [0, 255, 0, 255],
            "match_text_color": [255, 255, 255, 255],
            "match_label": "Online",
            "match_image": "",
            "nomatch_bg_color": [255, 0, 0, 255],
            "nomatch_text_color": [255, 255, 255, 255],
            "nomatch_label": "Offline",
            "nomatch_image": "",
            "username": "",
            "password": "",
            "return_type": "background_color", # background_color, text, text_color, background_image
            "return_handler": ""
        }

        settings = self.get_settings()

        for key, value in defaults.items():
            if key not in settings:
                settings[key] = value

        self.set_settings(settings)

        self.last_check_time = 0
        self.is_checking = False

    def on_ready(self):
        self.perform_check_async()

    def on_tick(self):
        if not self.settings.get("interval_enabled", False):
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

        settings = self.get_settings()
        command_type = settings.get("type", "web")
        target = settings.get("target", "")
        username = settings.get("username", "")
        password = settings.get("password", "")
        
        result = ""
        success = False
        status_code = -1
        
        try:
            if command_type == "web":
                try:
                    base64string = base64.b64encode(bytes('%s:%s' % (username, password), 'utf-8'))
                    request = urllib.request.Request(target, headers={'User-Agent': 'Mozilla/5.0', 'Authorization': "Basic %s" % base64string})
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
            
        self.update_ui(is_match, result)

    def update_ui(self, is_match: bool, result: str):
        prefix = "match_" if is_match else "nomatch_"

        settings = self.get_settings()

        bg_color = settings.get(f"{prefix}bg_color", [0, 0, 0, 255])
        text_color = settings.get(f"{prefix}text_color", [255, 255, 255, 255])
        label = settings.get(f"{prefix}label", "")
        image_path = settings.get(f"{prefix}image", "")
        return_type = settings.get("return_type", "")

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

    def get_config_rows(self):
        entry_row = Adw.EntryRow(title=self.plugin_base.lm.get("open-browser.url.title"))
        new_window_toggle = Adw.SwitchRow(title=self.plugin_base.lm.get("open-browser.new-window"))

        # Load from config
        settings = self.get_settings()
        url = settings.setdefault("url", None)
        if url is None:
            url = ""
        entry_row.set_text(url)
        new_window_toggle.set_active(settings.setdefault("new_window", False))
        self.set_settings(settings)

        # Connect entry
        entry_row.connect("notify::text", self.on_change_url)
        # Connect switch
        new_window_toggle.connect("notify::active", self.on_change_new_window)

        return [entry_row]
