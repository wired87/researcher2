import os
import sys
import unittest

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from researcher2.tools.google_search.wrapper import GoogleSearchTool

class TestGoogleSearchTool(unittest.TestCase):
    def test_search_execution(self):
        tool = GoogleSearchTool()
        query = "python programming language"
        
        print(f"Testing search for: {query}")
        # Construct query
        q_str = tool.construct_query({"query": query})
        self.assertEqual(q_str, query)
        
        # Run search
        raw_results = tool.run(q_str)
        self.assertIsInstance(raw_results, list)
        
        # Process response
        processed = tool.process_response(raw_results)
        self.assertEqual(processed["type"], "json")
        content = processed["content"]
        self.assertIsInstance(content, list)
        
        if len(content) > 0:
            print(f"Found {len(content)} results.")
            first = content[0]
            print("First result:", first)
            self.assertIn("title", first)
            self.assertIn("link", first)
            self.assertIn("snippet", first)
        else:
            print("Warning: No results found (could be network issue or rate limit)")

if __name__ == '__main__':
    unittest.main()
