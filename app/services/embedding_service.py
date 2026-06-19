
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

def create_embedding(client, content):
    """Create and return an embedding vector for the given content.

    Always converts content to `str` to avoid client errors when `None` or
    non-string types are passed.
    """
    text = str(content or "")
    resp = client.embeddings.create(
        model="gemini-embedding-001",
        input=text,
        dimensions=768
    )
    return resp.data[0].embedding