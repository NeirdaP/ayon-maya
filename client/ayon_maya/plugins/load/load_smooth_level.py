# -*- coding: utf-8 -*-
"""Smooth level loader."""

import ayon_maya.api.plugin
import json


class SmoothLevelLoader(ayon_maya.api.plugin.Loader):
    """Specific loader for smooth level"""

    product_types = {"look"}
    representations = {"json"}

    label = "Import smooth level"
    order = -10
    icon = "code-fork"
    color = "orange"

    def load(
            self,
            context,
            name,
            namespace,
            data
    ):
        import maya.cmds as cmds
        """
        Load Smooth level settings.
        """

        path = self.filepath_from_context(context)

        with open(path) as json_path:
            data = json.load(json_path)
        mesh_list = data.get("attributes")
        for mesh_data in mesh_list:
            attributes = mesh_data.get("attributes")
            mesh_name = mesh_data.get("name")
            smooth_level = attributes.get("smoothLevel")

            try:
                cmds.setAttr(f"{mesh_name}.smoothLevel", smooth_level)
            except Exception as e:
                print(f"Error : {e}")
                pass
        self.log.info(f">>> loading json [ {path} ]")
