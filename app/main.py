from fastapi import FastAPI
from .router import appointment_setter, knowledge_base
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,           
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(appointment_setter.router)
app.include_router(knowledge_base.router)
