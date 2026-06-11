# -*- coding: utf-8 -*-
"""Redshift mesh attributes loader."""
import ayon_maya
import json
from collections import defaultdict


class RedshiftMeshAttributesLoader(ayon_maya.api.plugin.Loader):
    """
    Specific loader for redshift mesh attributes
    """

    product_types = {"look"}
    representations = {"json"}

    label = "Import and assign redshift mesh attributes"
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
            # Visibility - General
            "rsEnableVisibilityOverrides",
            "rsPrimaryRayVisible",
            "rsSecondaryRayVisible",
            "rsShadowCaster",
            "rsShadowReceiver",
            "rsSelfShadows",
            "rsAOCaster",
            # Visibility - Reflection & Refraction
            "rsReflectionVisible",
            "rsRefractionVisible",
            "rsReflectionCaster",
            "rsRefractionCaster",
            # Visibility - Global Illumination
            "rsGiVisible",
            "rsCausticVisible",
            "rsGiReceiver",
            "rsForceBruteForceGI",
            "rsGiCaster",
            "rsReflectionCausticCaster",
            "rsRefractionCausticCaster",
            "rsCausticReceiver",
            # Matte
            "rsMatteEnable",
            "rsMatteShowBackground",
            "rsMatteApplyToSecondaryRays",
            "rsMatteAffectedByMatteLights",
            "rsMatteIncludeInPuzzleMatte",
            "rsMatteAlpha",
            "rsMatteReflectionScale",
            "rsMatteRefractionScale",
            "rsMatteDiffuseScale",
            # Shadow
            "rsMatteShadowEnable",
            "rsMatteReceiveShadowsFromMattes",
            "rsMatteShadowAffectsAlpha",
            "rsMatteShadowColor",
            "rsMatteShadowTransparency",
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

        self.log.info(f">>> Loaded json [ {path} ] to set redshift mesh attributes")
