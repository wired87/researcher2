import os
import json
import time
from typing import Dict, Any, List
from .tools.google_search.wrapper import GoogleSearchTool
from .tools.wolfram_alpha.wrapper import WolframAlphaTool
from .tools.arxiv.wrapper import ArxivTool
from .tools.nature.wrapper import NatureTool
from .tools.pubmed.wrapper import PubmedTool
from .env import Gem

class ResearchAgent:
    def __init__(self):
        self.gem = Gem()
        self.tools = {
            #"google_search": GoogleSearchTool,
            #"wolfram_alpha": WolframAlphaTool,
            "arxiv": ArxivTool,
            #"nature": NatureTool,
            #"pubmed": PubmedTool
        }
        self.output_dir = os.getenv("OUTPUTS", "data")
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        self.gem = Gem()

    def generate_queries(self, prompt: str) -> List[List[str]]:
        """
        Generates 3x3 queries for the first 3 tools based on the prompt using an LLM.
        Returns a list of lists of strings.
        """
        #tool_names = list(self.tools.keys())
        
        llm_prompt = f"""
        You are a research assistant.
        My research goal is: "{prompt}".
        
        Please generate 3 distinct search queries to extract as 
        much infromation as possible form the search queries
        """
        queries = self.gem.ask(llm_prompt)

        return queries


        
        
        try:
            response_text = self.gem.ask(llm_prompt)
            # Clean up potential markdown code blocks if the LLM adds them
            if response_text:
                cleaned_text = response_text.strip()
                if cleaned_text.startswith("```json"):
                    cleaned_text = cleaned_text[7:]
                if cleaned_text.startswith("```"):
                    cleaned_text = cleaned_text[3:]
                if cleaned_text.endswith("```"):
                    cleaned_text = cleaned_text[:-3]
                
                queries = json.loads(cleaned_text.strip())
                
                if isinstance(queries, list) and len(queries) == 3:
                    return queries
            
            print("Warning: LLM returned unexpected format. Fallback to simple queries.")
            return [[prompt]*3] * 3
            
        except Exception as e:
            print(f"Error generating queries with LLM: {e}. Fallback to simple queries.")
            return [[prompt]*3] * 3

    def run(self):
        prompt = os.getenv("RESEARCH_PROMPT")
        if not prompt:
            raise ValueError("RESEARCH_PROMPT environment variable is required.")

        print(f"Starting research for: {prompt}")
        
        # Get the first 3 tools to match the 3x3 queries
        active_tools = list(self.tools.items())
        
        query = self.generate_queries(prompt)
        
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
                self.save_response(f"{tool_name}_{q[:10].replace(' ', '_')}", processed_response)
                    
            except Exception as e:
                print(f"Error running {tool_name}: {e}")

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
