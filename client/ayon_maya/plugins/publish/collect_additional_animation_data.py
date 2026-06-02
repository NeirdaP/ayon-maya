from ayon_maya.api import plugin
import pyblish.api
import ayon_api

ADDITIONAL_ANIMATION_DATA_KEY = "additional_animation_data"
FOLDER_NAME_KEY = "source_folder_name"
FOLDER_ID_KEY = "source_folder_id"
FOLDER_TYPE_KEY = "source_folder_type"
NAMESPACE_KEY = "namespace"


class CollectAdditionalAnimationData(plugin.MayaInstancePlugin):
    """
    Collects additional animation data needed for Supamonks' workflow,
    that is not already covered by default collectors.
    For now, we retrieve the id, name and type of the folder the alembic originates from.
    These additional data are stored in a dict in all representations of the product.
    You can access it like this: representation["data"][ADDITIONAL_ANIMATION_DATA_KEY]
    """
    order = pyblish.api.IntegratorOrder - 0.1  # Execute after all representations are collected
    label = "Collect Additional Animation Data"
    families = ["animation"]

    def process(self, instance):
        project_name = instance.data["projectEntity"]["name"]
        version_ids = instance.data.get("inputVersions")

        if not version_ids:
            return

        variant = instance.data.get("variant")

        version_id = version_ids[0]
        source_version = ayon_api.get_version_by_id(
            project_name=project_name,
            version_id=version_id,
            fields=["productId"]
        )

        if not source_version:
            return

        source_product = ayon_api.get_product_by_id(
            project_name=project_name,
            product_id=source_version["productId"],
            fields=["folderId"]
        )

        source_folder = ayon_api.get_folder_by_id(
            project_name=project_name,
            folder_id=source_product["folderId"],
        )

        if not source_folder:
            return

        # Injection dans les représentations
        for repre in instance.data.get("representations", []):
            if "data" not in repre:
                repre["data"] = {}

            repre["data"].update({
                ADDITIONAL_ANIMATION_DATA_KEY: {
                    NAMESPACE_KEY: variant,
                    FOLDER_NAME_KEY: source_folder["name"],
                    FOLDER_TYPE_KEY: source_folder["folderType"],
                    FOLDER_ID_KEY: source_folder["id"]
                }
            })


