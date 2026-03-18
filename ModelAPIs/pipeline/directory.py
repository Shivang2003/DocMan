import os
import numpy as np
from dotenv import load_dotenv
from pinecone import Pinecone


def cosine_score(vec1, vec2):
    v1 = np.array(vec1, dtype=float)
    v2 = np.array(vec2, dtype=float)

    denom = np.linalg.norm(v1) * np.linalg.norm(v2)
    if denom == 0:
        return 0.0

    return float(np.dot(v1, v2) / denom)


def clean_name(file_id):
    return file_id.replace(".txt", "").replace("/", "_")


def get_all_ids_from_index(index, main_file):
    """
    IMPORTANT:
    Pinecone does not provide a simple 'give me all ids' in fetch().
    So for now, this method gets ids by querying around the main_file.

    If you already store all ids somewhere else, replace this function.
    """
    main_fetch = index.fetch(ids=[main_file])

    if main_file not in main_fetch.vectors:
        raise ValueError(f"Main file '{main_file}' not found in index")

    main_vector = main_fetch.vectors[main_file].values

    # Get many nearby files
    results = index.query(
        vector=main_vector,
        top_k=1000,
        include_metadata=True
    )

    all_ids = []
    for match in results.matches:
        all_ids.append(match.id)

    # ensure main_file is present
    if main_file not in all_ids:
        all_ids.insert(0, main_file)

    return list(set(all_ids))


def fetch_all_vectors(index, file_ids):
    vectors = {}
    result = index.fetch(ids=file_ids)

    for fid in file_ids:
        if fid in result.vectors:
            vectors[fid] = result.vectors[fid].values

    return vectors


def get_score(fid1, fid2, vectors, sim_cache):
    key = tuple(sorted([fid1, fid2]))
    if key not in sim_cache:
        sim_cache[key] = cosine_score(vectors[fid1], vectors[fid2])
    return sim_cache[key]


def build_cluster(seed_id, candidate_ids, vectors, sim_cache, threshold):
    cluster = []

    for fid in candidate_ids:
        score = get_score(seed_id, fid, vectors, sim_cache)
        if score >= threshold:
            cluster.append(fid)

    return cluster


def find_best_subgroup(file_ids, vectors, sim_cache, sub_threshold):
    """
    Find a tighter subgroup inside a folder.
    """
    best_group = []
    best_avg = -1

    if len(file_ids) < 2:
        return []

    for seed in file_ids:
        current_group = []

        for fid in file_ids:
            score = get_score(seed, fid, vectors, sim_cache)
            if score >= sub_threshold:
                current_group.append(fid)

        if len(current_group) < 2:
            continue

        # average internal similarity
        pair_scores = []
        for i in range(len(current_group)):
            for j in range(i + 1, len(current_group)):
                pair_scores.append(
                    get_score(current_group[i], current_group[j], vectors, sim_cache)
                )

        avg_score = sum(pair_scores) / len(pair_scores) if pair_scores else 1.0

        if len(current_group) > len(best_group):
            best_group = current_group
            best_avg = avg_score
        elif len(current_group) == len(best_group) and avg_score > best_avg:
            best_group = current_group
            best_avg = avg_score

    return best_group


def pick_central_file(group, vectors, sim_cache):
    best_file = group[0]
    best_avg = -1

    for fid in group:
        scores = []
        for other in group:
            if fid != other:
                scores.append(get_score(fid, other, vectors, sim_cache))

        avg_score = sum(scores) / len(scores) if scores else 0

        if avg_score > best_avg:
            best_avg = avg_score
            best_file = fid

    return best_file


def build_subdirectories(parent_members, parent_path, vectors, sim_cache, paths, sub_threshold):
    """
    Create deeper folders only for tighter groups.
    """
    if len(parent_members) < 3:
        return

    subgroup = find_best_subgroup(parent_members, vectors, sim_cache, sub_threshold)

    # no meaningful tighter subgroup
    if len(subgroup) < 2 or len(subgroup) == len(parent_members):
        return

    subgroup_seed = pick_central_file(subgroup, vectors, sim_cache)
    sub_path = f"{parent_path}/{clean_name(subgroup_seed)}"

    print("Creating subdirectory:", sub_path)

    for fid in subgroup:
        paths[fid] = sub_path

    # recurse deeper
    build_subdirectories(
        parent_members=subgroup,
        parent_path=sub_path,
        vectors=vectors,
        sim_cache=sim_cache,
        paths=paths,
        sub_threshold=min(sub_threshold + 0.03, 0.95)
    )


def assign_directories(
    main_file="docker_docs_summary.txt",
    index_name="test-docs-dataset",
    root_dir="healthsos_core",
    threshold=0.78,
    sub_threshold=0.85
):
    load_dotenv()
    api_key = os.getenv("PINECONE_API_KEY")

    pc = Pinecone(api_key=api_key)
    index = pc.Index(index_name)

    # 1. get ids
    all_ids = get_all_ids_from_index(index, main_file)

    # 2. fetch vectors once
    vectors = fetch_all_vectors(index, all_ids)

    if main_file not in vectors:
        raise ValueError(f"Main file '{main_file}' vector not found")

    sim_cache = {}
    paths = {}
    processed = set()

    # score everything against main file
    main_scores = {}
    for fid in vectors:
        if fid != main_file:
            main_scores[fid] = get_score(main_file, fid, vectors, sim_cache)

    # -------------------------
    # first top-level directory
    # -------------------------
    first_cluster = build_cluster(
        seed_id=main_file,
        candidate_ids=list(vectors.keys()),
        vectors=vectors,
        sim_cache=sim_cache,
        threshold=threshold
    )

    first_path = f"{root_dir}/{clean_name(main_file)}"
    print("Creating directory:", first_path)

    for fid in first_cluster:
        paths[fid] = first_path

    build_subdirectories(
        parent_members=first_cluster,
        parent_path=first_path,
        vectors=vectors,
        sim_cache=sim_cache,
        paths=paths,
        sub_threshold=sub_threshold
    )

    processed.update(first_cluster)

    # -------------------------
    # remaining top-level dirs
    # -------------------------
    while True:
        remaining = [fid for fid in vectors.keys() if fid not in processed]
        if not remaining:
            break

        # choose remaining file having max similarity with main_file
        remaining.sort(key=lambda x: main_scores.get(x, -1), reverse=True)
        next_seed = remaining[0]

        next_cluster = build_cluster(
            seed_id=next_seed,
            candidate_ids=remaining,
            vectors=vectors,
            sim_cache=sim_cache,
            threshold=threshold
        )

        next_path = f"{root_dir}/{clean_name(next_seed)}"
        print("Creating directory:", next_path)

        for fid in next_cluster:
            paths[fid] = next_path

        build_subdirectories(
            parent_members=next_cluster,
            parent_path=next_path,
            vectors=vectors,
            sim_cache=sim_cache,
            paths=paths,
            sub_threshold=sub_threshold
        )

        processed.update(next_cluster)

    # -------------------------
    # update metadata in index
    # -------------------------
    for fid, path in paths.items():
        index.update(
            id=fid,
            set_metadata={"directory": path}
        )

    return {
        "status": "success",
        "processed_files": len(paths),
        "directories_assigned": paths
    }