from typing import Any

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings_manager import SettingsManager


class OpenAISettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="KIARINA_LIB_OPENAI_")

    api_key: SecretStr | None = None
    """OpenAI API key"""

    organization_id: str | None = None
    """OpenAI organization ID"""

    base_url: str | None = None
    """Custom base URL for OpenAI API"""

    def to_client_kwargs(self) -> dict[str, Any]:
        """
        Convert settings to OpenAI client initialization arguments.

        Returns:
            Dictionary of client initialization arguments with non-None values.

        Example:
            >>> settings = OpenAISettings(api_key="sk-test", organization_id="org-123")
            >>> client_kwargs = settings.to_client_kwargs()
            >>> client = AsyncClient(**client_kwargs)
        """
        client_kwargs: dict[str, Any] = {}

        if self.api_key:
            client_kwargs["api_key"] = self.api_key.get_secret_value()

        if self.organization_id:
            client_kwargs["organization"] = self.organization_id

        if self.base_url:
            client_kwargs["base_url"] = self.base_url

        return client_kwargs


settings_manager = SettingsManager(OpenAISettings, multi=True)
