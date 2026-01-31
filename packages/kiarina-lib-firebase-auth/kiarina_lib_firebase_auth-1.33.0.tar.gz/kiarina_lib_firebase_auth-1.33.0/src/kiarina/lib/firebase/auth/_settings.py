from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings_manager import SettingsManager


class FirebaseAuthSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="KIARINA_LIB_FIREBASE_AUTH_",
        extra="ignore",
    )

    project_id: str
    """
    Firebase project ID
    """

    api_key: SecretStr
    """
    Firebase Web API Key

    Obtain this key from the Firebase Console.
    Project Settings > General > Your apps > Web API Key
    """


settings_manager = SettingsManager(FirebaseAuthSettings, multi=True)
