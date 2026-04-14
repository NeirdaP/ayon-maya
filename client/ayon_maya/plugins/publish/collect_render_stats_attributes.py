# -*- coding: utf-8 -*-
"""Maya render stats attributes collector."""
import pyblish.api
from ayon_maya.plugins.publish import collect_smooth_mesh_attributes


class CollectRenderStatsAttributes(collect_smooth_mesh_attributes.CollectSmoothMeshAttributes):
    """Collect render stats data on meshes of the instance.
    Behaves exactly the same as collect_smooth_mesh_attributes except with different attributes.
    """
    order = pyblish.api.CollectorOrder + 0.3
    families = ["look", "lookanim"]
    label = "Collect Render Stats Attributes"

    attributes = [
        "castsShadows",
        "receiveShadows",
        "holdOut",
        "motionBlur",
        "primaryVisibility",
        "smoothShading",
        "visibleInReflections",
        "visibleInRefractions",
        "doubleSided",
        "opposite",
        "geometryAntialiasingOverride",
        "antialiasingLevel",
        "shadingSamplesOverride",
        "shadingSamples",
        "maxShadingSamples",
    ]
