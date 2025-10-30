import os, uuid
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor

from fastapi import UploadFile, status
from fastapi.exceptions import HTTPException
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from PyPDF2 import PdfReader

from app.prompts.knowledge_base import website_info_prompt
from app.services.pinecone import pinecone_db
from app.utils.knowledge_base import embeddings_model


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
            top_k = 5,
            include_metadata=True
            )

        matches = results["matches"]

        knowledge_base = ""
        try:
            for match in matches:
                metadata = match['metadata']
                text = metadata.get('text')
                if not None:
                    knowledge_base = knowledge_base + text
            return knowledge_base
        except Exception as e:
            return knowledge_base
        
        
def load_pdf_from_upload(attachment: UploadFile):
    pdf_bytes = attachment.file.read()
    temp_stream = BytesIO(pdf_bytes)

    reader = PdfReader(temp_stream)
    docs = []
    
    if len(reader.pages) > 10:
        raise HTTPException("Upload file max page support to 10 pages.")
    
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        docs.append(Document(
            page_content=text,
            metadata={"page": i + 1, "filename": attachment.filename}
        ))
    return docs


def load_and_split_pdf(attachment: UploadFile):
    # loader = PyPDFLoader(pdf_path)
    documents = load_pdf_from_upload(attachment)
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
            
    if not embeddings:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Upload valid pdf.")

    return embeddings


def upsert_to_pinecone_for_pdf(user_id, documents, embeddings, metadata: dict[str, str]):
    
    index = pinecone_db.Index(name=os.getenv('PINECONEDB'))
    user_id = user_id
    
    # metadata.update({"text": documents[i].page_content})
    
    # vectors = [
    #     {
    #         "id": str(uuid.uuid4()),
    #         "values": embeddings[i],
    #         "metadata": {"text": documents[i].page_content}
    #     }
    #     for i in range(len(documents))
    # ]
    
    vectors = []
    for i in range(len(documents)):
        print("Preparing metadata...")
        metadata.update({"text": documents[i].page_content})
        _v = {
            "id": str(uuid.uuid4()),
            "values": embeddings[i],
            "metadata": metadata
        }
        vectors.append(_v)
        
    index.upsert(namespace = str(user_id), vectors=vectors)
    
    
def process_attachment_to_pinecone(attachment: UploadFile, user_id, metadata: dict[str, str]):
    documents = load_and_split_pdf(attachment)
    embeddings = threaded_embedding(documents, batch_size=20, max_workers=5)
    upsert_to_pinecone_for_pdf(user_id, documents, embeddings, metadata)
    
    return documents