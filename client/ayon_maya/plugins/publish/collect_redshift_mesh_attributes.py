# -*- coding: utf-8 -*-
"""Maya redshift mesh attributes collector."""
import pyblish.api
from ayon_maya.plugins.publish import collect_smooth_mesh_attributes


class CollectRedshiftMeshAttributes(collect_smooth_mesh_attributes.CollectSmoothMeshAttributes):
    """Collect subdivision displacement data on meshes of the instance.
    Behaves exactly the same as collect_subdivision except with different attributes.
    """
    order = pyblish.api.CollectorOrder + 0.3
    families = ["look", "lookanim"]
    label = "Collect Redshift Mesh Attributes"

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