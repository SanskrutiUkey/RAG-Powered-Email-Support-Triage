
embedding = client.embeddings.create(
    model="gemini-embedding-001",
    input=content,
    dimensions=768
)

vector = embedding.data[0].embedding