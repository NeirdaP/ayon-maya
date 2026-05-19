from ayon_server.settings import (
    BaseSettingsModel,
    SettingsField
    )

class RepresentationsModel(BaseSettingsModel):
    _layout = "expanded"
    representation: str = SettingsField("", title="Representation")

class IgnoreRepresentationsModel(BaseSettingsModel):
    _isGroup: bool = True
    repres_to_ignore: list[RepresentationsModel] = SettingsField(
        default_factory=list, title="Ignore Representations"
    )

DEFAULT_REPRE_IGNORE_SETTINGS = {
    "repres_to_ignore": []
}