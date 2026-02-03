from maya import cmds
import ayon_api
import json

from ayon_core.pipeline.workfile.workfile_template_builder import (
    PlaceholderLoadMixin,
    LoadPlaceholderItem,
)
from ayon_core.pipeline import context_tools, get_representation_path
from ayon_core.lib import attribute_definitions

from ayon_maya.api.lib import (
    get_container_transforms,
    get_node_parent,
    get_node_index_under_parent
)
from ayon_maya.api.workfile_template_builder import (
    MayaPlaceholderPlugin,
)
from enum import Enum


class MayaPlaceholderLoadMixin(PlaceholderLoadMixin):
    def get_load_plugin_options(self, options=None):
        """Unified attribute definitions for load placeholder.

        Common function for placeholder plugins used for loading of
        representations. Use it in 'get_placeholder_options'.

        Args:
            options (Dict[str, Any]): Already available options which are used
                as defaults for attributes.

        Returns:
            List[AbstractAttrDef]: Attribute definitions common for load
                plugins.
        """

        loaders_by_name = self.builder.get_loaders_by_name()
        loader_items = [
            {"value": loader_name, "label": loader.label or loader_name}
            for loader_name, loader in loaders_by_name.items()
        ]

        loader_items = list(sorted(loader_items, key=lambda i: i["label"]))
        group_modes_labels = [group_mode.fullname for group_mode in list(GroupMode)]
        options = options or {}

        # Get product types from all loaders excluding "*"
        product_types = set()
        for loader in loaders_by_name.values():
            product_types.update(loader.product_types)
        product_types.discard("*")

        # Sort for readability
        product_types = list(sorted(product_types))

        builder_type_enum_items = [
            {"label": "Current folder", "value": "context_folder"},
            {"label": "Linked folders", "value": "linked_folders"},
            {"label": "All folders", "value": "all_folders"},
        ]

        link_types = ayon_api.get_link_types(self.builder.project_name)

        # Filter link types for folder to folder links
        link_types_enum_items = [
            {"label": link_type["name"], "value": link_type["linkType"]}
            for link_type in link_types
            if (
                    link_type["inputType"] == "folder"
                    and link_type["outputType"] == "folder"
            )
        ]

        if not link_types_enum_items:
            link_types_enum_items.append(
                {"label": "<No link types>", "value": None}
            )

        build_type_label = "Folder Builder Type"
        build_type_help = (
            "Folder Builder Type\n"
            "\nBuilder type describe what template loader will look"
            " for."
            "\nCurrent Folder: Template loader will look for products"
            " of current context folder (Folder /assets/bob will"
            " find asset)"
            "\nAll folders: All folders matching the regex will be"
            " used."
        )

        product_type = options.get("product_type")
        if product_type is None:
            product_type = options.get("family")

        return [
            attribute_definitions.UISeparatorDef(),
            attribute_definitions.UILabelDef("Main attributes"),
            attribute_definitions.UISeparatorDef(),

            attribute_definitions.EnumDef(
                "builder_type",
                label=build_type_label,
                default=options.get("builder_type"),
                items=builder_type_enum_items,
                tooltip=build_type_help
            ),
            attribute_definitions.EnumDef(
                "link_type",
                label="Link Type",
                items=link_types_enum_items,
                tooltip=(
                    "Link Type\n"
                    "\nDefines what type of link will be used to"
                    " link the asset to the current folder."
                )
            ),
            attribute_definitions.EnumDef(
                "product_type",
                label="Product type",
                default=product_type,
                items=product_types
            ),
            attribute_definitions.TextDef(
                "representation",
                label="Representation name",
                default=options.get("representation"),
                placeholder="ma, abc, ..."
            ),
            attribute_definitions.EnumDef(
                "group_mode",
                label="Group mode",
                default=options.get("group_mode"),
                items=group_modes_labels,
                tooltip=(
                    "Group Mode"
                    "\nDefines how imported products will "
                    "be placed in hierarchy\n"
                    f"{GroupMode.Placeholder.fullname}: Places content at the placeholder's level, "
                    f"no additional grouping\n"
                    f"{GroupMode.Folders.fullname}: Groups products coming from same asset "
                    f"under a group with folder's name"
                )
            ),
            attribute_definitions.EnumDef(
                "loader",
                label="Loader",
                default=options.get("loader"),
                items=loader_items,
                tooltip=(
                    "Loader"
                    "\nDefines what AYON loader will be used to"
                    " load assets."
                    "\nUseable loader depends on current host's loader list."
                    "\nField is case sensitive."
                )
            ),
            attribute_definitions.TextDef(
                "loader_args",
                label="Loader Arguments",
                default=options.get("loader_args"),
                placeholder='{"camera":"persp", "lights":True}',
                tooltip=(
                    "Loader"
                    "\nDefines a dictionary of arguments used to load assets."
                    "\nUseable arguments depend on current placeholder Loader."
                    "\nField should be a valid python dict."
                    " Anything else will be ignored."
                )
            ),
            attribute_definitions.NumberDef(
                "order",
                label="Order",
                default=options.get("order") or 0,
                decimals=0,
                minimum=0,
                maximum=999,
                tooltip=(
                    "Order"
                    "\nOrder defines asset loading priority (0 to 999)"
                    "\nPriority rule is : \"lowest is first to load\"."
                )
            ),
            attribute_definitions.UISeparatorDef(),
            attribute_definitions.UILabelDef("Optional attributes"),
            attribute_definitions.UISeparatorDef(),
            attribute_definitions.TextDef(
                "folder_path",
                label="Folder filter",
                default=options.get("folder_path"),
                placeholder="regex filtering by folder path",
                tooltip=(
                    "Filtering assets by matching"
                    " field regex to folder path"
                )
            ),
            attribute_definitions.TextDef(
                "product_name",
                label="Product filter",
                default=options.get("product_name"),
                placeholder="regex filtering by product name",
                tooltip=(
                    "Filtering assets by matching"
                    " field regex to product name"
                )
            ),
        ]


