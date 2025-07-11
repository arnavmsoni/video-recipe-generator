import os
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("OPENAI_API_KEY")
assert key and key.startswith("sk-"), "API key not found or invalid"
print("successfully loaded:", key[:8] + "...")