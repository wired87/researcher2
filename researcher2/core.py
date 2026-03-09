import os
import json
import re
import time
from typing import Dict, Any, List, Callable, Optional, Tuple

import requests

from qbrain.core.session_manager.session import session_manager

# Default deep-research backend: "chatgpt" (LangChain + OpenAI + search) or "gemini"
DEFAULT_DEEP_RESEARCH_BACKEND = os.environ.get("DEEP_RESEARCH_BACKEND", "chatgpt").strip().lower()


def _extract_urls_from_text(text: str, max_urls: int = 5) -> List[str]:
    """Extract HTTP(S) URLs from text; return up to max_urls unique."""
    if not text:
        return []
    sources = re.findall(r'https?://[^\s\)\]\>"]+', text)
    return list(dict.fromkeys(sources))[:max_urls]


def _fetch_url_contents(urls: List[str]) -> List[Tuple[str, bytes]]:
    """Fetch raw content (bytes) for each URL. Returns list of (url, content)."""
    results: List[Tuple[str, bytes]] = []
    for url in urls:
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            results.append((url, resp.content))
        except Exception as e:
            print(f"[ResearchAgent] fetch failed for {url[:60]}...: {e}")
    return results


class ResearchAgent:
    def __init__(
        self,
        file_manager,
        gem,
        deep_research_backend: str = DEFAULT_DEEP_RESEARCH_BACKEND,
    ):
        self.gem = gem
        self.file_manager = file_manager
        self.tools = {}
        self.output_dir = os.getenv("OUTPUTS", "data")
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        self.deep_research_backend = (
            deep_research_backend if deep_research_backend in ("chatgpt", "gemini") else "chatgpt"
        )

    def start_research_for_session(
        self, user_id: str, session_id: str, prompt: str
    ) -> Dict[str, Any]:
        """
        Run deep research for a session and return found URLs and file content.
        Updates session research_files with discovered URLs.
        """
        result = self.run(
            prompt=prompt,
            use_dr_result_callable=lambda urls: session_manager.update_research_files(
                user_id, session_id, urls
            ),
            user_id=user_id,
            session_id=session_id,
        )
        return result or {}

    def generate_queries(self, prompt: str) -> List[str]:
        """Generate search queries from the prompt using the LLM."""
        llm_prompt = f"""
You are a research assistant.
My research goal is: "{prompt}".
Please generate 3 distinct search queries to extract as much information as possible from the search.
Return only the queries, one per line or comma-separated.
"""
        try:
            raw = self.gem.ask(llm_prompt)
            if isinstance(raw, list):
                return raw
            text = (raw or "").strip()
            queries = [q.strip() for q in re.split(r"[\n,]", text) if q.strip()][:3]
            return queries or [prompt]
        except Exception as e:
            print(f"[ResearchAgent] generate_queries: {e}")
            return [prompt]

    def _get_paper_urls_gemini(self, prompt: str, max_urls: int = 5) -> List[str]:
        """Use Gemini deep-research interaction to get paper URLs."""
        try:
            interaction = self.gem.client.interactions.create(
                input=prompt,
                agent="deep-research-pro-preview-12-2025",
                background=True,
            )
            print(f"[ResearchAgent] Gemini deep research started: {interaction.id}")
            for i in range(120):  # ~20 min at 10s
                interaction = self.gem.client.interactions.get(interaction.id)
                if interaction.status == "completed":
                    full_text = (interaction.outputs or [])[-1].text if interaction.outputs else ""
                    return _extract_urls_from_text(full_text, max_urls=max_urls)
                if interaction.status == "failed":
                    print(f"[ResearchAgent] Gemini deep research failed: {getattr(interaction, 'error', 'unknown')}")
                    return []
                time.sleep(10)
            print("[ResearchAgent] Gemini deep research timeout")
            return []
        except Exception as e:
            print(f"[ResearchAgent] _get_paper_urls_gemini: {e}")
            return []

    def _get_paper_urls_chatgpt(self, prompt: str, max_urls: int = 5) -> List[str]:
        """Use LangChain (OpenAI + search) to find paper URLs."""
        try:
            from langchain_openai import ChatOpenAI
            from langchain_community.tools import DuckDuckGoSearchRun
            from langchain_core.messages import HumanMessage, SystemMessage
            from langchain_core.output_parsers import StrOutputParser
        except ImportError as e:
            print(f"[ResearchAgent] LangChain not available for ChatGPT deep research: {e}")
            return []

        try:
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
            search = DuckDuckGoSearchRun(max_results=8)
            system = (
                "You are a research assistant. Your task is to find downloadable PDF or paper URLs "
                "relevant to the user's query. Return only a list of full URLs, one per line. "
                "Prefer direct PDF links (e.g. arxiv.org/pdf/..., PDF links from publishers)."
            )
            user_msg = (
                f"Find up to {max_urls} direct URLs to research papers or PDFs about: {prompt}\n\n"
                "Return only the URLs, one per line, no other text."
            )
            # Single search then LLM to extract/rank URLs
            search_result = search.invoke(prompt[:500])
            if not search_result:
                search_result = search.invoke("research papers " + prompt[:300])
            combined = f"Search results:\n{search_result}\n\nUser query: {prompt}\n\nExtract and return only the best paper/PDF URLs from the search results, one per line (max {max_urls})."
            chain = llm | StrOutputParser()
            response = chain.invoke([SystemMessage(content=system), HumanMessage(content=combined)])
            return _extract_urls_from_text(response or "", max_urls=max_urls)
        except Exception as e:
            print(f"[ResearchAgent] _get_paper_urls_chatgpt: {e}")
            return []

    def deep_research(
        self,
        prompt: str,
        backend: Optional[str] = None,
        max_urls: int = 5,
    ) -> Dict[str, Any]:
        """
        Run deep research (Gemini or ChatGPT via LangChain) and fetch content from discovered URLs.
        Returns dict with keys: urls (list[str]), contents (list[bytes]), contents_by_url (dict url -> bytes).
        """
        backend = (backend or self.deep_research_backend).strip().lower()
        if backend not in ("chatgpt", "gemini"):
            backend = "chatgpt"
        urls = (
            self._get_paper_urls_chatgpt(prompt, max_urls=max_urls)
            if backend == "chatgpt"
            else self._get_paper_urls_gemini(prompt, max_urls=max_urls)
        )
        if not urls:
            return {"urls": [], "contents": [], "contents_by_url": {}}
        fetched = _fetch_url_contents(urls)
        contents = [b for _, b in fetched]
        contents_by_url = {u: b for u, b in fetched}
        return {
            "urls": urls,
            "contents": contents,
            "contents_by_url": contents_by_url,
        }

    def research_workflow(
        self,
        user_id: str,
        session_id: str,
        file_urls: List[str],
        file_contents: Optional[List[bytes]] = None,
    ) -> Dict[str, Any]:
        """
        Persist URLs on session, optionally process file content via FileManager, and return
        found file content (urls + contents). No Vertex RAG.
        """
        print(f"[ResearchAgent] Starting research workflow for session {session_id}...")
        try:
            session_manager.update_research_files(user_id, session_id, file_urls)
        except Exception as e:
            print(f"[ResearchAgent] Warning: update_research_files failed: {e}")

        # Fetch content if not provided
        if file_contents is None or len(file_contents) != len(file_urls):
            fetched = _fetch_url_contents(file_urls)
            file_contents = [b for _, b in fetched]
            file_urls = [u for u, _ in fetched]

        module_id = f"mod_research_{session_id}_{len(file_urls)}"
        extracted_data = None
        try:
            extracted_data = self.file_manager.process_bytes(module_id, file_contents)
        except Exception as e:
            print(f"[ResearchAgent] process_bytes skipped: {e}")

        if extracted_data:
            from qbrain.core.managers_context import get_param_manager, get_field_manager, get_method_manager
            param_mgr = getattr(self.file_manager, "param_manager", None) or get_param_manager()
            method_mgr = getattr(self.file_manager, "method_manager", None) or get_method_manager()
            field_mgr = getattr(self.file_manager, "fields_manager", None) or get_field_manager()
            data_payload = {
                "id": module_id,
                "source_urls": file_urls,
                "description": "Auto-generated from research workflow",
            }
            params_dict = extracted_data.get("params", {})
            if params_dict:
                params_list = [
                    {
                        "id": p_name,
                        "name": p_name,
                        "param_type": p_type,
                        "description": f"Extracted from {module_id}",
                        "user_id": user_id,
                    }
                    for p_name, p_type in params_dict.items()
                ]
                param_mgr.set_param(params_list, user_id)
            methods_list = extracted_data.get("methods", [])
            if methods_list:
                for m in methods_list:
                    m["user_id"] = user_id
                method_mgr.set_method(methods_list, user_id)
            fields_list = extracted_data.get("fields", [])
            if fields_list:
                for f in fields_list:
                    f["user_id"] = user_id
                field_mgr.set_field(fields_list, user_id)
            module_row = {
                **data_payload,
                **extracted_data,
                "user_id": user_id,
            }
            module_row.pop("methods", None)
            module_row.pop("fields", None)
            self.file_manager.set_module(module_row, user_id)
        print(f"[ResearchAgent] Research workflow completed for module {module_id}")

        return {
            "urls": file_urls,
            "contents": file_contents,
            "module_id": module_id,
        }

    def run(
        self,
        prompt: str,
        use_dr_result_callable: Optional[Callable[[List[str]], None]] = None,
        user_id: str = "test_user",
        session_id: str = "test_session",
    ) -> Dict[str, Any]:
        """
        Run deep research (backend from init), fetch content, optionally call callback with URLs,
        run research_workflow, and return found file content (urls + contents).
        """
        if not prompt:
            raise ValueError("Research prompt is required.")
        print(f"[ResearchAgent] Starting research for: {prompt[:80]}...")
        dr = self.deep_research(prompt, max_urls=5)
        urls = dr.get("urls") or []
        contents = dr.get("contents") or []
        if use_dr_result_callable and urls:
            try:
                use_dr_result_callable(urls)
            except Exception as e:
                print(f"[ResearchAgent] Callback error: {e}")
        if not urls:
            print("[ResearchAgent] No URLs found from deep research.")
            return {"urls": [], "contents": [], "module_id": None}
        result = self.research_workflow(
            user_id=user_id,
            session_id=session_id,
            file_urls=urls,
            file_contents=contents,
        )
        print("[ResearchAgent] Research run finished.")
        return result

    def save_response(self, tool_name: str, response: Dict[str, Any]) -> None:
        filename = tool_name
        content = response.get("content")
        response_type = response.get("type", "text")
        if response_type == "json":
            filepath = os.path.join(self.output_dir, f"{filename}.json")
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(content, f, indent=2)
        else:
            filepath = os.path.join(self.output_dir, f"{filename}.txt")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(str(content))
        print(f"[ResearchAgent] Saved output to {filepath}")
