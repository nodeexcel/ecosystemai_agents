from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .router import (appointment_setter, knowledge_base, email_agent,
                     phone_agent, account_agent, seo_agent, coo_agent, hr_agent,
                     content_creation, admin, customer_support)
from .social_media_integrations import (instagram, whatsapp, google_calendar, linkedin)
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
app.include_router(email_agent.router)
app.include_router(phone_agent.router)
app.include_router(instagram.router)
app.include_router(whatsapp.router)
app.include_router(google_calendar.router)
app.include_router(account_agent.router)
app.include_router(seo_agent.router)
app.include_router(coo_agent.router)
app.include_router(hr_agent.router)
app.include_router(content_creation.router)
app.include_router(linkedin.router)
app.include_router(admin.router)
app.include_router(customer_support.router)

@app.get("/")
def health_check():
    return JSONResponse(content={"message": "success"}, status_code=200)