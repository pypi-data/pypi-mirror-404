from typing import Dict, Any
import os
from .interfaces import BaseLLMProvider, BaseMemoryStore

SUPPORTED_LLM_PROVIDERS = ["openai", "ollama", "groq", "deepseek", "gemini", "claude"]

class ServiceContainer:
    _instance = None
    
    def __init__(self):
        self.services: Dict[str, Any] = {}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ServiceContainer()
        return cls._instance

    def register_llm(self, provider: BaseLLMProvider):
        self.services['llm'] = provider

    def register_memory(self, store: BaseMemoryStore):
        self.services['memory'] = store

    def get_llm(self) -> BaseLLMProvider:
        return self.services.get('llm')

    def get_memory(self) -> BaseMemoryStore:
        return self.services.get('memory')

    def register_provider_by_config(self, config_data: dict):
        """
        Determines which adapter to load based on the YAML config.
        """
        llm_config = config_data.get("llm", {})
        provider_type = llm_config.get("provider", "openai")
        
        # LOGIC: Current support is mainly via the OpenAI Adapter
        # because it is the industry standard for connection.
        if provider_type in SUPPORTED_LLM_PROVIDERS:
            from .adapters.openai_adapter import OpenAIAdapter
            
            # We pass the whole config section so the adapter can extract what it needs
            adapter = OpenAIAdapter(llm_config)
            self.register_llm(adapter)
            
        else:
            print(f"⚠️ Warning: Unknown LLM provider '{provider_type}'")

    
    # New method to register memory provider
    def register_memory_by_config(self, config_data: dict):
        """
        Loads the memory provider.
        """
        mem_config = config_data.get("memory", {})
        provider = mem_config.get("provider", "mem0")
        
        if provider == "mem0":
            from .adapters.memory_adapter import Mem0Adapter
            adapter = Mem0Adapter(mem_config)
            self.register_memory(adapter)
            print(f"💾 Connected to Memory: Mem0")
        else:
            print("⚠️ No valid memory provider found.")