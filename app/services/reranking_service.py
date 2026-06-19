from sentence_transformers import CrossEncoder

model = CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L-6-v2"
)

# Given a query and a list of documents, score each document, sort by relevance, and return the top K most relevant documents.
def rerank_docs(query, docs, top_k=3):

    pairs = []
    for doc in docs:
        pairs.append([query, doc])

    scores = model.predict(pairs)

    ranked = []
    for i in range(len(docs)):
        ranked.append((docs[i], scores[i]))

    ranked.sort(key=lambda item: item[1], reverse=True)

    top_docs = []
    for doc, score in ranked[:top_k]:
        top_docs.append(doc)

    return top_docs