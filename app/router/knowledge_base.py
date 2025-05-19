import os, uuid
from fastapi import Depends
from fastapi.routing import APIRouter
from fastapi.responses import JSONResponse 

from langchain_openai import OpenAIEmbeddings

from sqlalchemy.orm import Session

from app.schemas.knowledge_base import Snippet
from app.models.get_db import get_db
from app.models.model import User, KnowledgeBase
from app.utils.user_auth import get_current_user
from app.services.pinecone import pinecone_db
from app.utils.knowledge_base import website_scrape, knowledge_base_embedding_and_storage

router = APIRouter(tags=['knowledge_base'])

embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")

@router.post('/knowledge-base')
def embeddings_for_snippets(payload: Snippet, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    if payload.data_type == 'snippet':
        snippet = payload.data
        user_id = user.id
        knowledge_base_embedding_and_storage(embeddings_model, user_id, pinecone_db, snippet)
        knowledge_base = KnowledgeBase(data_type='snippet', data=snippet, user_id=user_id)
        db.add(knowledge_base)
        db.commit()

    if payload.data_type=='website':
        website_data = website_scrape(payload.data)
        user_id = user.id
        knowledge_base_embedding_and_storage(embeddings_model, user_id, pinecone_db, website_data)
        knowledge_base = KnowledgeBase(**payload.model_dump(), user_id=user_id)
        db.add(knowledge_base)
        db.commit()
    return JSONResponse({"success": "Your data is stored in BrainAI knowlwage base"}, status_code=200)

@router.get('/snippets')
def get_snippets(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    snippets = db.query(KnowledgeBase).filter_by(data_type='snippet').all()
    info = []
    for snippet in snippets:
        info.append(snippet.data)
    websites = db.query(KnowledgeBase).filter_by(data_type='website').all()
    website_urls = []
    for website in websites:
        website_urls.append(website.data)
    return JSONResponse({"snippets": info, "website": website_urls},status_code=200)



        
        
        
        
    
        




