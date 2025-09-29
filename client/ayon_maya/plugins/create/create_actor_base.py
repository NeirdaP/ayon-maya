from ayon_maya.api import plugin


class CreateActorBase(plugin.MayaCreator):
    """Simple base rig specific to supamonks"""

    identifier = "io.openpype.creators.maya.actorbase"
    label = "Actor Base"
    product_type = "actorbase"
    icon = "wheelchair"