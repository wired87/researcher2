import os
from typing import Any, Dict, List
from googlesearch import search
from ..base import BaseTool

class GoogleSearchTool(BaseTool):
    def __init__(self):
        super().__init__("google_search")
        # No API keys required for this implementation
        pass

    def construct_query(self, requirements: Dict[str, Any]) -> str:
        """
        Extracts the query string from the requirements dictionary.
        """
        return requirements.get("query", "")

    def run(self, query: str) -> List[Any]:
        """
        Executes the search using googlesearch-python.
        Returns a list of SearchResult objects.
        """
        print(f"Executing Google Search for: {query}")
        try:
            # Step 1: Perform the search
            # We use advanced=True to get more details like title and description
            # num_results=10 limits the number of results to fetch
            results = list(search(query, num_results=10, advanced=True))
            return results
        except Exception as e:
            print(f"Error during Google Search: {e}")
            return []

    def process_response(self, response: List[Any]) -> Dict[str, Any]:
        """
        Processes the list of SearchResult objects into a standardized dictionary format.
        """
        results = []
        
        # Step 2: Iterate through the results
        for item in response:
            # Step 3: Extract relevant fields
            # The SearchResult object has .title, .url, and .description attributes
            results.append({
                "title": item.title,
                "link": item.url,
                "snippet": item.description
            })
            
        # Step 4: Return the formatted results
        return {
            "type": "json",
            "content": results
        }
