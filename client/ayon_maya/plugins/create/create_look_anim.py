from ayon_maya.plugins.create import create_look


class CreateLookAnim(create_look.CreateLook):
    """Shader connections defining the anim look.
    Distinct from the final render look and specific to supamonks."""

    identifier = "io.openpype.creators.maya.look_anim"
    label = "Look Anim"
    product_type = "lookanim"
    icon = "paint-brush"