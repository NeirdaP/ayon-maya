# -*- coding: utf-8 -*-
"""Creator of Redshift proxy render product types."""

from ayon_maya.api import plugin

class CreateRedshiftProxyRender(plugin.MayaCreator):
    """Create instance of Redshift Proxy Render product."""

    identifier = "io.openpype.creators.maya.redshiftproxyrender"
    label = "Redshift Proxy Render"
    product_type = "redshiftproxyrender"
    icon = "gears"