from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings_manager import SettingsManager


class AppContextSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="KIARINA_LLM_APP_CONTEXT_")

    app_author: str = "kiarina"
    """
    Default value for the application author.

    Alphanumeric characters, dots, underscores, hyphens, and spaces are allowed.
    Leading and trailing dots, as well as spaces, are not allowed.
    """

    app_name: str = "kiarina-llm"
    """
    Default value for the application name.

    Alphanumeric characters, dots, underscores, hyphens, and spaces are allowed.
    Leading and trailing dots, as well as spaces, are not allowed.
    """


settings_manager = SettingsManager(AppContextSettings)