class MayaPlaceholderLoadPlugin(MayaPlaceholderPlugin, MayaPlaceholderLoadMixin):
    identifier = "maya.load"
    label = "Maya load"

    item_class = LoadPlaceholderItem

    def _create_placeholder_name(self, placeholder_data):

        # Split builder type: context_assets, linked_assets, all_assets
        prefix, suffix = placeholder_data["builder_type"].split("_", 1)
        parts = [prefix]

        # add family if any
        placeholder_product_type = placeholder_data.get("product_type")
        if placeholder_product_type is None:
            placeholder_product_type = placeholder_data.get("family")

        if placeholder_product_type:
            parts.append(placeholder_product_type)

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

    def _parent_in_hierarchy(self, placeholder, containers):
        """Parent loaded container to placeholder's parent.

        ie : Set loaded content as placeholder's sibling

        Args:
            container (str): Placeholder loaded containers
        """

        if not containers:
            return

        # TODO: This currently returns only a single root but a loaded scene
        #   could technically load more than a single root
        if not isinstance(containers, list):
            containers = [containers]

        group_mode = placeholder.data.get("group_mode")
        for container in containers:
            container_representation_id = cmds.getAttr(f"{container}.representation")
            project_name = context_tools.get_current_project_name()
            representation = ayon_api.get_representation_by_id(
                project_name=project_name,
                representation_id=container_representation_id
            )

            context = representation["context"]

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
            placeholder_parent = get_node_parent(placeholder.scene_identifier)
            scene_parent = placeholder_parent
            version_id = representation["versionId"]

            if group_mode == GroupMode.Folders.fullname:
                representations = ayon_api.get_representations(
                    project_name=context["project"]["name"],
                    version_ids={version_id},
                    representation_names={"json"}
                )
                json_path = get_representation_path(next(representations))
                with open(json_path) as json_file:
                    data = json.load(json_file)
                    folder_name = data["input_folders"][0]["name"]
                    scene_parent = f"{placeholder_parent}|{folder_name}"

            if not cmds.objExists(scene_parent):
                name = scene_parent.split("|")[-1]
                cmds.group(name=name, parent=placeholder_parent, empty=True)

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
    Placeholder = "Placeholder level"
    Folders = "Group products from same folder"

    def __new__(cls, value):
        member = object.__new__(cls)
        member._value_ = value
        member.fullname = value
        return member
