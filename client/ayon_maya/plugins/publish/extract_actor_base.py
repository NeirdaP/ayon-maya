# -*- coding: utf-8 -*-
"""Extract actorbase as Maya Scene."""
import os

from ayon_maya.api.lib import maintained_selection
from ayon_maya.api import plugin
from maya import cmds


class ExtractActorBase(plugin.MayaExtractorPlugin):
    """Extract actorBase (light rig) as Maya Scene."""

    label = "Extract ActorBase (Maya Scene)"
    families = ["actorbase"]
    scene_type = "ma"


    def remove_from_scene(self, node):
        if not cmds.ls(node):
            return

        def unlock_and_delete(to_delete):
            try:
                cmds.lockNode(to_delete, lock=False)
                cmds.delete(to_delete)
            except Exception as e:
                print("Failed to delete {}: {}".format(to_delete, e))

        if cmds.nodeType(node) == "objectSet":
            children = cmds.sets(node, query=True)
        else:
            children = cmds.listRelatives(node, children=True)

        if not children:
            unlock_and_delete(node)       
        else:
            for child in children:
                self.remove_from_scene(child)
                unlock_and_delete(node)


    def process(self, instance):
        """Plugin entry point."""
        maya_settings = instance.context.data["project_settings"]["maya"]
        ext_mapping = {
            item["name"]: item["value"]
            for item in maya_settings["ext_mapping"]
        }
        if ext_mapping:
            self.log.debug("Looking in settings for scene type ...")
            # use extension mapping for first family found
            for family in self.families:
                try:
                    self.scene_type = ext_mapping[family]
                    self.log.debug(
                        "Using '.{}' as scene type".format(self.scene_type))
                    break
                except AttributeError:
                    # no preset found
                    pass
        # Define extract output file path
        dir_path = self.staging_dir(instance)
        filename = "{0}.{1}".format(instance.name, self.scene_type)
        path = os.path.join(dir_path, filename)

        # Perform extraction
        self.log.debug("Performing extraction ...")
        with maintained_selection():
            #cmds.select(instance, noExpand=True)
            cmds.select(clear=True)
            for name in instance.data.get("rig_sets"):
                cmds.select(name, add=True, noExpand=True)

            cmds.file(path,
                      force=True,
                      typ="mayaAscii" if self.scene_type == "ma" else "mayaBinary",  # noqa: E501
                      exportSelected=True,
                      preserveReferences=False,
                      channels=True,
                      constraints=True,
                      expressions=True,
                      constructionHistory=True)

        if "representations" not in instance.data:
            instance.data["representations"] = []

        representation = {
            'name': self.scene_type,
            'ext': self.scene_type,
            'files': filename,
            "stagingDir": dir_path
        }
        instance.data["representations"].append(representation)

        # Move stuff back into place and clean up the scene
        for moved_root in instance.data["moved_roots"]:
            cmds.parent(moved_root, world=True)

        for item in instance.data.get("rig_sets"):
            self.remove_from_scene(item)

        self.log.debug("Extracted instance '%s' to: %s", instance.name, path)
