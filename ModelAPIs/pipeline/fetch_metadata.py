import os
from pinecone import Pinecone
from dotenv import load_dotenv

def fetch_unique_directories(index_name="test-docs-dataset", batch_size=100):
    """
    Fetch all unique 'directory' values from a Pinecone index.
    
    Returns a set of directory paths.
    """
    load_dotenv()
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

    # Initialize Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(index_name)

    # Get vector count
    stats = index.describe_index_stats()
    vector_count = stats['namespaces'].get('', {}).get('vector_count', 0)
    if vector_count == 0:
        return set()

    directory_set = set()
    offset = 0

    while True:
        # Query all vectors in batches without filter
        res = index.query(
            top_k=batch_size,
            include_metadata=True,
            include_values=False,
            filter={},
            offset=offset
        )

        matches = res.matches
        if not matches:
            break

        for match in matches:
            directory = match.metadata.get("directory") if match.metadata else None
            if directory:
                directory_set.add(directory)

        offset += batch_size

    return directory_set