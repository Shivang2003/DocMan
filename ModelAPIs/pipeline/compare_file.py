from pinecone import Pinecone

# =========================
# CONFIG
# =========================

PINECONE_API_KEY = "pcsk_2NbMLj_e6iu4DuwhT12PehxftHTVRbG3gfDGygSbti9WQcP98XiNtgaxGcEbwKFtUUtHx"
INDEX_NAME = "test-index"
FILE_ID = "healthsos_overview.txt"

# =========================
# CONNECT
# =========================

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

# =========================
# FETCH VECTOR
# =========================
response = index.fetch(ids=[FILE_ID])
print(response)

if FILE_ID not in response.vectors:
    print("File not found in Pinecone index")
    exit()

file_vector = response.vectors[FILE_ID].values

# =========================
# QUERY SIMILAR FILES
# =========================

results = index.query(
    vector=file_vector,
    top_k=10,
    include_metadata=True
)

# =========================
# PRINT RESULTS
# =========================

print(f"\nSimilarity results for: {FILE_ID}\n")

for match in results.matches:

    if match.id == FILE_ID:
        continue

    print("File:", match.id)
    print("Score:", match.score)
    print("-" * 40)