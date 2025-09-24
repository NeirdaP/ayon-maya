# -*- coding: utf-8 -*-
"""Maya subdivision level collector."""
import pyblish.api
from ayon_maya.plugins.publish import collect_subdivision

class CollectSubdivisionDisplace(collect_subdivision.CollectSubdivision):
    """Collect subdivision displacement data on meshes of the instance.
    Behaves exactly the same as collect_subdivision except with different attributes.
    """
    order = pyblish.api.CollectorOrder + 0.3
    families = ["look", "lookanim"]
    label = "Collect Subdivision Displace"

    # Arnold and Redshift subdiv displacement settings
    subdiv_attributes = ["rsEnableDisplacement", 
                         "rsMaxDisplacement",
                         "rsDisplacementScale",
                         "rsAutoBumpMap", 
                         "aiDispHeight", 
                         "aiDispPadding", 
                         "aiDispZeroValue"
                        ]