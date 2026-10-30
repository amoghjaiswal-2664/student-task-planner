from dotenv import load_dotenv
from groq import Groq

load_dotenv()

MODEL = "openai/gpt-oss-20b"

def complete(prompt: str, system: str | None = None) -> str:
    client = Groq()
    messages = [] 
    if system:
        messages.append({"role": "system","content": system})
    messages.append({"role": "user","content": prompt})
    response = client.chat.completions.create(model=MODEL, messages=messages, temperature=0)
    return response.choices[0].message.content