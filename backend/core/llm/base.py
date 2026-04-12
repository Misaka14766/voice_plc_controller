from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class LLMResponse:
    content: str
    tool_calls: Optional[List[Dict]] = None

class BaseLLM(ABC):
    @abstractmethod
    async def generate(self, messages: List[Dict], tools: Optional[List[Dict]] = None) -> LLMResponse:
        pass