import faiss
import numpy as np


def create_vector_store(vectors):
    dimension = len(vectors[0])

    index = faiss.IndexFlatL2(dimension)

    vectors_array = np.array(vectors).astype("float32")

    index.add(vectors_array)

    return index