from pydantic_settings import BaseSettings
from pydantic_settings_manager import SettingsManager

from ._types.language import Language


class I18nSettings(BaseSettings):
    default_language: Language = "en"
    """Default language to use when translation is not found."""


settings_manager = SettingsManager(I18nSettings)
