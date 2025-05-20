import os, uuid
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings

from app.ai_agents.prompts import Prompts
from app.services.pinecone import pinecone_db

llm = ChatOpenAI(
    model="gpt-4o",
    api_key=os.getenv("API_KEY"),
)

def website_scrape(website_link):
    prompt = Prompts.website_info_prompt()
    messages = [
    (
        "system", prompt
    ),
    ("human", website_link),
]
    data = llm.invoke(messages)
    return data.content

embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")

def knowledge_base_embedding_and_storage(user_id, data):
    embedded_query = embeddings_model.embed_query(data)
    user_id = user_id
    id = uuid.uuid4()
    
    index = pinecone_db.Index(name=os.getenv('PINECONEDB'))

    index.upsert(
        namespace = str(user_id),
        vectors=[
            {
                "id": str(id),
                "values": embedded_query,
                "metadata": {"chunk_text": data}, 
            },
        ]
    )
    
def fetch_text(message, user_id):
        index = pinecone_db.Index(name=os.getenv('PINECONEDB'))
        
        embedded_query = embeddings_model.embed_query(message)

        results = index.query(
            namespace=str(user_id), 
            vector = embedded_query, 
            top_k = 1,
            include_metadata=True
            )

        data = results["matches"]
        try:
            metadata = data[1]
            knowledge_base = metadata.get('chunk_text')
            return knowledge_base
        except:
            return ""