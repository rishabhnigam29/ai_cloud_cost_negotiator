import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")


def get_llm(temperature: float = 0.0):
    return ChatOpenAI(
        model=OPENAI_MODEL,
        temperature=temperature,
    )