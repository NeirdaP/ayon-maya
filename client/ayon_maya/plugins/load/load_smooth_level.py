# -*- coding: utf-8 -*-
"""Smooth level loader."""
import ayon_maya
import json
from collections import defaultdict


class SmoothLevelLoader(ayon_maya.api.plugin.Loader):
    """
    Specific loader for smooth level
    """

    product_types = {"look"}
    representations = {"json"}

    label = "Import and assign smooth level"
    order = -10
    icon = "signal"
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
        smooth_attributes = [
            "smoothLevel",
            "rsEnableDisplacement",
            "rsMaxDisplacement",
            "rsDisplacementScale",
            "aiDispHeight",
            "aiDispPadding",
            "aiDispZeroValue"
        ]
        # Get all node uuids from scene
        scene_uuids = defaultdict(list)  # uuid is synonym of ayon cbid here

        for node in cmds.ls():
            node_uuid = ayon_maya.api.lib.get_id(node)
            if node_uuid:
                scene_uuids[node_uuid].append(node)

        path = self.filepath_from_context(context)

        with open(path) as json_file:
            data = json.load(json_file)

        mesh_list = data.get("attributes")

        for mesh_data in mesh_list:
            attributes = mesh_data.get("attributes")
            mesh_uuid = mesh_data.get("uuid")
            for smooth_attribute in smooth_attributes:

                attribute_value = attributes.get(smooth_attribute)

                for mesh_name in scene_uuids.get(mesh_uuid):
                    if not mesh_name:
                        self.log.info(f"Warning: Node '{mesh_name}' with uuid '{mesh_uuid}' was not found in scene")
                        continue

                    cmds.setAttr(f"{mesh_name}.displaySmoothMesh", 2) # Tick the 'Smooth Mesh Preview' checkbox and set the 'Display' to 'Smooth Mesh'
                    attribute = f"{mesh_name}.{smooth_attribute}"
                    try:
                        cmds.setAttr(attribute, attribute_value)
                    except Exception as e:
                        self.log.info(f"Failed setting attribute '{attribute}' with value '{attribute_value}': {e}")

        self.log.info(f">>> Loaded json [ {path} ] to set smooth levels")
