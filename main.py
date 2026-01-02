# Import StreamController modules
from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.PluginManager.ActionHolder import ActionHolder

# Import actions
from .actions import StatusAction

class StatusPlugin(PluginBase):
    def __init__(self):
        super().__init__()

        ## Register actions
        self.status_checker_holder = ActionHolder(
            plugin_base = self,
            action_base = StatusAction,
            action_id_suffix = "StatusChecker",
            action_id = "com.bgrande.StatusPlugin::StatusChecker",
            action_name = "Status Checker",
            # icon=Gtk.Picture.new_for_filename(os.path.join(self.PATH, "assets", "icon.png")),
            action_support={
                Input.Key: ActionInputSupport.SUPPORTED,
                Input.Dial: ActionInputSupport.SUPPORTED,
                Input.Touchscreen: ActionInputSupport.UNTESTED
            }
        )
        self.add_action_holder(self.status_checker_holder)

        # Register plugin
        self.register(
            plugin_name = self.lm.get("plugin.name"),
            github_repo = self.lm.get("plugin.github"),
            plugin_version = self.lm.get("plugin.version"),
            app_version = self.lm.get("app-version")
        )
