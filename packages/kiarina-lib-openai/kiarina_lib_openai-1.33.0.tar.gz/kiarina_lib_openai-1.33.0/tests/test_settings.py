from pydantic import SecretStr

from kiarina.lib.openai import OpenAISettings


def test_api_key():
    settings = OpenAISettings.model_validate({"api_key": "sk-test-key-123"})
    assert settings.api_key is not None
    assert settings.api_key.get_secret_value() == "sk-test-key-123"


def test_to_client_kwargs():
    settings = OpenAISettings(
        api_key=SecretStr("sk-test-key"),
        organization_id="org-123",
        base_url="https://api.example.com/v1",
    )

    client_kwargs = settings.to_client_kwargs()

    assert client_kwargs == {
        "api_key": "sk-test-key",
        "organization": "org-123",
        "base_url": "https://api.example.com/v1",
    }
