import os
from google import genai

api_key = os.environ.get("GOOGLE_API_KEY") or "AIzaSyCedINEB2WO60mrmVuv88LmIo2Q77Stc0g"
client = genai.Client(api_key=api_key)

print("Listing models...")
try:
    # In the new SDK, client.models.list() returns an iterator of models
    response = client.models.list()
    for m in response:
        print(f"Name: {m.name}, DisplayName: {m.display_name}")
except Exception as e:
    print(f"Error: {e}")
