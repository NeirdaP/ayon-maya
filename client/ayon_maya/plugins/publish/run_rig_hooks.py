import os
import ayon_api
import pathlib
import runpy
import pyblish.api

from ayon_maya.api import plugin
from ayon_maya import version
from maya import cmds


class RunRigHooks(plugin.MayaInstancePlugin):
    """
    Plugin to run arbitrary project-defined python scripts that modify/process the rig product
    """
    order = pyblish.api.ExtractorOrder + 0.49
    label = "Run Rig Hooks"
    families = ["rig"]

    def process(self, instance):        
        self.log.info("Retrieving rig hooks directory from project settings")
        publish_hook_profiles = ayon_api.get_addon_project_settings(
                                        "maya", 
                                        version.__version__, 
                                        instance.context.data["projectName"]).get("publish_hooks").get("profiles")
        self.log.debug(publish_hook_profiles)

        rig_hooks_dir = None 
        curr_task_type = instance.data.get("taskEntity").get("taskType")
        for profile in publish_hook_profiles:
            if curr_task_type in profile.get("task_types"):
                rig_hooks_dir = profile.get("path")

        python_hooks = pathlib.Path(rig_hooks_dir).rglob("*.py") if rig_hooks_dir else None

        if not rig_hooks_dir or not python_hooks:
            self.log.warning("Rig hooks directory is not defined or is empty. Skipping plugin execution...")
            return

        # Save the current scene before opening staged product so as not to lose work
        original_workfile_path = cmds.file(query=True, sceneName=True)
        cmds.file(save=True) 

        # Run hooks on first .ma representation found for this instance
        representations = instance.data.get("representations")
        for representation in representations:

            if representation.get("name") == "ma":
                ma_repre_path = os.path.join(representation.get("stagingDir"), representation.get("files"))

                cmds.file(ma_repre_path, open=True)
                for hook_path in python_hooks:
                    try:
                        runpy.run_path(hook_path)
                        cmds.file(save=True)
                    except Exception as e:
                        self.log.warning("Hit error when trying to run hook {}: {}".format(hook_path, e))
                break
        
        # Re-opening workfile to ensure consistent versioning
        cmds.file(original_workfile_path, open=True, force=True)