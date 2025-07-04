import os
from openai import OpenAI
from langchain_openai import ChatOpenAI

openai_client = OpenAI(api_key=os.getenv("API_KEY"))

llm = ChatOpenAI(api_key=os.getenv("API_KEY"),
                    model="gpt-4o",
                    temperature=1.5,
                    top_p=0.7)