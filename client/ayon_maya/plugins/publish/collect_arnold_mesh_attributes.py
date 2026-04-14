# -*- coding: utf-8 -*-
"""Maya arnold mesh attributes collector."""
import pyblish.api
from ayon_maya.plugins.publish import collect_smooth_mesh_attributes


class CollectArnoldMeshAttributes(collect_smooth_mesh_attributes.CollectSmoothMeshAttributes):
    """Collect subdivision displacement data on meshes of the instance.
    Behaves exactly the same as collect_subdivision except with different attributes.
    """
    order = pyblish.api.CollectorOrder + 0.3
    families = ["look", "lookanim"]
    label = "Collect Arnold Mesh Attributes"

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