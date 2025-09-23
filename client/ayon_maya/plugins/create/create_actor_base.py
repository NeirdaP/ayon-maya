from ayon_maya.api import plugin


class CreateActorBase(plugin.MayaCreator):
    """Simple light base rig"""

    identifier = "io.openpype.creators.maya.actorbase"
    label = "Actor Base"
    product_type = "actorbase"
    icon = "wheelchair"