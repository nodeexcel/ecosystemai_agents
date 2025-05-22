import os
from pinecone import Pinecone, ServerlessSpec

pinecone_db = Pinecone(api_key=os.getenv('PINECONE_KEY'))

index_name = os.getenv('PINECONEDB')
if not pinecone_db.has_index(index_name):
    pinecone_db.create_index(
        name=index_name,
        dimension=1536,
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
    ))