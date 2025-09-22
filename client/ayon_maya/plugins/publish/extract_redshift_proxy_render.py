# -*- coding: utf-8 -*-
"""Redshift Proxy extractor."""
from __future__ import annotations
import os
from typing import Union

from ayon_core.pipeline.context_tools import get_current_folder_entity, \
                                        get_current_project_entity, \
                                        get_current_task_entity, \
                                        get_current_host_name
from ayon_maya.api.lib import maintained_selection, renderlayer, namespaced, unique_namespace
from ayon_maya.api import plugin
from ayon_maya.api.render_setup_tools import (
    allow_export_from_render_setup_layer,
)
from maya import cmds


class ExtractRedshiftProxyRender(plugin.MayaExtractorPlugin):
    """Extract the content of the instance to a redshift proxy file and place in an .ma file."""

    label = "Redshift Proxy Render (.ma)"
    families = ["redshiftproxyrender"]
    targets = ["local", "remote"]

    def get_rs_publish_path_from_context(self, instance):
        from ayon_core.pipeline.anatomy.anatomy import Anatomy 
        from ayon_core.pipeline.template_data import get_template_data

        project_entity = get_current_project_entity()
        anatomy = Anatomy(project_entity.get("name"), project_entity=project_entity)
        template_data = get_template_data(project_entity, get_current_folder_entity(), get_current_task_entity(), get_current_host_name())
        template_data["product"] = {"type" : instance.data.get("productType"), "name" : instance.data.get("productName")}
        template_data["ext"] = "rs"
        publish_template = anatomy.get_template_item("hero", "default")
         
        return os.path.join(publish_template["directory"].format_strict(template_data), 
                            publish_template["file"].format_strict(template_data))


    def process(self, instance):
        from ayon_maya.plugins.load.load_redshift_proxy import RedshiftProxyLoader

        """Extractor entry point."""
        # Make sure Redshift is loaded
        cmds.loadPlugin("redshift4maya", quiet=True)

        # TODO might remove the animation attributes altogether based on feedback from testing
        anim_on = False
        if anim_on:
            # Add frame number #### placeholder for animated exports
            file_name = "{}.####.rs".format(instance.name)
        else:
            file_name = "{}.rs".format(instance.name)

        staging_dir = self.staging_dir(instance)
        rs_file_path = os.path.join(staging_dir, file_name)

        rs_options = "exportConnectivity=0;enableCompression=1;keepUnused=0;"
        rs_repr_files: Union[str, list[str]] = file_name
        if not anim_on:
            # Remove animation information because it is not required for
            # non-animated products
            keys = ["frameStart",
                    "frameEnd",
                    "handleStart",
                    "handleEnd",
                    "frameStartHandle",
                    "frameEndHandle"]
            for key in keys:
                instance.data.pop(key, None)
        
        else:
            start_frame = instance.data["frameStartHandle"]
            end_frame = instance.data["frameEndHandle"]
            rs_options = "{}startFrame={};endFrame={};frameStep={};".format(
                rs_options, start_frame,
                end_frame, instance.data["step"]
            )
            rs_repr_files: list[str] = []
            for frame in range(
                    int(start_frame),
                    int(end_frame) + 1,
                    int(instance.data["step"])):
                frame_padded = str(frame).rjust(4, "0")
                frame_filename = file_name.replace(
                    ".####.rs", f".{frame_padded}.rs"
                )
                rs_repr_files.append(frame_filename)
        

        # Write out rs file
        self.log.debug("Writing: '%s'", rs_file_path)

        # Allow overriding what renderlayer to export from. By default, force
        # it to the default render layer. (Note that the renderlayer isn't
        # currently exposed as an attribute to artists)
        layer = instance.data.get("renderLayer", "defaultRenderLayer")
        with maintained_selection():
            with renderlayer(layer):
                with allow_export_from_render_setup_layer():
                    cmds.select(instance.data["setMembers"], noExpand=True)
                    cmds.file(rs_file_path,
                              preserveReferences=False,
                              force=True,
                              type="Redshift Proxy",
                              exportSelected=True,
                              options=rs_options)
                    

        # Store workfile path, then open a new maya scene to create second representation
        original_workfile_path = cmds.file(query=True, sceneName=True)            
        cmds.file(force=True, newFile=True)
        
        # Create a redshift proxy and set the filepath to the publish path of the rs representation
        rs_publish_path = self.get_rs_publish_path_from_context(instance)
        redshift_proxy_loader = RedshiftProxyLoader()
        folder_name = get_current_folder_entity().get("name")
        namespace = unique_namespace(
            folder_name + "_",
            prefix="_" if folder_name[0].isdigit() else "",
            suffix="_",
        )

        # Load logic copied from load_redshift_proxy.py
        with maintained_selection():
            cmds.namespace(addNamespace=namespace)
            with namespaced(namespace, new=False):
                nodes, group_node = redshift_proxy_loader.create_rs_proxy(folder_name, rs_publish_path)
        proxy = nodes[0]  # RedshiftProxyMesh
        redshift_proxy_loader._set_rs_proxy_file_type(proxy, rs_publish_path)

        ma_repre_file = "{}.ma".format(instance.name)
        path = os.path.join(staging_dir, ma_repre_file)
        cmds.file(rename=path)
        cmds.file(  save=True,
                    type="mayaAscii",
                    force=True,
                    preserveReferences=False,
                    channels=True,
                    constraints=True,
                    expressions=True,
                    constructionHistory=True)

        # Add both representations to instance data
        if "representations" not in instance.data:
            instance.data["representations"] = []

        rs_representation = {
            'name': 'rs',
            'ext': 'rs',
            'files': rs_repr_files,
            "stagingDir": staging_dir,
        }
        ma_representation = {
            'name': "ma",
            'ext': "ma",
            'files': ma_repre_file,
            "stagingDir": staging_dir
        }
        instance.data["representations"].append(rs_representation)
        instance.data["representations"].append(ma_representation)

        # Re-open original workfile to ensure proper workfile versioning
        cmds.file(original_workfile_path, open=True, force=True)

        self.log.debug(
            f"Extracted instance '{instance.name}' to: {staging_dir}"
        )
