from __future__ import annotations
import json
from enum import Enum

from maya import cmds
import ayon_api
from ayon_core.pipeline.workfile.workfile_template_builder import (
    PlaceholderLoadMixin,
    LoadPlaceholderItem,
)
from ayon_core.pipeline import context_tools, get_representation_path
from ayon_core.lib import attribute_definitions

from ayon_maya.api.lib import (
    get_container_transforms,
    get_highest_in_hierarchy,
    get_node_parent,
    get_node_index_under_parent
)
from ayon_maya.api.workfile_template_builder import (
    MayaPlaceholderPlugin,
)


class MayaPlaceholderLoadMixin(PlaceholderLoadMixin):
    def get_load_plugin_options(self, options=None):
        """
        Override of ayon_core's PlaceholderLoadMixin to add custom options
        For now we only add the option "group_mode"
        """
        options = options or {}

        group_modes_labels = [group_mode.fullname for group_mode in list(GroupMode)]

        inherited_options = super().get_load_plugin_options(options)
        loader_option = [option for option in inherited_options if option.label == "Loader"][0]
        folder_filter_option = [option for option in inherited_options if option.label == "Folder filter"][0]
        loader_option_index = inherited_options.index(loader_option)
        folder_filter_index = inherited_options.index(folder_filter_option)
        inherited_options.insert(
            loader_option_index + 1,  # Add 'group_mode' option exactly after the 'loader' option
            attribute_definitions.EnumDef(
                "group_mode",
                label="Group mode",
                items=group_modes_labels,
                default=options.get("group_mode") if options else None,
                tooltip=(
                    "Group Mode"
                    "\nDefines how imported products will "
                    "be placed in hierarchy\n"
                    f"{GroupMode.PLACEHOLDER.fullname}: Places content at the placeholder's level, "
                    f"no additional grouping\n"
                    f"{GroupMode.FOLDER.fullname}: Groups products coming from same asset "
                    f"under a group with folder's name"
                )
            )
        )

        inherited_options.insert(
            folder_filter_index + 1,  # Add 'folder_type_filter' option exactly after the 'folder_filter' option
            attribute_definitions.TextDef(
                "folder_type_filter",
                label="Folder type filter",
                default=options.get("folder_type_filter"),
                placeholder="Character, Prop..."
            )
        )
        return inherited_options

    def _get_representations(self, placeholder):
        """
        Override to apply the product type filter on representations
        For now, the product type filter only works if the representation
        has the related custom json representation to retrieve its original folder
        """

        representations = super()._get_representations(placeholder)

        filtered_representations = []
        folder_type_filter = placeholder.data.get("folder_type_filter", "")
        folder_type_filter_list = folder_type_filter.strip().split(",")

        if folder_type_filter_list:
            for representation in representations:
                folder_type = representation["context"]["folder"]["type"]
                related_json_path = get_related_json_representation_path(representation)
                if related_json_path:
                    with open(related_json_path) as json_file:
                        data = json.load(json_file)
                        try:
                            project_name = representation["context"]["project"]["name"]
                            folder_id = data["input_folders"][0]["id"]
                            folder = ayon_api.get_folder_by_id(project_name, folder_id)
                            folder_type = folder["folderType"]
                        except KeyError as e:
                            print(e)

                if folder_type in folder_type_filter_list:
                    filtered_representations.append(representation)
        else:
            filtered_representations = representations
        return filtered_representations


