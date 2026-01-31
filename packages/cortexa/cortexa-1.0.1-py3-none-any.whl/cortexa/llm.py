import requests
import json

class LLM:
    def __init__(self, model="llama3"):
        self.model = model
        self.url = "http://localhost:11434/api/chat"

    def stream_generate(self, messages):
        with requests.post(
            self.url,
            json={
                "model": self.model,
                "messages": messages,
                "stream": True
            },
            stream=True,
            timeout=300
        ) as response:

            response.raise_for_status()

            for line in response.iter_lines():
                if not line:
                    continue

                data = json.loads(line.decode("utf-8"))

                if "message" in data:
                    yield data["message"]["content"]
