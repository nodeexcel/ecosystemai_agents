import os, json, html
from langchain_openai import ChatOpenAI
from .prompts import Prompts


llm = ChatOpenAI(
    model="gpt-4o",
    api_key=os.getenv("API_KEY"),
    temperature=1.5,
    top_p=0.7
)

def email_agent(prompt):
    ai_message = llm.invoke([("system", prompt)])
    email_prompt = ai_message.content
    ai_message = llm.invoke([("system", email_prompt)])
    email = ai_message.content
    email_correction_prompt = Prompts.email_validation()
    ai_response = llm.invoke([("system", email_correction_prompt), ("human", email)])
    ai_response = ai_response.content
    if ai_response.startswith('"') and ai_response.endswith('"'):
        ai_response = ai_response[1:-1]
    elif ai_response.startswith("'") and ai_response.endswith("'"):
        ai_response = ai_response[1:-1]

    return ai_response, email


import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "atul.etech2011@gmail.com"
SMTP_PASSWORD = "lyiy hbto zvnx lhge"  # Use App Password if using Gmail 2FA

SENDER_EMAIL = SMTP_USERNAME


def send_email(body: str, html: bool = False):
    msg = MIMEMultipart("alternative")
    msg["From"] = SENDER_EMAIL
    msg["To"] = "atul.etech2011@gmail.com"
    msg["Subject"] = "test"

    # Attach plain or HTML content
    if html:
        part = MIMEText(body, "html")
    else:
        part = MIMEText(body, "plain")
    msg.attach(part)
    print("bvhgbhubihbihbih")
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SENDER_EMAIL, "aay.etech2011@gmail.com", msg.as_string())