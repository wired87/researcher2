import os
from Bio import Entrez
from typing import Any, Dict
from ..base import BaseTool

class PubmedTool(BaseTool):
    def __init__(self):
        super().__init__("pubmed")
        Entrez.email = os.getenv("PUBMED_EMAIL")
        if not Entrez.email:
             raise ValueError("PUBMED_EMAIL environment variable is required.")
        # Optional API key
        api_key = os.getenv("PUBMED_API_KEY")
        if api_key:
            Entrez.api_key = api_key

    def construct_query(self, requirements: Dict[str, Any]) -> str:
        return requirements.get("query", "")

    def run(self, query: str) -> Any:
        # Search for IDs
        handle = Entrez.esearch(db="pubmed", term=query, retmax=5)
        record = Entrez.read(handle)
        handle.close()
        id_list = record["IdList"]
        
        if not id_list:
            return []

        # Fetch details
        handle = Entrez.efetch(db="pubmed", id=id_list, rettype="medline", retmode="text")
        records = handle.read()
        handle.close()
        return records

    def process_response(self, response: Any) -> Dict[str, Any]:
        # Response is raw text in MEDLINE format
        return {
            "type": "text",
            "content": response
        }
