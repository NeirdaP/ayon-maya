# -*- coding: utf-8 -*-
"""Arnold mesh attributes loader."""
import ayon_maya
import json
from collections import defaultdict


class ArnoldMeshAttributesLoader(ayon_maya.api.plugin.Loader):
    """
    Specific loader for arnold mesh attributes
    """

    product_types = {"look"}
    representations = {"json"}

    label = "Import and assign arnold mesh attributes"
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

        attributes = [
            # Arnold
            "aiTranslator",
            "aiOpaque",
            "aiMatte",
            # Visibility
            "primaryVisibility",
            "aiCastShadows",
            "aiVisibleInDiffuseReflection",
            "aiVisibleInSpecularReflection",
            "aiVisibleInDiffuseTransmission",
            "aiVisibleInSpecularTransmission",
            "aiVisibleInVolume",
            "aiSelfShadows",
            # Subdivision
            "aiSubdivType",
            "aiSubdivIterations",
            "aiSubdivAdaptiveMetric",
            "aiSubdivPixelError",
            "aiSubdivAdaptiveSpace",
            "aiSubdivUvSmoothing",
            "aiSubdivSmoothDerivs",
            "aiSubdivFrustumIgnore",
            # Displacement Attributes
            "aiDispHeight",
            "aiDispPadding",
            "aiDispZeroValue",
        ]

        # Get all node uuids from scene
        scene_uuids = defaultdict(list)

        for node in cmds.ls():
            node_uuid = ayon_maya.api.lib.get_id(node)
            if node_uuid:
                scene_uuids[node_uuid].append(node)

        path = self.filepath_from_context(context)

        with open(path) as json_file:
            data = json.load(json_file)

        mesh_list = data.get("attributes")

        for mesh_data in mesh_list:
            mesh_attributes = mesh_data.get("attributes")
            mesh_uuid = mesh_data.get("uuid")
            for attr_name in attributes:

                attribute_value = mesh_attributes.get(attr_name)

                matching_nodes = scene_uuids.get(mesh_uuid)
                if not matching_nodes:
                    self.log.warning(f"Node with uuid '{mesh_uuid}' was not found in scene")
                    continue

                for mesh_name in matching_nodes:
                    attribute = f"{mesh_name}.{attr_name}"
                    try:
                        if isinstance(attribute_value, str):
                            cmds.setAttr(attribute, attribute_value, type="string")
                        else:
                            cmds.setAttr(attribute, attribute_value)
                    except Exception as e:
                        self.log.info(f"Failed setting attribute '{attribute}' with value '{attribute_value}': {e}")

        self.log.info(f">>> Loaded json [ {path} ] to set arnold mesh attributes")
