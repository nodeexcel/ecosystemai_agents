from io import BytesIO
import os
import uuid 

from fastapi import Depends, UploadFile, Form, File, status
from fastapi.routing import APIRouter
from fastapi.responses import JSONResponse 
from langchain.chains.summarize import load_summarize_chain
from langchain_core.documents import Document
from typing import Optional

from sqlalchemy.orm import Session

from app.ai_agents.email_agent import llm
from app.models.get_db import get_db
from app.models.model import User, KnowledgeAttachment, KnowledgeBase
from app.services.aws_boto3 import aws_client, get_upload_args
from app.utils.user_auth import get_current_user
from app.utils.knowledge_base import (
    website_scrape, 
    knowledge_base_embedding_and_storage, 
    process_large_pdf_to_pinecone,
)
from app.utils.attachment_kb import process_attachment_to_pinecone
from app.services.babel import get_translator_dependency


router = APIRouter(tags=['knowledge_base'])

    
@router.post('/knowledge-base')
def embeddings_for_snippets(data: str = Form(...),
                            data_type: str = Form(...),
                            file: Optional[UploadFile] = File(None),
                            db: Session = Depends(get_db), user_id: str = Depends(get_current_user),
                            _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
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
            return JSONResponse(status_code=400, content=_("Only PDF files are allowed."))

        file_path = f"knowledge_base/{user.email}/{file.filename}"
        
        file_object = db.query(KnowledgeBase).filter_by(path=file_path).first()
        
        if file_object:
            return JSONResponse(content={"error": "File already exists"},  status_code=400)
        
        extra_args = get_upload_args(file.filename)
        
        try:
            aws_client.upload_fileobj(Fileobj=file.file, 
                       Bucket=os.getenv('BUCKET_NAME'), Key=file_path,
                       ExtraArgs=extra_args)
        except Exception as e:
            print(e)
            return JSONResponse(content={"error": "could not upload document"}, status_code=500)

        knowledge_base = KnowledgeBase(data_type='files', data=data, path=file_path, user_id=user_id)
        db.add(knowledge_base)
        db.commit()
        db.refresh(knowledge_base)
        
        file_path = os.getenv("S3_BASE_URL") + f"/{file_path}"
        try:
            process_large_pdf_to_pinecone(file_path, user_id)
        except Exception:
            return JSONResponse(content={"error": "Your request could not be supported"},  status_code=500)
        
    return JSONResponse({"success": _("Your data is stored in BrainAI knowledge base")}, status_code=200)

@router.get('/snippets')
def get_snippets(db: Session = Depends(get_db), user_id: str = Depends(get_current_user), _ = Depends(get_translator_dependency)):
    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    snippets = db.query(KnowledgeBase).filter_by(data_type='snippet', user_id=user_id).all()
    snippets_data = []
    for snippet in snippets:
        snippet_info = {}
        snippet_info['id'] = snippet.id
        snippet_info['data'] = snippet.data
        snippets_data.append(snippet_info)
        
    websites = db.query(KnowledgeBase).filter_by(data_type='website', user_id=user_id).all()
    website_urls = []
    website_info = {}
    for website in websites:
        website_info = {}
        website_info['id'] = website.id
        website_info['url'] = website.data
        website_urls.append(website_info)
        
    files = db.query(KnowledgeBase).filter_by(data_type='files', user_id=user_id).all()
    documents = []
    for file in files:
        document_info = {}
        document_info['id'] = file.id
        document_info['path'] = os.getenv("S3_BASE_URL") + f"/{file.path}"
        documents.append(document_info)
    return JSONResponse({"snippets": snippets_data, "website": website_urls, "files":documents},status_code=200)


@router.delete('/knowledge-base/{id}')
def delete_knowledge_base(id, db: Session = Depends(get_db), user_id: str = Depends(get_current_user),
                          _ = Depends(get_translator_dependency)):
                              
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(content={'error': _("user does not exist")}, status_code=404)
    knowledge_base = db.query(KnowledgeBase).filter_by(id=id, user_id=user_id).first()
    if not knowledge_base:
        return JSONResponse({"error": _("knowledge_base does not exist")}, status_code=404)
    db.delete(knowledge_base)
    db.commit()
    return JSONResponse({"success": _("knowledge base deleted successfully")},status_code=200)
    
@router.post("/kb-attachments")
async def upload_attachment(
    agent_name: str,
    db: Session = Depends(get_db), 
    user_id: str = Depends(get_current_user),
    attachment: UploadFile = File(...)
):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return JSONResponse(
            content={"error": "User does not exist"},
            status_code=404
        )
        
    file_id = str(uuid.uuid4())
    filename = attachment.filename
    file_path = f"chatbot/{agent_name}/{user.email}/{file_id}_{filename}"
    extra_args = get_upload_args(filename)
    file_content = await attachment.read()
    
    try:
        aws_client.upload_fileobj(
            Fileobj=attachment.file,
            Bucket=os.getenv("BUCKET_NAME"),
            Key=file_path,
            ExtraArgs=extra_args
        )
    except Exception as e:
        print(e)
        return JSONResponse(
            content={"error": "could not upload attachment"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
    attachment_url = os.getenv("S3_BASE_URL") + f"/{file_path}"
    
    metadata = {
        "attachment_url": attachment_url,
        "file_id": file_id,
        "filename": filename,
    }
    new_file_upload = UploadFile(
        filename=filename,
        file=BytesIO(file_content)
    )
    documents: list[Document] = process_attachment_to_pinecone(new_file_upload, user.id, metadata)
    chain = load_summarize_chain(llm, chain_type="map_reduce")
    summary = await chain.ainvoke(documents)
    
    attachment_content_creation = KnowledgeAttachment(
        agent_name=agent_name,
        attachment_url=attachment_url,
        file_id=file_id, 
        filename=filename,
        file_summary=summary['output_text'],
        user_id=user.id
    )
    db.add(attachment_content_creation)
    db.commit()
    db.refresh(attachment_content_creation)
    
    return JSONResponse(
        content={"message": {"file_id": file_id, "filename": filename}},
        status_code=status.HTTP_202_ACCEPTED
    )
        
        
    
        




