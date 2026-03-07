from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

# =====================
# CONFIG
# =====================

PINECONE_API_KEY = "pcsk_2NbMLj_e6iu4DuwhT12PehxftHTVRbG3gfDGygSbti9WQcP98XiNtgaxGcEbwKFtUUtHx"
INDEX_NAME = "test-index"

# =====================
# INIT
# =====================

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

model = SentenceTransformer("all-MiniLM-L6-v2")

# =====================
# USER QUERY
# =====================

query = "can I notification of nearby hospitals in HealthSOS?"

# convert query to embedding
query_vector = model.encode(query).tolist()

# =====================
# SEARCH
# =====================

results = index.query(
    vector=query_vector,
    top_k=3,
    include_metadata=True
)

# =====================
# PRINT RESULTS
# =====================

for match in results["matches"]:
    print("\nScore:", match["score"])
    print("Text:", match["metadata"]["text"])