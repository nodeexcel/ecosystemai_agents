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

router = APIRouter(tags=['knowledge_base'])

embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")

@router.post('/knowledge-base')
def embeddings_for_snippets(payload: Snippet, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    if payload.data_type == 'snippet':
        snippet = payload.data

        embedded_query = embeddings_model.embed_query(snippet)
        user_id = user.id
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
        
        knowledge_base = KnowledgeBase(**payload.model_dump(), user_id=user_id)
        db.add(knowledge_base)
        db.commit()
        db.refresh(knowledge_base)
    
    return JSONResponse({"success": "Your data is stored in BrainAI knowlwage base"}, status_code=200)

@router.get('/snippets')
def get_snippets(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    snippets = db.query(KnowledgeBase).filter_by(data_type='snippet').all()
    info = []
    data = {}
    for snippet in snippets:
        data['text'] = snippet.data
        info.append(data)
    return JSONResponse({"snippets": info},status_code=200)
        
        
        
        
    
        




