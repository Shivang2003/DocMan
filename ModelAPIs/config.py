from pinecone import Pinecone

PINECONE_API_KEY = "pcsk_2NbMLj_e6iu4DuwhT12PehxftHTVRbG3gfDGygSbti9WQcP98XiNtgaxGcEbwKFtUUtHx"

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index("healthsos")