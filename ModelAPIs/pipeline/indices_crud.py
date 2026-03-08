import os
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "project-indices-details"

pc = Pinecone(api_key=PINECONE_API_KEY)

def createVectorInIndex(id, stored_ids, description, directories=None, embed_model="all-MiniLM-L6-v2"):
    model = SentenceTransformer(embed_model)
    vector_values = model.encode(description).tolist()  # convert text to embedding

    metadata = {
        "stored_ids": stored_ids,
        "directories": directories if directories else []
    }

    pc.Index(INDEX_NAME).upsert(
        vectors=[{
            "id": id,
            "values": vector_values,
            "metadata": metadata
        }]
    )


def updateVectorInIndex(id, field_updated, new_value):
    index = pc.Index(INDEX_NAME)

    # Fetch the vector
    result = index.fetch(ids=[id])

    if id not in result.vectors:
        print(f"Vector with id '{id}' not found.")
        return

    vector_obj = result.vectors[id]

    # Access metadata safely
    metadata = vector_obj.metadata or {}

    # Update metadata
    if field_updated in metadata and isinstance(metadata[field_updated], list):
        if isinstance(new_value, list):
            metadata[field_updated].extend(new_value)
        else:
            metadata[field_updated].append(new_value)
    else:
        metadata[field_updated] = new_value

    # Upsert the vector with the same values but updated metadata
    index.upsert(
        vectors=[{
            "id": id,
            "values": vector_obj.values,
            "metadata": metadata
        }]
    )

def getVectorInIndex(id):
    index = pc.Index(INDEX_NAME)
    result = index.fetch(ids=[id])
    return id in result.vectors

def deleteIndex():
    pass