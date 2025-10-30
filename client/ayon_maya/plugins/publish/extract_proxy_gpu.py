# -*- coding: utf-8 -*-
"""Proxy gpu extractor."""
from __future__ import annotations
import os
from ayon_maya.api import plugin
from ayon_maya.plugins.publish.extract_actor_base import create_pymonk_rig
from maya import cmds


class ExtractProxyGPU(plugin.MayaExtractorPlugin):
    """"""
    import pyblish.api
    order = pyblish.api.ExtractorOrder + .1     # Plugin runs after extract_gpu_cache
    label = "Proxy GPU (.ma)"
    families = ["proxygpu"]
    targets = ["local", "remote"]
    

    def get_gpu_cache_publish_path_from_context(self, instance):        
        import os
        from ayon_core.pipeline.anatomy.anatomy import Anatomy 
        from ayon_core.pipeline.template_data import get_template_data
        from ayon_core.pipeline.context_tools import get_current_folder_entity, \
                                                get_current_project_entity, \
                                                get_current_task_entity, \
                                                get_current_host_name

        # Use ayon api & templates to determine the gpu cache published location
        project_entity = get_current_project_entity()
        anatomy = Anatomy(project_entity.get("name"), project_entity=project_entity)
        template_data = get_template_data(project_entity, get_current_folder_entity(), get_current_task_entity(), get_current_host_name())
        template_data["product"] = {"type" : instance.data.get("productType"), "name" : instance.data.get("productName")}
        template_data["ext"] = "abc"
        template_data["output"] = "gpu_cache"
        publish_template = anatomy.get_template_item("hero", "default")
         
        return os.path.join(publish_template["directory"].format_strict(template_data), 
                            publish_template["file"].format_strict(template_data))

    
    def load_gpu_cache(self, path, folder_name, product_name, namespace=None):
        from ayon_maya.api.lib import unique_namespace

        # Logic for loading a gpu cache into a new maya scene
        namespace = namespace or unique_namespace(
            folder_name + "_",
            prefix="_" if folder_name[0].isdigit() else "",
            suffix="_",
        )
        cmds.loadPlugin("gpuCache", quiet=True)

        # Root group
        label = "{}:{}".format(namespace, product_name)
        root = cmds.group(name=label, empty=True)

        # Create transform with shape
        transform_name = label + "_GPU"
        transform = cmds.createNode("transform", name=transform_name,
                                    parent=root)
        cache = cmds.createNode("gpuCache",
                                parent=transform,
                                name=f"{transform_name}Shape")

        # Set the cache filepath
        cmds.setAttr(cache + '.cacheFileName', path, type="string")
        cmds.setAttr(cache + '.cacheGeomPath', "|", type="string")    # root
        if cmds.attributeQuery("aiNamespace", node=cache, exists=True):
            # Set Arnold namespace attribute to ensure shaders are loaded uniquely
            # when a gpu cache is loaded multiple times
            cmds.setAttr(cache + '.aiNamespace', namespace, type="string")

        # Lock parenting of the transform and cache
        cmds.lockNode([transform, cache], lock=True)
        return (root, cache)


    def process(self, instance):
        """Extractor entry point."""

        # Identify the previously exported gpu cache in instance representations
        gpu_cache_staged_path = None
        for representation in instance.data.get("representations") or []:
            if representation.get("name") == "gpu_cache":
                gpu_cache_staged_path = os.path.join(representation.get("stagingDir"), representation.get("files"))

        if not gpu_cache_staged_path:
            self.log.warning("Cannot extract proxy gpu maya scene because cannot locate staged gpu cache! \
                             Check that the extract_gpu_cache plugin successfully ran.")
            return
        
        # Open a new maya scene and load the staged path of the gpu cache
        # Store the original workfile path so as not to corrupt workfile versioning
        original_workfile_path = cmds.file(query=True, sceneName=True)
        cmds.file(save=True)            
        cmds.file(force=True, newFile=True)        

        name = instance.data.get("folderPath").split("/")[-1]
        root, cache = self.load_gpu_cache(gpu_cache_staged_path, name, instance.data.get("productName"))
        cmds.refresh()  # Refresh the scene to ensure cache is evaluated before running actorize

        # Run actorize on the gpu cache root that was loaded
        # This will also create the needed rig sets and mark everything with cbids
        created_sets = create_pymonk_rig([root], self.log)

        if not created_sets:
            self.log.warning("Actorize did not complete successfully, skipping proxygpu extraction")
            return

        # Change the filepath on the gpu cache to point to the final published path
        gpu_cache_publish_path = self.get_gpu_cache_publish_path_from_context(instance)
        cmds.setAttr(cache + '.cacheFileName', gpu_cache_publish_path, type="string")

        # Create the .ma representation and store on the instance
        staging_dir = self.staging_dir(instance)
        ma_repre_file = "{}_proxygpu.ma".format(instance.name)
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

        # Add representation to instance data
        if "representations" not in instance.data:
            instance.data["representations"] = []

        ma_representation = {
            'name': "ma",
            'ext': "ma",
            'files': ma_repre_file,
            "stagingDir": staging_dir
        }
        instance.data["representations"].append(ma_representation)

        # Re-open original workfile to ensure proper workfile versioning
        cmds.file(original_workfile_path, open=True, force=True)

        self.log.debug(
            f"Extracted instance '{instance.name}' to: {staging_dir}"
        )
