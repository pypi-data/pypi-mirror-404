from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

# ABC = Abstract Base Class. It means "You cannot use this class directly, 
# you must create a new class based on this template."

class BaseLLMProvider(ABC):
    """
    The blueprint for any AI model (OpenAI, Gemini, Claude).
    """
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """
        Every LLM must have a 'generate' function.
        We use **kwargs (keyword arguments) so in V2, if we want to add 
        'temperature' or 'top_p', we don't have to rewrite this line.
        """
        pass

class BaseMemoryStore(ABC):
    """
    The blueprint for memory (Neo4j, Mem0, Postgres).
    """

    @abstractmethod
    async def save(self, key: str, value: Dict[str, Any]) -> bool:
        """
        Save data. 'Dict[str, Any]' means a dictionary where keys are strings
        and values can be anything (text, numbers, lists).
        """
        pass

    @abstractmethod
    async def retrieve(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get data back. Returns a Dictionary or None if nothing is found.
        """
        pass