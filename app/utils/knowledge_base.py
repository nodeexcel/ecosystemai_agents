import os
from langchain_openai import ChatOpenAI
from app.ai_agents.prompts import Prompts

llm = ChatOpenAI(
    model="gpt-4o",
    api_key=os.getenv("API_KEY"),
)

def website_scrape(website_link):
    prompt = Prompts.website_info_prompt()
    messages = [
    (
        "system", prompt
    ),
    ("human", website_link),
]
    data = llm.invoke(messages)
    return data