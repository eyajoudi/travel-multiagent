"""
LLM unique utilisé par tous les agents.
Note: llama-3.3-70b-versatile est passé "Enterprise only" chez Groq (plus accessible
en free tier). On utilise gpt-oss-20b à la place : gratuit, rapide, bon en JSON.
"""
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

def get_llm(temperature: float = 0):
    return ChatGroq(
        model="openai/gpt-oss-20b",
        temperature=temperature,
        api_key=os.environ["GROQ_API_KEY"],
    )


def parse_json_response(text: str) -> str:
    """Retire les ```json ... ``` que gpt-oss ajoute parfois autour du JSON."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        text = text.removeprefix("json").strip()
    return text
