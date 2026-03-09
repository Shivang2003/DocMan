# app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from pipeline.directory import assign_directories
from pipeline.fetch_metadata import fetch_unique_directories
from pipeline.ingest import ingest_documents_from_github

app = FastAPI(title="Document Management API")

# =========================
# Request models
# =========================
# class IngestRequest(BaseModel):
#     index_name: str
#     data_folder: str
#     embed_model: str = None  # optional, only if needed downstream

class DirectoryRequest(BaseModel):
    main_file: str
    index_name: str = "test-docs-dataset"
    root_dir: str = "healthsos_core"
    threshold: float = 0.78
    sub_threshold: float = 0.85

class DirectoryMetadataRequest(BaseModel):
    index_name: str = Field(..., description="Name of the Pinecone index (required)")

class GitHubIngestRequest(BaseModel):
    username: str = Field(..., example="your-github-username")
    repo: str = Field(..., example="DocMan")
    branch: str = Field(default="main", example="main")
    projectname: str = Field(..., example="healthsos")
    index_name: str = Field(default="test-docs-dataset", example="test-docs-dataset")
    embed_model: str = Field(default="all-MiniLM-L6-v2", example="all-MiniLM-L6-v2")

# =========================
# Ingest API
# =========================
# @app.post("/ingest/")
# async def api_ingest(payload: IngestRequest):
#     """
#     Trigger ingestion of documents into Pinecone using ingest.py
#     """
#     # Call ingest_documents from pipeline.ingest
#     # If your ingest_documents supports main_file, you can pass payload.main_file
#     result = ingest_documents(
#         data_folder=payload.data_folder,
#         index_name=payload.index_name,
#         embed_model=payload.embed_model  # optional
#     )
#     return result

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
# Get docs from github for ingest api
# =========================

@app.post("/ingest/github")
def ingest_github(request: GitHubIngestRequest):
    try:
        result = ingest_documents_from_github(
            username=request.username,
            repo=request.repo,
            branch=request.branch,
            projectname=request.projectname,
            index_name=request.index_name,
            embed_model=request.embed_model
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =========================
# Root endpoint
# =========================
@app.get("/")
async def root():
    return {"message": "Document Management API Running"}