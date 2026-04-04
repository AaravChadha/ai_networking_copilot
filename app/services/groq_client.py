import json
import time

from groq import Groq, RateLimitError

from app.config import settings

client = Groq(api_key=settings.GROQ_API_KEY)


def chat(system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
    """Send a chat request and return the text response."""
    for attempt in range(settings.GROQ_MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
            )
            return response.choices[0].message.content
        except RateLimitError:
            if attempt < settings.GROQ_MAX_RETRIES - 1:
                wait = settings.GROQ_RATE_LIMIT_DELAY * (2 ** attempt)
                time.sleep(wait)
            else:
                raise


def chat_json(system_prompt: str, user_prompt: str, temperature: float = 0.3) -> dict | list:
    """Send a chat request with JSON mode and return parsed JSON."""
    for attempt in range(settings.GROQ_MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                response_format={"type": "json_object"},
            )
            return json.loads(response.choices[0].message.content)
        except RateLimitError:
            if attempt < settings.GROQ_MAX_RETRIES - 1:
                wait = settings.GROQ_RATE_LIMIT_DELAY * (2 ** attempt)
                time.sleep(wait)
            else:
                raise
