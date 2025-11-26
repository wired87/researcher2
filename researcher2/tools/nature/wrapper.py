import os
import requests
from typing import Any, Dict
from ..base import BaseTool

class NatureTool(BaseTool):
    def __init__(self):
        super().__init__("nature")
        self.api_key = os.getenv("NATURE_API_KEY")
        if not self.api_key:
            raise ValueError("NATURE_API_KEY environment variable is required.")

    def construct_query(self, requirements: Dict[str, Any]) -> str:
        return requirements.get("query", "")

    def run(self, query: str) -> Dict[str, Any]:
        url = "http://api.springernature.com/openaccess/json"
        params = {
            "api_key": self.api_key,
            "q": query,
            "p": 5  # limit results
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        records = response.get("records", [])
        results = []
        for record in records:
            results.append({
                "title": record.get("title"),
                "abstract": record.get("abstract"),
                "url": record.get("url"),
                "publicationName": record.get("publicationName")
            })
        return {
            "type": "json",
            "content": results
        }
