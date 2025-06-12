import os
from openai import OpenAI

openai_client = OpenAI(api_key=os.getenv("API_KEY"))