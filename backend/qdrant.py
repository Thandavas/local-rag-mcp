from qdrant_client import QdrantClient
from qdrant_client.http import models

model_name = "sentence-transformers/all-MiniLM-L6-v2"

client = QdrantClient(path="data/qdrant_data")

def create_collection(collection_name='mylocal'):
    rs = client.get_collections()
    existing = [c.name for c in rs.collections]
    if collection_name not in existing:
        client.create_collection(
        collection_name,
        vectors_config=models.VectorParams(
            size=client.get_embedding_size(model_name), distance=models.Distance.COSINE)
        )

def insert_collection(ids,payload,vectors,collection_name='mylocal'):
    client.upload_collection(
        collection_name,
        vectors=vectors,
        payload=payload,
        ids=ids
    )

def search_collection(query_vector, collection_name='mylocal', limit=4):
    rs = client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=limit
        )
    return {"results": [point.payload["text"] for point in rs.points]}