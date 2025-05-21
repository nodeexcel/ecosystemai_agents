import os, uuid
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from concurrent.futures import ThreadPoolExecutor


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

def load_and_split_pdf(pdf_path):
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    return splitter.split_documents(documents)

def embed_batch(texts):
    return embeddings_model.embed_documents(texts)

def threaded_embedding(documents, batch_size=20, max_workers=5):
    batches = [documents[i:i+batch_size] for i in range(0, len(documents), batch_size)]

    embeddings = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(embed_batch, [doc.page_content for doc in batch]) for batch in batches]
        for future in futures:
            embeddings.extend(future.result())

    return embeddings

def upsert_to_pinecone_for_pdf(user_id, documents, embeddings):
    
    index = pinecone_db.Index(name=os.getenv('PINECONEDB'))
    user_id = user_id
    id = uuid.uuid4()
    
    vectors = [
        {
            "id": str(id),
            "values": embeddings[i],
            "metadata": {"text": documents[i].page_content}
        }
        for i in range(len(documents))
    ]
    index.upsert(namespace = str(user_id), vectors=vectors)
    
def process_large_pdf_to_pinecone(pdf_path, user_id):
    documents = load_and_split_pdf(pdf_path)
    embeddings = threaded_embedding(documents, batch_size=20, max_workers=5)
    upsert_to_pinecone_for_pdf(user_id, documents, embeddings)