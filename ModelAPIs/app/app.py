# app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from pipeline.ingest import ingest_documents
from pipeline.directory import assign_directories
from pipeline.fetch_metadata import fetch_unique_directories

app = FastAPI(title="Document Management API")

# =========================
# Request models
# =========================
class IngestRequest(BaseModel):
    index_name: str
    data_folder: str
    embed_model: str = None  # optional, only if needed downstream

class DirectoryRequest(BaseModel):
    main_file: str
    index_name: str = "test-docs-dataset"
    root_dir: str = "healthsos_core"
    threshold: float = 0.78
    sub_threshold: float = 0.85

class DirectoryMetadataRequest(BaseModel):
    index_name: str = Field(..., description="Name of the Pinecone index (required)")

# =========================
# Ingest API
# =========================
@app.post("/ingest/")
async def api_ingest(payload: IngestRequest):
    """
    Trigger ingestion of documents into Pinecone using ingest.py
    """
    # Call ingest_documents from pipeline.ingest
    # If your ingest_documents supports main_file, you can pass payload.main_file
    result = ingest_documents(
        data_folder=payload.data_folder,
        index_name=payload.index_name,
        embed_model=payload.embed_model  # optional
    )
    return result

# =========================
# Directory API
# =========================
@app.post("/directory/")
async def api_directory(payload: DirectoryRequest):
    """
    Trigger clustering and directory assignment using directory.py
    """
    result = assign_directories(
        main_file=payload.main_file,
        index_name=payload.index_name,
        root_dir=payload.root_dir,
        threshold=payload.threshold,
        sub_threshold=payload.sub_threshold
    )
    return result

class DirectoryMetadataRequest(BaseModel):
    index_name: str

# =========================
# Directory Metadata API
# =========================
@app.post("/directories/")
async def api_directories(payload: DirectoryMetadataRequest):
    if not payload.index_name:
        raise HTTPException(status_code=400, detail="index_name is required")

    directories = fetch_unique_directories(index_name=payload.index_name)
    return {"unique_directories": list(directories)}

# =========================
# Root endpoint
# =========================
@app.get("/")
async def root():
    return {"message": "Document Management API Running"}