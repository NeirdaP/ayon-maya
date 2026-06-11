# -*- coding: utf-8 -*-
"""Maya smooth mesh attributes collector."""
import pyblish.api
from ayon_maya.api import plugin, lib
from maya import cmds  # noqa


class CollectSmoothMeshAttributes(plugin.MayaInstancePlugin):
    """Collect smooth mesh attributes of the instance.
    """
    order = pyblish.api.CollectorOrder + 0.3
    families = ["look", "lookanim"]
    label = "Collect Smooth Mesh Attributes"

    attributes = [
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

    def get_attributes_for_node(self, node):
        node_attributes = {}
        for attr in self.attributes:
            if not cmds.attributeQuery(attr, node=node, exists=True):
                self.log.debug(f"Attribute {attr} does not exist on {node}, skipping its collection")
                continue

            attribute = "{}.{}".format(node, attr)
            # We don't support mixed-type attributes yet.
            if cmds.attributeQuery(attr, node=node, multi=True):
                self.log.warning(
                    f"Attribute '{attribute}' is mixed-type and is "
                    "not supported yet."
                )
                continue

            # Maya returns None for string attributes that have never
            # been set. Skip those to avoid storing invalid values.
            value = cmds.getAttr(attribute)
            if value is None:
                continue

            node_attributes[attr] = value

        return node_attributes

    def process(self, instance):
        """For each node in instance, check if it has the above subdiv_attributes, 
        and if so, add it to the instance's lookData. 

        Note: This plugin assumes that the lookData dict already exists and therefore 
        should be running after the collect_look plugin. 
        """
        # Skip processing if lookData doesn't exist
        look_data = instance.data.get("lookData")
        if not look_data:
            self.log.warning("Instance look data does not exist, cannot add attributes (check plugin ordering)")
            return

        # Create nodes attributes list from scratch if it doesn't exist
        if not look_data.get("attributes"):
            attributes = []
            for node in instance:
                node_attributes = self.get_attributes_for_node(node)
                if node_attributes:
                    attributes.append({"name": node,
                                        "uuid": lib.get_id(node),
                                        "attributes": node_attributes})
            instance.data["lookData"]["attributes"] = attributes

        # Otherwise update existing attributes dictionaries with additional keys
        else:
            for entry in instance.data["lookData"]["attributes"]:
                node = entry.get("name")
                node_attributes = self.get_attributes_for_node(node)
                for key, value in node_attributes.items():
                    entry["attributes"][key] = value
    