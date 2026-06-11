# -*- coding: utf-8 -*-
"""Smooth mesh attributes loader."""
import ayon_maya
import json
from collections import defaultdict


class SmoothMeshAttributesLoader(ayon_maya.api.plugin.Loader):
    """
    Specific loader for smooth mesh attributes
    """

    product_types = {"look"}
    representations = {"json"}

    label = "Import and assign smooth mesh attributes"
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
            "displaySmoothMesh",
            "smoothLevel",
            "displaySubdComps",
            "useSmoothPreviewForRender",
            "renderSmoothLevel",
            "useGlobalSmoothDrawType",
            "smoothDrawType",
            "displayDisplacement",
            "osdVertBoundary",
            "osdFvarBoundary",
            "osdFvarPropagateCorners",
            "osdSmoothTriangles",
            "osdCreaseMethod",
            "enableOpenCL",
            "smoothTessLevel",
            "boundaryRule",
            "continuity",
            "smoothUVs",
            "propagateEdgeHardness",
            "keepMapBorders",
            "keepBorder",
            "keepHardEdge",
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

                matching_nodes = scene_uuids.get(mesh_uuid)
                if not matching_nodes:
                    self.log.warning(f"Node with uuid '{mesh_uuid}' was not found in scene")
                    continue

                for mesh_name in matching_nodes:

                    attribute = f"{mesh_name}.{smooth_attribute}"
                    try:
                        if isinstance(attribute_value, str):
                            cmds.setAttr(attribute, attribute_value, type="string")
                        else:
                            cmds.setAttr(attribute, attribute_value)
                    except Exception as e:
                        self.log.info(f"Failed setting attribute '{attribute}' with value '{attribute_value}': {e}")

        self.log.info(f">>> Loaded json [ {path} ] to set smooth levels")
