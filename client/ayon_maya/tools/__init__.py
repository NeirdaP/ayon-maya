import os
from ayon_core.tools.utils.host_tools import qt_app_context


class MayaToolsSingleton:
    _look_assigner = None


def get_look_assigner_tool(parent):
    """Create, cache and return look assigner tool window."""
    if MayaToolsSingleton._look_assigner is None:
        from .mayalookassigner import MayaLookAssignerWindow
        mayalookassigner_window = MayaLookAssignerWindow(parent)
        MayaToolsSingleton._look_assigner = mayalookassigner_window
    return MayaToolsSingleton._look_assigner


def show_look_assigner(parent=None):
    """Look manager is Maya specific tool for look management."""

    with qt_app_context():
        look_assigner_tool = get_look_assigner_tool(parent)
        look_assigner_tool.show()

        # Pull window to the front.
        look_assigner_tool.raise_()
        look_assigner_tool.activateWindow()
        look_assigner_tool.showNormal()


def show_blast_manager():
    import maya.cmds as cmds
    try:
        import blast_manager.controller.maya.maya_controller as maya_controller
        from blast_manager.gui.main_panel import PlayblastGui
    except ImportError as e:
        print(f"Can't import blast_manager: {e}")
        return

    user_path = os.path.expanduser("~")
    blast_manager_path = os.path.join(user_path, "blast_manager")
    scene_path = cmds.file(q=True, sn=True)
    playblast_gui = PlayblastGui(
        parent=maya_controller.get_maya_main_window(),
        controller_type=maya_controller.MayaBlastController,
        local_path=blast_manager_path,
        scene_path=scene_path,
        default_camera=None,
        third_party_open=[]
    )
    playblast_gui.show()

