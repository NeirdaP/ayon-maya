# -*- coding: utf-8 -*-
"""Smooth level loader."""
import ayon_maya
from ayon_maya.api.plugin import Loader
import json


class SmoothLevelLoader(Loader):
    """
    Specific loader for smooth level
    """

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
        Load Smooth level settings based on uuid.
        """
        # Get all node uuids from scene
        scene_uuids = {}  # uuid is synonym of ayon cbid here

        for node in cmds.ls():
            node_uuid = ayon_maya.api.lib.get_id(node)
            if node_uuid:
                scene_uuids[node_uuid] = node

        path = self.filepath_from_context(context)

        with open(path) as json_path:
            data = json.load(json_path)

        mesh_list = data.get("attributes")

        for mesh_data in mesh_list:
            attributes = mesh_data.get("attributes")
            mesh_uuid = mesh_data.get("uuid")
            smooth_level = attributes.get("smoothLevel")

            mesh_name = scene_uuids.get(mesh_uuid)
            if not mesh_name:
                self.log.info(f"Warning: Node '{mesh_name}' with uuid '{mesh_uuid}' was not found in scene")
                continue
            try:
                cmds.setAttr(f"{mesh_name}.smoothLevel", smooth_level)
            except Exception as e:
                self.log.info(f"Error : {e}")
                pass
        self.log.info(f">>> loading json [ {path} ]")
