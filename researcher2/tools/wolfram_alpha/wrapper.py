import os
import wolframalpha
from typing import Any, Dict
from ..base import BaseTool

class WolframAlphaTool(BaseTool):
    def __init__(self):
        super().__init__("wolfram_alpha")
        self.app_id = os.getenv("WOLFRAM_APP_ID")
        if not self.app_id:
            raise ValueError("WOLFRAM_APP_ID environment variable is required.")
        self.client = wolframalpha.Client(self.app_id)

    def construct_query(self, requirements: Dict[str, Any]) -> str:
        return requirements.get("query", "")

    def run(self, query: str) -> Any:
        return self.client.query(query)

    def process_response(self, response: Any) -> Dict[str, Any]:
        results = []
        for pod in response.pods:
            for sub in pod.subpods:
                if sub.plaintext:
                    results.append({
                        "title": pod.title,
                        "text": sub.plaintext
                    })
        return {
            "type": "text",
            "content": "\n".join([f"{r['title']}: {r['text']}" for r in results])
        }
