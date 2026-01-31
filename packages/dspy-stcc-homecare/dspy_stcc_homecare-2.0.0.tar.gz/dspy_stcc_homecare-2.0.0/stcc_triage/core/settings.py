"""
DeepSeek Configuration Settings.

Environment-based configuration for DeepSeek API with python-dotenv.
"""

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()


class DeepSeekConfig(BaseSettings):
    """DeepSeek API configuration from environment variables."""

    api_key: str = Field(..., alias="DEEPSEEK_API_KEY")
    base_url: str = Field(
        default="https://api.deepseek.com/v1", alias="DEEPSEEK_BASE_URL"
    )
    model: str = Field(default="deepseek-chat", alias="DEEPSEEK_MODEL")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields from .env


def get_deepseek_config():
    """
    Get configured DeepSeek LM for DSPy.

    Returns:
        Configured DSPy OpenAI-compatible model instance
    """
    try:
        import dspy
    except ImportError:
        raise ImportError(
            "dspy-ai package not installed. Run: uv add dspy-ai"
        )

    config = DeepSeekConfig()

    # Configure DeepSeek as OpenAI-compatible endpoint
    lm = dspy.LM(
        model=f"openai/{config.model}",
        api_key=config.api_key,
        api_base=config.base_url,
    )

    # Return a simple object with both the LM and config
    class ConfiguredLM:
        def __init__(self, lm, config):
            self.lm = lm
            self.config = config

    return ConfiguredLM(lm, config)
