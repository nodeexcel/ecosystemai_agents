from fastapi import FastAPI
from .router import appointment_setter, knowledge_base, email_agent, phone_agent
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,           
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(appointment_setter.router)
app.include_router(knowledge_base.router)
app.include_router(email_agent.router)
app.include_router(phone_agent.router)