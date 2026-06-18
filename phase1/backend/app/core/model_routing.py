PROVIDER_PREFIX = {
    "openai": "openai",
    "anthropic": "anthropic",
    "google_gemini": "gemini",
    "openrouter": "openrouter",
    "custom": "openai",  # assume OpenAI-compatible unless told otherwise
}


def build_litellm_overrides(connector, model_name: str, api_key: str) -> dict:
    prefix = PROVIDER_PREFIX.get(connector.provider, "openai")
    return {
        "model": f"{prefix}/{model_name}",
        "api_key": api_key,
        "api_base": connector.base_url,
    }
