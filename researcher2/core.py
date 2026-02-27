import os
import json
import re
import threading
import time
from typing import Dict, Any, List, Callable

import requests

from core.session_manager.session import session_manager
from vertex_rag.engine import VertexRagEngine


class ResearchAgent:
    def __init__(self, file_manager, gem, vrag_engien):
        self.gem = gem
        self.tools = {
            #"google_search": GoogleSearchTool,
            #"wolfram_alpha": WolframAlphaTool,
            #s"arxiv": ArxivTool,
            #"nature": NatureTool,
            #"pubmed": PubmedTool
        }
        self.file_manager = file_manager
        self.threads = []
        self.output_dir = os.getenv("OUTPUTS", "data")
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        # Vertex AI RAG main class (configured per-session when needed)
        self.vertex_rag = vrag_engien

    def start_research_for_session(self, user_id: str, session_id: str, prompt: str) -> None:
        """
        Kick off a deep-research workflow for a session.

        - Uses ResearchAgent to discover relevant documents.
        - The callback merges discovered URLs into the session's research_files column.
        - ResearchAgent.research_workflow handles file processing and Vertex RAG ingestion.
        """

        def _on_sources(urls: List[str]) -> None:
            try:
                session_manager.update_research_files(user_id, session_id, urls)
            except Exception as e:
                print(f"[OrchestratorManager] Failed to update research_files via callback: {e}")

        self.run(
            prompt=prompt,
            use_dr_result_callable=_on_sources,
            user_id=user_id,
            session_id=session_id,
        )


    def generate_queries(self, prompt: str) -> List[List[str]]:
        """
        Generates 3x3 queries for the first 3 tools based on the prompt using an LLM.
        Returns a list of lists of strings.
        """
        
        llm_prompt = f"""
        You are a research assistant.
        My research goal is: "{prompt}".
        Please generate 3 distinct search queries to extract as 
        much infromation as possible form the search queries
        """
        queries = self.gem.ask(llm_prompt)
        print("queries", queries)
        return queries

    def research_workflow(self, user_id: str, session_id: str, file_urls: List[str]):
        """
        Executes the research workflow:
        1. Receives file contents (bytes) and URLs from a research thread.
        2. Uses FileManager to process/extract components from these files.
        3. Upserts the extracted components (Modules, Fields, Params, Methods).
        4. Updates the session's research_files list.
        """
        print(f"Starting research workflow for session {session_id}...")

        # 0. Persist discovered research file URLs on the session
        try:
            session_manager.update_research_files(user_id, session_id, file_urls)
        except Exception as e:
            print(f"Warning: failed to update research_files for session {session_id}: {e}")

        # 0b. If the session has a dedicated RAG corpus, import the remote files into it
        rag_engine_for_session = None
        try:
            session = session_manager.get_session(int(session_id))
            corpus_id = session.get("corpus_id") if session else None
            if corpus_id:
                rag_engine_for_session = VertexRagEngine(corpus_id=corpus_id)
                try:
                    rag_engine_for_session.import_remote_files(paths=file_urls)
                except Exception as re_err:
                    print(f"Warning: Vertex RAG import failed for session {session_id}: {re_err}")
        except Exception as e:
            print(f"Warning: failed to initialize VertexRagEngine for session {session_id}: {e}")

        content = []
        for url in file_urls:
            content.append(requests.get(url).content)

        # We assume these files belong to a single logical 'module' or context for now, 
        # or we iterate if they are distinct. 
        # Let's treat them as a batch for a new module or update.
        # For simplicity, we'll generate a placeholder module ID or derive it.
        module_id = f"mod_research_{session_id}_{len(file_urls)}"

        # 1. Extract Data using RawModuleExtractor logic (inherited by FileManager)
        extracted_data = self.file_manager.process_bytes(module_id, content)

        # 2. Prepare data for upsert (similar to process_and_upload_file_config)
        data_payload = {
            "id": module_id,
            "source_urls": file_urls,
            "description": "Auto-generated from research workflow",
        }

        # Upsert Params
        params_dict = extracted_data.get("params", {})
        if params_dict:
            params_list = []
            for p_name, p_type in params_dict.items():
                params_list.append({
                    "id": p_name,
                    "name": p_name,
                    "param_type": p_type,
                    "description": f"Extracted from {module_id}",
                    "user_id": user_id
                })
            self.file_manager.param_manager.set_param(params_list, user_id)

        # Upsert Methods
        methods_list = extracted_data.get("methods", [])
        if methods_list:
            for m in methods_list:
                m["user_id"] = user_id
                if "id" in m:
                    m["id"] = m["id"]
            self.file_manager.method_manager.set_method(methods_list, user_id)

        # Upsert Fields
        fields_list = extracted_data.get("fields", [])
        if fields_list:
            for f in fields_list:
                f["user_id"] = user_id
                if "id" in f:
                    f["id"] = f["id"]
            self.file_manager.fields_manager.set_field(fields_list, user_id)

        # Upsert Module
        module_row = {
            **data_payload,
            **extracted_data,
            "user_id": user_id
        }
        # Cleanup lists
        module_row.pop("methods", None)
        module_row.pop("fields", None)

        self.file_manager.set_module(module_row, user_id)

        print(f"Research workflow completed for module {module_id}")
        return module_id
    

    def run(
            self,
            prompt,
            use_dr_result_callable:Callable,
            user_id="test_user",
            session_id="test_session",
    ):
        if not prompt:
            raise ValueError("RESEARCH_PROMPT environment variable is required.")

        print(f"Starting research for: {prompt}")
        
        # Get the first 3 tools to match the 3x3 queries
        active_tools = list(self.tools.items())
        
        query = self.generate_queries(prompt)

        if use_dr_result_callable is not None:
            prompt += "THE RESULT OF THE PROMPT SHOULD JSUT BE 5 top web apths to downlaodabel pdf files (fetchable)"
            t = threading.Thread(
                target=self.run_research_thread,
                args=(prompt, use_dr_result_callable)
            )
            self.threads.append(t)
            t.start()
            t.join(timeout=999)
            response = self.gem.ask(
                prompt
            )
            sources = re.findall(r'(https?://\S+|/path/to/\S+)', response)
            top_5 = list(dict.fromkeys(sources))[:5]

            self.research_workflow(
                user_id=user_id,
                session_id=session_id,
                file_urls=top_5,
            )
            print("research thead started")

        else:
            for i, (tool_name, tool_class) in enumerate(active_tools):

                tool_queries = query
                print(f"Running {tool_name} with queries: {tool_queries}")



                try:
                    tool = tool_class()
                    # Run for each query generated
                    print(f" run - Query: {query}")
                    query_reqs = {"query": query}
                    query = tool.construct_query(query_reqs)
                    raw_response = tool.run(query)
                    processed_response = tool.process_response(raw_response)
                    self.save_response(f"{tool_name}_{query[:10].replace(' ', '_')}", processed_response)

                except Exception as e:
                    print(f"Error running {tool_name}: {e}")


    from typing import Callable, List

    def run_research_thread(self, prompt: str, callback: Callable[[List[str]], None]):
        """
        Startet den Deep Research Agent in einem Thread und gibt die
        Top 5 Quellen an den Callback weiter.
        """


        try:
            interaction = self.gem.client.interactions.create(
                input=prompt,
                agent='deep-research-pro-preview-12-2025',
                background=True
            )
            print(f"Deep Research gestartet: {interaction.id}")
            i=0
            while True:
                interaction = self.gem.client.interactions.get(interaction.id)
                if interaction.status == "completed":
                    full_text = interaction.outputs[-1].text
                    # Extrahiere Top 5 Quellen (URLs oder Pfade) via Regex
                    sources = re.findall(r'(https?://\S+|/path/to/\S+)', full_text)
                    top_5 = list(dict.fromkeys(sources))[:5]  # Eindeutige Top 5
                    callback(top_5)
                    break
                elif interaction.status == "failed":
                    print(f"Research failed: {interaction.error}")
                    break
                i+=1
                print("t-step", i)
                time.sleep(10)
        except Exception as e:
            print(f"Thread Error: {e}")


    def save_response(self, tool_name: str, response: Dict[str, Any]):
        #timestamp = int(time.time())
        filename = f"{tool_name}"
        
        content = response["content"]
        response_type = response["type"]

        if response_type == "json":
            filepath = os.path.join(self.output_dir, f"{filename}.json")
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(content, f, indent=2)
        else:
            filepath = os.path.join(self.output_dir, f"{filename}.txt")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(str(content))
        
        print(f"Saved output to {filepath}")
