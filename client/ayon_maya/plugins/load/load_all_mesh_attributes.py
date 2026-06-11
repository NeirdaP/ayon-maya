# -*- coding: utf-8 -*-
"""Combined mesh attributes loader."""
from ayon_maya.plugins.load.load_smooth_mesh_attributes import SmoothMeshAttributesLoader
from ayon_maya.plugins.load.load_arnold_mesh_attributes import ArnoldMeshAttributesLoader
from ayon_maya.plugins.load.load_redshift_mesh_attributes import RedshiftMeshAttributesLoader
from ayon_maya.plugins.load.load_render_stats_mesh_attributes import RenderStatsMeshAttributesLoader


class AllMeshAttributesLoader(SmoothMeshAttributesLoader):
    """
    Loader that applies all mesh attributes at once:
    smooth mesh, arnold, redshift, and render stats.
    """

    label = "Import and assign all mesh attributes"
    order = -11
    icon = "signal"
    color = "orange"

    _sub_loaders = [
        SmoothMeshAttributesLoader,
        ArnoldMeshAttributesLoader,
        RedshiftMeshAttributesLoader,
        RenderStatsMeshAttributesLoader,
    ]

    def load(self, context, name, namespace, data):
        for loader_class in self._sub_loaders:
            loader_class.load(self, context, name, namespace, data)
