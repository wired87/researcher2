import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from researcher2.core import ResearchAgent

class TestResearchAgent(unittest.TestCase):
    @patch('researcher2.core.Gem')
    def test_generate_queries_structure(self, MockGem):
        # Mock the Gem instance and its ask method
        mock_gem_instance = MockGem.return_value
        # Return a valid JSON string representing 3x3 queries
        mock_gem_instance.ask.return_value = '''
        [
            ["q1_t1", "q2_t1", "q3_t1"],
            ["q1_t2", "q2_t2", "q3_t2"],
            ["q1_t3", "q2_t3", "q3_t3"]
        ]
        '''
        
        agent = ResearchAgent()
        queries = agent.generate_queries("test prompt")
        
        self.assertIsInstance(queries, list)
        self.assertEqual(len(queries), 3)
        for row in queries:
            self.assertIsInstance(row, list)
            self.assertEqual(len(row), 3)
            for q in row:
                self.assertIsInstance(q, str)
                
        print("generate_queries returned correct structure:")
        print(queries)

    @patch('researcher2.core.Gem')
    def test_generate_queries_fallback(self, MockGem):
        # Mock Gem to raise an exception
        mock_gem_instance = MockGem.return_value
        mock_gem_instance.ask.side_effect = Exception("LLM Error")
        
        agent = ResearchAgent()
        queries = agent.generate_queries("test prompt")
        
        # Should return fallback 3x3
        self.assertEqual(len(queries), 3)
        self.assertEqual(len(queries[0]), 3)
        self.assertEqual(queries[0][0], "test prompt")
        
        print("generate_queries fallback worked:")
        print(queries)

if __name__ == '__main__':
    unittest.main()
