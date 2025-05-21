import os, uuid
from fastapi import Depends, UploadFile, Form, File
from fastapi.routing import APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse 

from sqlalchemy.orm import Session

from app.models.get_db import get_db
from app.models.model import User, KnowledgeBase
from app.utils.user_auth import get_current_user
from app.utils.knowledge_base import website_scrape, knowledge_base_embedding_and_storage, process_large_pdf_to_pinecone

router = APIRouter(tags=['knowledge_base'])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

router.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
    
@router.post('/knowledge-base')
def embeddings_for_snippets(data: str = Form(...),
                            data_type: str = Form(...),
                            file: UploadFile = File(...),
                            db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    if data_type == 'snippet':
        snippet = data
        user_id = user.id
        knowledge_base_embedding_and_storage(user_id, snippet)
        knowledge_base = KnowledgeBase(data_type='snippet', data=snippet, user_id=user_id)
        db.add(knowledge_base)
        db.commit()

    if data_type=='website':
        website_data = website_scrape(data)
        user_id = user.id
        knowledge_base_embedding_and_storage(user_id, website_data)
        knowledge_base = KnowledgeBase(data_type='website', data=data, user_id=user_id)
        db.add(knowledge_base)
        db.commit()
        
    if data_type=='files':
        if not file.filename.endswith(".pdf"):
            return JSONResponse(status_code=400, content="Only PDF files are allowed.")

        filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        with open(file_path, "wb") as f:
            f.write(file.file.read())

        file_url = f"/uploads/{filename}"

        knowledge_base = KnowledgeBase(data_type='files', data=data, path=file_url, user_id=user_id)
        db.add(knowledge_base)
        db.commit()
        db.refresh(knowledge_base)
        
        process_large_pdf_to_pinecone(file_path, user_id)
        
    return JSONResponse({"success": "Your data is stored in BrainAI knowledge base"}, status_code=200)

@router.get('/snippets')
def get_snippets(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': "user does not exist"}, status_code=404)
    snippets = db.query(KnowledgeBase).filter_by(data_type='snippet', user_id=user_id).all()
    info = []
    for snippet in snippets:
        info.append(snippet.data)
    websites = db.query(KnowledgeBase).filter_by(data_type='website', user_id=user_id).all()
    website_urls = []
    for website in websites:
        website_urls.append(website.data)
    files = db.query(KnowledgeBase).filter_by(data_type='files', user_id=user_id).all()
    documents = []
    for file in files:
        path = f"http://116.202.210.102:8000{file.path}"
        documents.append(path)
    return JSONResponse({"snippets": info, "website": website_urls, "files":documents},status_code=200)





        
        
        
        
    
        




