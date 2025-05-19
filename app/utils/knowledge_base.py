import os, uuid
from langchain_openai import ChatOpenAI
from app.ai_agents.prompts import Prompts

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

def knowledge_base_embedding_and_storage(embeddings_model, user_id, pinecone_db, data):
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
                "metadata": {}, 
            },
        ]
    )