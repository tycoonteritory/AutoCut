"""
Centralized OpenAI client for all AI services
"""
import logging
from openai import OpenAI
from backend.config import settings

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Centralized OpenAI client"""

    def __init__(self):
        """Initialize OpenAI client with API key from settings"""
        if not settings.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY not configured. "
                "Please create a .env file with your OpenAI API key. "
                "See .env.example for details."
            )

        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        logger.info("OpenAI client initialized")

    def create_chat_completion(self, messages, model=None, temperature=0.7, max_tokens=None):
        """
        Create a chat completion using GPT

        Args:
            messages: List of message dictionaries
            model: Model to use (default: from settings)
            temperature: Creativity level (0-1)
            max_tokens: Maximum tokens in response

        Returns:
            Response text
        """
        model = model or settings.GPT_MODEL

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error creating chat completion: {e}", exc_info=True)
            raise


# Global instance
_openai_client = None


def get_openai_client() -> OpenAIClient:
    """Get or create OpenAI client singleton"""
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAIClient()
    return _openai_client
