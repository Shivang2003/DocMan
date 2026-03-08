import os
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
from pipeline.indices_crud import createVectorInIndex, updateVectorInIndex, getVectorInIndex
from dotenv import load_dotenv

def ingest_documents(data_folder=None, index_name="test-docs-dataset", embed_model="all-MiniLM-L6-v2"):
   
    # CONFIG
    load_dotenv()
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

    # respect arguments passed by the caller; fall back to sensible defaults
    INDEX_NAME = index_name or "test-docs-dataset"

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # if user gave a relative path, interpret it from project root

    if data_folder:
        DATA_FOLDER = os.path.abspath(os.path.join(BASE_DIR, data_folder))
    else:
        DATA_FOLDER = os.path.join(BASE_DIR, "data", "raw", "docs_dataset")
    EMBED_MODEL = embed_model or "all-MiniLM-L6-v2"

    # INIT PINECONE

    pc = Pinecone(api_key=PINECONE_API_KEY)

    # create index if not exists
    existing_indexes = [i.name for i in pc.list_indexes()]

    if INDEX_NAME not in existing_indexes:
        pc.create_index(
            name=INDEX_NAME,
            dimension=384,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )

    index = pc.Index(INDEX_NAME)

    # LOAD EMBEDDING MODEL

    model = SentenceTransformer(EMBED_MODEL)

    # READ DATASET

    documents = []
    ids = []

    for file in os.listdir(DATA_FOLDER):
        if file.endswith(".txt"):
            path = os.path.join(DATA_FOLDER, file)

            with open(path, "r", encoding="utf-8") as f:
                text = f.read()

            documents.append(text)
            ids.append(file)

    print(f"Loaded {len(documents)} documents")

    # CREATE EMBEDDINGS

    embeddings = model.encode(documents)

    # PREPARE VECTORS

    vectors = []

    if not getVectorInIndex(INDEX_NAME):
        createVectorInIndex(id=INDEX_NAME, stored_ids=[], description="Index for document embeddings", directories=["None"], embed_model=EMBED_MODEL)
        

    for i in range(len(documents)):
        vectors.append({
            "id": ids[i],
            "values": embeddings[i].tolist(),
            "metadata": {
                "fileName": ids[i],
                "directory": "None"
            }
        })
        updateVectorInIndex(id=INDEX_NAME, field_updated="stored_ids", new_value=ids[i])

    # UPSERT INTO PINECONE

    index.upsert(vectors=vectors)

    print("Data inserted into Pinecone successfully")

    return {"status": "success", "inserted_docs": len(documents), "index_name": INDEX_NAME}