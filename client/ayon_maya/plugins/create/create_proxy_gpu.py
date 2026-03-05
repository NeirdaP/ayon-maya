from maya import cmds
from ayon_maya.api import lib, plugin
from ayon_core.lib import BoolDef


def _get_animation_attr_defs(
        create_context,
        include_user_defined_attributes,
        include_parent_hierarchy=False):
    """Get Animation generic definitions."""
    defs = lib.collect_animation_defs(create_context=create_context)
    defs.extend(
        [
            BoolDef("farm", label="Submit to Farm"),
            BoolDef("refresh", label="Refresh viewport during export"),
            BoolDef(
                "includeParentHierarchy",
                label="Include Parent Hierarchy",
                tooltip=(
                    "Whether to include parent hierarchy of nodes in the "
                    "publish instance."
                ),
                default=include_parent_hierarchy
            ),
            BoolDef(
                "includeUserDefinedAttributes",
                label="Include User Defined Attributes",
                tooltip=(
                    "Whether to include all custom maya attributes found "
                    "on nodes as attributes in the Alembic data."
                ),
                default=include_user_defined_attributes
            ),
        ]
    )

    return defs


def convert_legacy_alembic_creator_attributes(node_data, class_name):
    """This is a legacy transfer of creator attributes to publish attributes
    for ExtractAlembic/ExtractAnimation plugin.
    """
    publish_attributes = node_data["publish_attributes"]

    if class_name in publish_attributes:
        return node_data

    attributes = [
        "attr",
        "attrPrefix",
        "visibleOnly",
        "writeColorSets",
        "writeFaceSets",
        "writeNormals",
        "renderableOnly",
        "visibleOnly",
        "worldSpace",
        "renderableOnly"
    ]
    plugin_attributes = {}
    for attr in attributes:
        if attr not in node_data["creator_attributes"]:
            continue
        value = node_data["creator_attributes"].pop(attr)

        plugin_attributes[attr] = value

    publish_attributes[class_name] = plugin_attributes

    return node_data


class CreateProxyGpu(plugin.MayaCreator):
    """Creator for alembic proxy gpu cache"""

    identifier = "io.openpype.creators.maya.proxygpu"
    label = "Proxy GPU"
    product_base_type = "proxygpu"
    product_type = product_base_type
    icon = "gears"
    include_user_defined_attributes = False

    def read_instance_node(self, node):
        node_data = super(CreateProxyGpu, self).read_instance_node(node)
        node_data = convert_legacy_alembic_creator_attributes(
            node_data, "ExtractAlembic"
        )
        return node_data

    def get_instance_attr_defs(self):
        return _get_animation_attr_defs(self.create_context,
                                        self.include_user_defined_attributes)

    def create(self, product_name, instance_data, pre_create_data):
        instance = super(CreateProxyGpu, self).create(
            product_name, instance_data, pre_create_data
        )
        instance_node = instance.get("instance_node")

        # For Arnold standin proxy
        proxy_set = cmds.sets(name=instance_node + "_proxy_SET", empty=True)
        cmds.sets(proxy_set, forceElement=instance_node)
