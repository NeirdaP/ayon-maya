# -*- coding: utf-8 -*-
"""Extract rig as Maya Scene."""
import os

from ayon_maya.api.lib import maintained_selection, set_id, \
                              generate_ids, get_id_required_nodes
from ayon_maya.api import plugin
from maya import cmds


class ExtractActorBase(plugin.MayaExtractorPlugin):
    """Extract actorBase (simple base rig) as Maya Scene."""

    label = "Extract ActorBase (Maya Scene)"
    families = ["actorbase"]
    scene_type = "ma"


    def remove_from_scene(self, node):
        if not cmds.ls(node):
            return

        def unlock_and_delete(to_delete):
            try:
                cmds.lockNode(to_delete, lock=False)
                cmds.delete(to_delete)
            except Exception as e:
                print("Failed to delete {}: {}".format(to_delete, e))

        if cmds.nodeType(node) == "objectSet":
            children = cmds.sets(node, query=True)
        else:
            children = cmds.listRelatives(node, children=True)

        if not children:
            unlock_and_delete(node)       
        else:
            for child in children:
                self.remove_from_scene(child)
                unlock_and_delete(node)


    def prepare_scene(self, instance):
        from pymonk.src.api.run import actorize_geometry_transforms
        from ayon_core.pipeline.context_tools import get_current_folder_entity, \
                                                     get_current_project_name

        project = get_current_project_name()
        asset = get_current_folder_entity().get("name")

        # Store data about moved sets to clean up scene later
        moved = {}
        for member in instance.data.get("setMembers"):
            if cmds.nodeType(member) != "transform":
                continue
            parent = cmds.listRelatives(member, parent=True)
            moved[cmds.ls(member)[0]] = parent[0] if parent else None
        
        pymonk_rig_sets = ["all_anim_set", "all_skin_set", "rig_root_grp"]
        rig_selection_sets = []

        try:
            # Actorize call will move the instance set members into msh grp temporarily
            actorize_geometry_transforms(list(moved.keys()), asset, project)

            # Place the created mesh group and anim group into appropriate selection sets
            for child_grp in cmds.listRelatives("rig_root_grp") or []:
                if child_grp == "msh_grp":
                    set_name = "{}_out_SET".format(instance.data["productName"])
                elif child_grp == "anim_grp":
                    set_name = "{}_controls_SET".format(instance.data["productName"])
                else:
                    continue
                cmds.sets([child_grp], name=set_name)
                rig_selection_sets.append(set_name)

            # Get all the newly created nodes and filter for the ones that should have cbids
            all_created_nodes = []
            for rig_set in pymonk_rig_sets:
                all_created_nodes.append(rig_set)
                all_created_nodes.extend(cmds.listRelatives(rig_set, allDescendents=True) or [])
            all_created_nodes.extend(rig_selection_sets)
            filtered_nodes = get_id_required_nodes(nodes=all_created_nodes)

            # Assign cbids to the new nodes
            for node, id in generate_ids(filtered_nodes):
                set_id(node, id, overwrite=False)

        except Exception as e:
            self.log.error("Error running actorize in the scene: {}".format(e))
            return

        # Store information about the sets we made and the group(s) we moved
        instance.data["rig_sets"] = pymonk_rig_sets + rig_selection_sets
        instance.data["moved"] = moved
        

    def get_staged_output_path(self, instance):
        """
            Determine the staged representation output path based on
            staging directory, instance name, and configured scene type
        """
        maya_settings = instance.context.data["project_settings"]["maya"]
        ext_mapping = {
            item["name"]: item["value"]
            for item in maya_settings["ext_mapping"]
        }
        if ext_mapping:
            self.log.debug("Looking in settings for scene type ...")
            # use extension mapping for first family found
            for family in self.families:
                try:
                    self.scene_type = ext_mapping[family]
                    self.log.debug(
                        "Using '.{}' as scene type".format(self.scene_type))
                    break
                except AttributeError:
                    # no preset found
                    self.log.warning(f"No scene extension presets found for family: {family}")
                    pass

        # Define extract output file path
        dir_path = self.staging_dir(instance)
        filename = "{0}.{1}".format(instance.name, self.scene_type)

        return os.path.join(dir_path, filename)


    def process(self, instance):
        """Plugin entry point."""

        # Prepare the scene by running pymonk actorize, which will 
        # reorganize things into groups and create controls
        self.prepare_scene(instance)

        if not instance.data.get("rig_sets"):
            self.log.warning("Actorize did not complete successfully, skipping actorbase extraction")
            return

        # Get the output path in the staging directory
        path = self.get_staged_output_path(instance)

        # Perform extraction
        self.log.debug("Performing extraction ...")
        with maintained_selection():
            cmds.select(clear=True)
            for name in instance.data.get("rig_sets"):
                cmds.select(name, add=True, noExpand=True)

            cmds.file(path,
                      force=True,
                      typ="mayaAscii" if self.scene_type == "ma" else "mayaBinary",  # noqa: E501
                      exportSelected=True,
                      preserveReferences=False,
                      channels=True,
                      constraints=True,
                      expressions=True,
                      constructionHistory=True)

        if "representations" not in instance.data:
            instance.data["representations"] = []

        representation = {
            'name': self.scene_type,
            'ext': self.scene_type,
            'files': os.path.basename(path),
            "stagingDir": os.path.dirname(path)
        }
        instance.data["representations"].append(representation)

        # Move the displaced contents of the instance back to wherever they were before
        for moved, parent in instance.data.get("moved").items():
            if not parent:
                cmds.parent(moved, world=True)
            else:
                cmds.parent(moved, parent, relative=True)

        # Clean up the rig sets that pymonk created
        for item in instance.data.get("rig_sets"):
            self.remove_from_scene(item)

        self.log.debug("Extracted instance '%s' to: %s", instance.name, path)
