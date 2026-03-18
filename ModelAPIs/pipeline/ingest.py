import os
import requests
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

from pipeline.indices_crud import (
    createVectorInIndex,
    updateVectorInIndex,
    getVectorInIndex
)


def _get_github_headers():
    headers = {
        "Accept": "application/vnd.github+json"
    }

    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    return headers


def _list_github_folder_contents(username: str, repo: str, branch: str, folder_path: str):
    """
    Uses GitHub Contents API to list files in a folder.
    Example folder_path: docs/raw/healthsos
    """
    url = f"https://api.github.com/repos/{username}/{repo}/contents/{folder_path}"
    params = {"ref": branch}

    response = requests.get(url, headers=_get_github_headers(), params=params, timeout=30)

    if response.status_code != 200:
        raise Exception(
            f"GitHub API error while listing folder. "
            f"Status: {response.status_code}, Response: {response.text}"
        )

    data = response.json()

    if not isinstance(data, list):
        raise Exception(f"Expected folder listing, got: {data}")

    return data


def _download_text_file(download_url: str):
    response = requests.get(download_url, timeout=30)

    if response.status_code != 200:
        raise Exception(
            f"Failed to download file. Status: {response.status_code}, URL: {download_url}"
        )

    return response.text


def ingest_documents_from_github(
    username: str,
    repo: str,
    projectname: str,
    branch: str = "main",
    index_name: str = "test-docs-dataset",
    embed_model: str = "all-MiniLM-L6-v2"
):
    load_dotenv()

    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    if not pinecone_api_key:
        raise Exception("PINECONE_API_KEY not found in environment.")

    folder_path = f"docs/raw/{projectname}"

    # -----------------------------
    # INIT PINECONE
    # -----------------------------
    pc = Pinecone(api_key=pinecone_api_key)

    existing_indexes = [idx.name for idx in pc.list_indexes()]
    if index_name not in existing_indexes:
        pc.create_index(
            name=index_name,
            dimension=384,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )

    index = pc.Index(index_name)

    # -----------------------------
    # LOAD EMBEDDING MODEL
    # -----------------------------
    model = SentenceTransformer(embed_model)

    # -----------------------------
    # FETCH FILES FROM GITHUB
    # -----------------------------
    folder_items = _list_github_folder_contents(
        username=username,
        repo=repo,
        branch=branch,
        folder_path=folder_path
    )

    documents = []
    ids = []

    for item in folder_items:
        if item.get("type") == "file" and item.get("name", "").endswith(".txt"):
            file_name = item["name"]
            download_url = item.get("download_url")

            if not download_url:
                continue

            text = _download_text_file(download_url)

            if text and text.strip():
                documents.append(text)
                ids.append(f"{projectname}__{file_name}")

    if not documents:
        raise Exception(f"No .txt documents found in GitHub folder: {folder_path}")

    print(f"Loaded {len(documents)} documents from GitHub")

    # -----------------------------
    # CREATE EMBEDDINGS
    # -----------------------------
    embeddings = model.encode(documents)

    # -----------------------------
    # CREATE METADATA VECTOR IF NEEDED
    # -----------------------------
    meta_id = index_name

    if not getVectorInIndex(meta_id):
        createVectorInIndex(
            id=meta_id,
            stored_ids=[],
            description=f"Index for document embeddings from GitHub folder {folder_path}",
            directories=["None"],
            embed_model=embed_model
        )

    # -----------------------------
    # PREPARE VECTORS
    # -----------------------------
    vectors = []
    for i in range(len(documents)):
        vectors.append({
            "id": ids[i],
            "values": embeddings[i].tolist(),
            "metadata": {
                "fileName": ids[i],
                "directory": "None",
                "source": "github",
                "repo": repo,
                "owner": username,
                "branch": branch,
                "projectname": projectname,
                "folder_path": folder_path
            }
        })

    # -----------------------------
    # UPSERT INTO PINECONE
    # -----------------------------
    index.upsert(vectors=vectors)

    # -----------------------------
    # UPDATE INDEX METADATA ONCE
    # -----------------------------
    updateVectorInIndex(
        id=meta_id,
        field_updated="stored_ids",
        new_value=ids
    )

    print("Data inserted into Pinecone successfully")

    return {
        "status": "success",
        "inserted_docs": len(documents),
        "index_name": index_name,
        "source": "github",
        "repo": repo,
        "branch": branch,
        "folder_path": folder_path,
        "stored_ids": ids
    }