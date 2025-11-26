import arxiv
from typing import Any, Dict
from ..base import BaseTool

class ArxivTool(BaseTool):
    def __init__(self):
        super().__init__("arxiv")
        self.client = arxiv.Client()

    def construct_query(self, requirements: Dict[str, Any]) -> str:
        return requirements.get("query", "")

    def run(self, query: str) -> Any:
        search = arxiv.Search(
            query=query,
            max_results=5,
            sort_by=arxiv.SortCriterion.Relevance
        )
        return list(self.client.results(search))

    def process_response(self, response: Any) -> Dict[str, Any]:
        results = []
        for result in response:
            results.append({
                "title": result.title,
                "summary": result.summary,
                "pdf_url": result.pdf_url,
                "published": str(result.published)
            })
        return {
            "type": "json",
            "content": results
        }
