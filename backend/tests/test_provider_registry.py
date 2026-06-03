from app.ai.providers.registry import ProviderRegistry
from app.schemas.provider import ProviderName


def test_provider_registry_exposes_required_providers():
    descriptors = ProviderRegistry().descriptors()
    names = {descriptor.name for descriptor in descriptors}

    assert names == {
        ProviderName.gemini,
        ProviderName.anthropic,
        ProviderName.openrouter,
        ProviderName.ollama,
    }
