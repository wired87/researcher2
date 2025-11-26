import unittest
from unittest.mock import MagicMock, patch
import os
import shutil
from researcher2.core import ResearchAgent

class TestResearchAgent(unittest.TestCase):
    def setUp(self):
        self.output_dir = "test_outputs"
        os.environ["OUTPUTS"] = self.output_dir
        os.environ["RESEARCH_PROMPT"] = "test prompt"
        # Mock API keys
        os.environ["GOOGLE_API_KEY"] = "fake"
        os.environ["GOOGLE_CX"] = "fake"
        os.environ["WOLFRAM_APP_ID"] = "fake"
        os.environ["NATURE_API_KEY"] = "fake"
        os.environ["PUBMED_EMAIL"] = "fake@example.com"

    def tearDown(self):
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    @patch("researcher2.tools.google_search.wrapper.requests.get")
    @patch("researcher2.tools.wolfram_alpha.wrapper.wolframalpha.Client")
    @patch("researcher2.tools.arxiv.wrapper.arxiv.Client")
    @patch("researcher2.tools.nature.wrapper.requests.get")
    @patch("researcher2.tools.pubmed.wrapper.Entrez.esearch")
    @patch("researcher2.tools.pubmed.wrapper.Entrez.efetch")
    def test_run(self, mock_efetch, mock_esearch, mock_nature_get, mock_arxiv_client, mock_wolfram_client, mock_google_get):
        # Mock Google
        mock_google_response = MagicMock()
        mock_google_response.json.return_value = {"items": [{"title": "Test", "link": "http://test.com", "snippet": "Test snippet"}]}
        mock_google_get.return_value = mock_google_response

        # Mock Wolfram
        mock_wolfram_instance = MagicMock()
        mock_pod = MagicMock()
        mock_pod.title = "Result"
        mock_subpod = MagicMock()
        mock_subpod.plaintext = "42"
        mock_pod.subpods = [mock_subpod]
        mock_wolfram_instance.query.return_value = MagicMock(pods=[mock_pod])
        mock_wolfram_client.return_value = mock_wolfram_instance

        # Mock Arxiv
        mock_arxiv_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.title = "Arxiv Paper"
        mock_result.summary = "Summary"
        mock_result.pdf_url = "http://arxiv.org/pdf"
        mock_result.published = "2023-01-01"
        mock_arxiv_instance.results.return_value = [mock_result]
        mock_arxiv_client.return_value = mock_arxiv_instance

        # Mock Nature
        mock_nature_response = MagicMock()
        mock_nature_response.json.return_value = {"records": [{"title": "Nature Paper", "abstract": "Abstract", "url": "http://nature.com", "publicationName": "Nature"}]}
        mock_nature_get.return_value = mock_nature_response

        # Mock Pubmed
        mock_esearch_handle = MagicMock()
        mock_esearch.return_value = mock_esearch_handle
        # We need to mock Entrez.read separately or just mock the return of read if we mocked esearch to return a handle that read consumes.
        # But Entrez.read takes the handle.
        # Simpler: Mock Entrez.read
        with patch("researcher2.tools.pubmed.wrapper.Entrez.read") as mock_read:
            mock_read.return_value = {"IdList": ["12345"]}
            
            mock_efetch_handle = MagicMock()
            mock_efetch_handle.read.return_value = "Medline citation"
            mock_efetch.return_value = mock_efetch_handle

            agent = ResearchAgent()
            agent.run()

        # Check if files were created
        files = os.listdir(self.output_dir)
        self.assertTrue(len(files) >= 5) # One for each tool
        print(f"Created files: {files}")

if __name__ == "__main__":
    unittest.main()
