# directory.py
import os
from dotenv import load_dotenv
from pinecone import Pinecone
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def assign_directories(
    main_file="docker_docs_summary.txt",
    index_name="test-docs-dataset",
    root_dir="healthsos_core",
    threshold=0.78,
    sub_threshold=0.85
):
    load_dotenv()
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

    # Connect to Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(index_name)

    # Fetch main vector
    main_fetch = index.fetch(ids=[main_file])
    main_vector = main_fetch.vectors[main_file].values

    main_name = main_file.replace(".txt", "")
    main_directory = f"{root_dir}/{main_name}"

    # Initial cluster
    results = index.query(vector=main_vector, top_k=100, include_metadata=True)
    cluster, remaining = [], []

    for match in results.matches:
        if match.score >= threshold:
            cluster.append(match.id)
        else:
            remaining.append(match.id)

    print("Creating directory:", main_directory)
    for file_id in cluster:
        index.update(id=file_id, set_metadata={"directory": main_directory})

    processed = set(cluster)

    # Subcluster function
    def create_subclusters(file_ids, parent_dir):
        if len(file_ids) <= 2:
            return
        vectors, ids = [], []
        for fid in file_ids:
            res = index.fetch(ids=[fid])
            vec = res.vectors[fid].values
            vectors.append(vec)
            ids.append(fid)
        vectors = np.array(vectors)
        sim_matrix = cosine_similarity(vectors)
        avg_scores = sim_matrix.mean(axis=1)
        seed_index = np.argmax(avg_scores)
        seed_file = ids[seed_index]
        seed_vector = vectors[seed_index]
        subcluster = []
        for i, fid in enumerate(ids):
            score = cosine_similarity([seed_vector], [vectors[i]])[0][0]
            if score >= sub_threshold:
                subcluster.append(fid)
        if len(subcluster) == len(ids):
            return
        sub_dir = seed_file.replace(".txt", "")
        sub_path = f"{parent_dir}/{sub_dir}"
        print("Creating subdirectory:", sub_path)
        for fid in subcluster:
            index.update(id=fid, set_metadata={"directory": sub_path})

    # Create subclusters
    create_subclusters(cluster, main_directory)

    # Process remaining files
    while remaining:
        seed = remaining.pop(0)
        if seed in processed:
            continue
        seed_fetch = index.fetch(ids=[seed])
        seed_vector = seed_fetch.vectors[seed].values
        seed_name = seed.replace(".txt", "")
        directory_name = f"{root_dir}/{seed_name}"
        results = index.query(vector=seed_vector, top_k=100, include_metadata=True)
        cluster = []
        for match in results.matches:
            if match.id in processed:
                continue
            if match.score >= threshold:
                cluster.append(match.id)
        print("\nCreating directory:", directory_name)
        for file_id in cluster:
            index.update(id=file_id, set_metadata={"directory": directory_name})
            processed.add(file_id)
        create_subclusters(cluster, directory_name)

    return {"status": "success", "processed_files": len(processed)}