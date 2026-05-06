import json
import os
from ayon_maya.api import plugin
import ayon_api
from ayon_core.pipeline.publish.input_versions import serialize_input_versions

class ExtractAnimationInputs(plugin.MayaExtractorPlugin):
    """Extract the name of the folder from which the product that created this instance originates.
    Also extract the variant's name of this instance.

    The name of the variant allows us to know from which asset and (which occurence of it) the animation product
    comes from and thus set the appropriate namespace in the lighting scene or else.

    """
    label = "Extract Animation Inputs"
    families = ["animation"]
    optional = False

    def process(self, instance):
        project_name = instance.data["projectEntity"]["name"]
        variant = instance.data.get("variant",None)
        if not variant:
            self.log.warning(f"Can't find variant name in instance {instance.name}. The load in the lighting scene might not be doable.")
        
        json_data = {
            "namespace": variant
        }
        if instance.data["inputVersions"]:
            # Serialize the input versions and get either version id or hero version id depending on settings
            serialized_input_versions = serialize_input_versions(instance.data.get("inputVersions"))
            serialized_input_version_ids = []
            for version in serialized_input_versions:
                if version.get("data").get("hero"):
                    serialized_input_version_ids.append(version.get("data").get("hero_version_id"))
                else:
                    serialized_input_version_ids.append(version.get("version_id"))
            input_versions = ayon_api.get_versions(
                project_name=project_name,
                version_ids=serialized_input_version_ids,
                fields=["productId"]
            )
            input_products = ayon_api.get_products(
                project_name=project_name,
                product_ids=[v["productId"] for v in input_versions],
                fields=["folderId"]
            )
            input_folders = ayon_api.get_folders(
                project_name=project_name,
                folder_ids=[p["folderId"] for p in input_products],
                fields=["id", "name"]
            )
            json_data.update({
                "input_folders":[{"id": folder["id"],"name": folder["name"]} for folder in input_folders]
            })

        json_filename = f"{instance.name}.json"
        stagingdir = self.staging_dir(instance)
        json_path = os.path.join(stagingdir, json_filename)

        with open(json_path, "w+") as file:
            json.dump(json_data, fp=file, indent=2)

        json_representation = {
            'name': 'json',
            'ext': 'json',
            'files': json_filename,
            "stagingDir": stagingdir,
        }
        instance.data["representations"].append(json_representation)
        self.log.info(f"Extracted these data in json : {json_data}")
        self.log.debug(f"Extracted instance '{instance.name}' to: {json_representation}")
