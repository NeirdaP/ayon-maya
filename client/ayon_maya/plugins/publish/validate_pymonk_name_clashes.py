import ayon_maya.api.action
from ayon_core.pipeline.publish import (
    PublishValidationError,
    ValidateContentsOrder,
)
from ayon_maya.api import plugin
from maya import cmds


class ValidatePymonkNameClashes(plugin.MayaInstancePlugin):
    """Validates whether the scene contains any names that would clash with names 
        created by pymonk actorize()."""

    order = ValidateContentsOrder
    label = 'Pymonk Name Clashes'
    actions = [ayon_maya.api.action.SelectInvalidAction]
    families = ['actorbase']

    @classmethod
    def get_invalid(cls, instance):
        # Get the disallowed names from pymonk
        import pymonk
        pymonk_nodes_to_create = pymonk.get_actorize_node_names_before_creation()
    
        # Node is invalid if it already exists in scene
        invalid = list()
        for node in pymonk_nodes_to_create:
            exists = cmds.ls(str(node), dagObjects=True)
            if exists:
                invalid.extend(exists)
        return invalid
    

    def process(self, instance):
        invalid = self.get_invalid(instance)
        if invalid:
            names = "\n".join(invalid)
            raise PublishValidationError(
                title="Name clashes",
                message="The following nodes in the scene clash with a " \
                "name that will be created by pymonk actorize:\n{}".format(names)
            )
