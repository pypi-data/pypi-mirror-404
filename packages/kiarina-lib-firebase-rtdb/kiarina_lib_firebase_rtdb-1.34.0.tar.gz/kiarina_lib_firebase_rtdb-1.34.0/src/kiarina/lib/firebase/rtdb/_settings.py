from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings_manager import SettingsManager


class RTDBSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="KIARINA_LIB_FIREBASE_RTDB_",
        extra="ignore",
    )

    max_retry_delay: float = 60.0
    """
    Maximum delay between retries in seconds.
    Default: 60.0
    """

    initial_retry_delay: float = 1.0
    """
    Initial delay between retries in seconds.
    Default: 1.0
    """

    retry_delay_multiplier: float = 2.0
    """
    Exponential backoff multiplier for retry delays.
    Default: 2.0
    """


settings_manager = SettingsManager(RTDBSettings)
