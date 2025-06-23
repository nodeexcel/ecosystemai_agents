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

def email_correction(prompt, email):
    ai_response = llm.invoke([("system", prompt), ("human", email)])
    ai_response = ai_response.content
    if ai_response.startswith('"') and ai_response.endswith('"'):
        ai_response = ai_response[1:-1]
    elif ai_response.startswith("'") and ai_response.endswith("'"):
        ai_response = ai_response[1:-1]
    return ai_response