class MayaPlaceholderLoadPlugin(MayaPlaceholderPlugin, MayaPlaceholderLoadMixin):
    identifier = "maya.load"
    label = "Maya load"

    item_class = LoadPlaceholderItem

    def _create_placeholder_name(self, placeholder_data):

        # Split builder type: context_assets, linked_assets, all_assets
        prefix, suffix = placeholder_data["builder_type"].split("_", 1)
        parts = [prefix]

        # add family if any
        placeholder_product_base_type = (
            placeholder_data.get("product_base_type")
            or placeholder_data.get("product_type")
            or placeholder_data.get("family")
        )

        if placeholder_product_base_type:
            parts.append(placeholder_product_base_type)

        # add loader arguments if any
        loader_args = placeholder_data["loader_args"]
        if loader_args:
            loader_args = eval(loader_args)
            for value in loader_args.values():
                parts.append(str(value))

        parts.append(suffix)
        placeholder_name = "_".join(parts)

        return placeholder_name.capitalize()

    def _get_loaded_repre_ids(self):
        loaded_representation_ids = self.builder.get_shared_populate_data(
            "loaded_representation_ids"
        )
        if loaded_representation_ids is None:
            try:
                containers = cmds.sets("AVALON_CONTAINERS", q=True)
            except ValueError:
                containers = []

            loaded_representation_ids = {
                cmds.getAttr(container + ".representation")
                for container in containers
            }
            self.builder.set_shared_populate_data(
                "loaded_representation_ids", loaded_representation_ids
            )
        return loaded_representation_ids

    def populate_placeholder(self, placeholder):
        self.populate_load_placeholder(placeholder)

    def repopulate_placeholder(self, placeholder):
        repre_ids = self._get_loaded_repre_ids()
        self.populate_load_placeholder(placeholder, repre_ids)

    def get_placeholder_options(self, options=None):
        return self.get_load_plugin_options(options)

    def load_succeed(self, placeholder, container):
        self._parent_in_hierarchy(placeholder, container)

    def get_scene_parent(self, container, placeholder):
        group_mode = placeholder.data.get("group_mode")
        container_representation_id = cmds.getAttr(f"{container}.representation")
        project_name = context_tools.get_current_project_name()

        representation = ayon_api.get_representation_by_id(
            project_name=project_name,
            representation_id=container_representation_id
        )

        context = representation["context"]

        placeholder_parent = get_node_parent(placeholder.scene_identifier)
        scene_parent = placeholder_parent

        if group_mode == GroupMode.FOLDER.fullname:
            # Content will be parented under a group with the name of the parent's folder
            # First we check if a json representation exists next to the current one
            # if so, we get the folder name from this json instead of the current context
            representation_path = get_related_json_representation_path(representation)

            if representation_path:
                with open(representation_path) as json_file:
                    data = json.load(json_file)
                    folder_name = data["input_folders"][0]["name"]

            else:
                folder_name = context["folder"]["name"]

            scene_parent = f"{folder_name}"
            if placeholder_parent:
                scene_parent = f"{placeholder_parent}|{scene_parent}"

        return scene_parent

    def _parent_in_hierarchy(self, placeholder, containers):
        """Parent loaded container to placeholder's parent.

        ie : Set loaded content as placeholder's sibling
        Adds a folder group to the imported content depending on the group_mode value (see GroupMode class)
        Args:
            placeholder (MayaPlaceholderPlugin): Placeholder object
            containers (str): Placeholder loaded containers
        """

        if not containers:
            return

        # TODO: This currently returns only a single root but a loaded scene
        #   could technically load more than a single root
        if not isinstance(containers, list):
            containers = [containers]

        for container in containers:

            scene_parent = self.get_scene_parent(container, placeholder)
            container_root = get_container_transforms(container, root=True)
            # Bugfix: The get_container_transforms does not recognize the load
            # reference group currently
            # TODO: Remove this when it does
            parent = get_node_parent(container_root)
            if parent:
                container_root = parent
            roots = [container_root]
            # Add the loaded roots to the holding sets if they exist
            holding_sets = cmds.listSets(object=placeholder.scene_identifier) or []
            for holding_set in holding_sets:
                cmds.sets(roots, forceElement=holding_set)

            # Parent the roots to the place of the placeholder locator and match
            # its matrix
            placeholder_form = cmds.xform(
                placeholder.scene_identifier,
                query=True,
                matrix=True,
                worldSpace=True
            )

            if scene_parent and not cmds.objExists(scene_parent):
                name = scene_parent.split("|")[-1]
                placeholder_parent = get_node_parent(placeholder.scene_identifier)
                
                if placeholder_parent:
                    cmds.group(name=name, parent=placeholder_parent, empty=True)
                else:
                    cmds.group(name=name, empty=True)

            for node in set(roots):
                cmds.xform(node, matrix=placeholder_form, worldSpace=True)

                if scene_parent != get_node_parent(node):
                    if scene_parent:
                        node = cmds.parent(node, scene_parent)[0]
                    else:
                        node = cmds.parent(node, world=True)[0]

                # Move loaded nodes in index order next to their placeholder node
                cmds.reorder(node, back=True)
                index = get_node_index_under_parent(placeholder.scene_identifier)
                cmds.reorder(node, front=True)
                cmds.reorder(node, relative=index + 1)


class GroupMode(Enum):
    PLACEHOLDER = "Placeholder level"
    FOLDER = "Group products from same folder"

    def __new__(cls, value):
        member = object.__new__(cls)
        member._value_ = value
        member.fullname = value
        return member


def get_related_json_representation_path(representation):
    context = representation["context"]
    version_id = representation["versionId"]
    project_name = context["project"]["name"]
    representations = ayon_api.get_representations(
        project_name=project_name,
        version_ids={version_id},
        representation_names={"json"}
    )

    representation = next(representations, None)
    if representation:
        return get_representation_path(representation)
