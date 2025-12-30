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
            action_id = "com.junie.StatusPlugin::StatusChecker",
            action_name = "Status Checker",
        )
        self.add_action_holder(self.status_checker_holder)

        # Register plugin
        self.register(
            plugin_name = "Status Plugin",
            github_repo = "https://github.com/StreamController/StreamControllerStatusPlugin",
            plugin_version = "1.0.0",
            app_version = "1.1.1-alpha"
        )
