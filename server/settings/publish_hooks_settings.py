from ayon_server.settings import (
    BaseSettingsModel,
    SettingsField,
    task_types_enum,
)


class PublishHooksBuildProfilesModel(BaseSettingsModel):
    _layout = "expanded"
    task_types: list[str] = SettingsField(
        default_factory=list,
        title="Task types",
        enum_resolver=task_types_enum
    )
    path: str = SettingsField("", title="Path to hooks folder")


class PublishHooksModel(BaseSettingsModel):
    enabled: bool = SettingsField(title="PublishHooks")
    optional: bool = SettingsField(title="Optional")
    active: bool = SettingsField(title="Active")
    families: list[str] = SettingsField(default_factory=list, title="Product Types")
    profiles: list[PublishHooksBuildProfilesModel] = SettingsField(
        default_factory=list,
        title="Profiles"
    )
