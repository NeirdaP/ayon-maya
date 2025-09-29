# -*- coding: utf-8 -*-
"""Maya subdivision level collector."""
import pyblish.api
from ayon_maya.api import plugin
from maya import cmds  # noqa


class CollectSubdivision(plugin.MayaInstancePlugin):
    """Collect subdivision data on meshes of the instance.
    """
    order = pyblish.api.CollectorOrder + 0.3
    families = ["look", "lookanim"]
    label = "Collect Subdivision"

    subdiv_attributes = ["smoothLevel"]

    def process(self, instance):
        """For each node in instance, check if it has the above subdiv_attributes, 
        and if so, add it to the instance's lookData. 

        Note: This plugin assumes that the lookData dict already exists and therefore 
        should be running after the collect_look plugin. 
        """

        # Add the value to the lookData attributes 
        lookData = instance.data.get("lookData")        
        if not lookData or not lookData.get("attributes"):
            self.log.warning("Instance look data does not exist, cannot add attributes (check plugin ordering)")
            return 
        
        for entry in instance.data["lookData"]["attributes"]:
            node = entry.get("name")

            for attr in self.subdiv_attributes:
                if not cmds.attributeQuery(attr, node=node, exists=True):
                    self.log.debug("Attribute {} does not exist on {}, skipping its collection".format(attr, node))
                    continue

                attribute = "{}.{}".format(node, attr)
                # We don't support mixed-type attributes yet.
                if cmds.attributeQuery(attr, node=node, multi=True):
                    self.log.warning("Attribute '{}' is mixed-type and is "
                                     "not supported yet.".format(attribute))
                    continue

                # Maya has a tendency to return string attribute values as
                # `None` if it is an empty string and the attribute has never
                # been set but is still at default value.
                attribute_type = cmds.getAttr(attribute, type=True)
                value = cmds.getAttr(attribute, asString=True)
                if value is None:
                    # If the attribute type is `string` we will convert it
                    # to enforce an empty string value
                    if attribute_type == "string":
                        value = ""
                    else:
                        continue

                # Add this item to the current entry's attributes
                entry["attributes"][attr] = value
    