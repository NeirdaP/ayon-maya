import pyblish.api
from ayon_maya.api import plugin
from maya import cmds


class CollectActorBase(plugin.MayaInstancePlugin):
    """
    Run actorize on set contents and imprint any pipeline needed metadata on the instance
    Will need more information about what's used in validation and extraction in order to do this properly

    """
    order = pyblish.api.CollectorOrder + 0.05
    label = "Collect Actor Base"
    families = ["actorbase"]


    def process(self, instance):

        from pymonk.src.api.run import actorize_geometry_transforms
        from ayon_core.pipeline.context_tools import get_current_folder_entity, \
                                                     get_current_project_name

        project = get_current_project_name()
        asset = get_current_folder_entity().get("name")

        # Collect the geometry transforms in the instance selection set
        geometry_transforms_list = []
        shapes = cmds.ls(instance, type="shape")

        # Keep track of parenting relationships since stuff is moved in the actorize step
        geometry_transform_to_group_root = {}

        for shape in shapes:
            parent_transform = cmds.listRelatives(shape, parent=True, type="transform")
            group_root_transform = cmds.listRelatives(parent_transform, parent=True, type="transform")
            geometry_transforms_list.append(parent_transform[0])
            geometry_transform_to_group_root[parent_transform[0]] = group_root_transform

        moved_roots = []
        try:
            actorize_geometry_transforms(geometry_transforms_list, asset, project)

            # Move the group root back into place (this is kind of a workaround for pymonk changing the hierarchy)
            for transform in geometry_transform_to_group_root:
                new_parent = cmds.listRelatives(transform, parent=True, type="transform")
                cmds.parent(geometry_transform_to_group_root[transform], new_parent)
                
                cmds.parent(transform, geometry_transform_to_group_root[transform])
                moved_roots.append(geometry_transform_to_group_root[transform])

        except Exception as e:
            print("Error running actorize in the scene: {}".format(e))

        # Store information about the sets we made and the group(s) we moved
        instance.data["rig_sets"] = ["all_anim_set", "all_skin_set", "rig_root_grp"]
        instance.data["moved_roots"] = moved_roots
        