import numpy as np


def retrieve_chunks(query, embedding_model, index, chunks, k=3):
    # Convert the user's question into an embedding
    query_vector = embedding_model.embed_query(query)

    # Convert to NumPy array
    query_vector = np.array([query_vector]).astype("float32")

    # Search FAISS for the k closest vectors
    distances, indices = index.search(query_vector, k)

    # Get the corresponding chunks
    relevant_chunks = []

    for i in indices[0]:
        if i != -1:
            relevant_chunks.append(chunks[i])

    return relevant_chunks