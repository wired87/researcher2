from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseTool(ABC):
    """Abstract base class for all research tools."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def construct_query(self, requirements: Dict[str, Any]) -> Any:
        """
        Constructs the query in the format required by the tool's API.
        
        Args:
            requirements: A dictionary containing the requirements/parameters for the query.
        
        Returns:
            The constructed query object/string.
        """
        pass

    @abstractmethod
    def run(self, query: Any) -> Any:
        """
        Executes the tool with the given query.
        
        Args:
            query: The query to execute.
        
        Returns:
            The raw response from the tool.
        """
        pass

    @abstractmethod
    def process_response(self, response: Any) -> Dict[str, Any]:
        """
        Processes the raw response into a standardized format.
        
        Args:
            response: The raw response from the tool.
        
        Returns:
            A dictionary containing the processed data, including 'type' (file, json, text) and 'content'.
        """
        pass
