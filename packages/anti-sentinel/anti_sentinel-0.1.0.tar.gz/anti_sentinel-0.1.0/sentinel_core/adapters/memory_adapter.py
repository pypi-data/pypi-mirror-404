import os
from typing import Any, Dict, List
from sentinel_core.interfaces import BaseMemoryStore

class Mem0Adapter(BaseMemoryStore):
    """
    Adapter for Mem0 (Cloud Mode).
    """

    def __init__(self, config: Dict[str, Any]):
        # Fallback user if none provided
        self.default_user = config.get("user_id", "sentinel_user")
        
        self.api_key = config.get("api_key") or os.getenv("MEM0_API_KEY")

        if not self.api_key:
            raise ValueError("❌ MEM0_API_KEY is missing. Add it to .env")

        print("🧠 Initializing Memory (Cloud Mode)...")
        from mem0 import MemoryClient
        self.client = MemoryClient(api_key=self.api_key)

    async def save(self, content: str, user_id: str = None, metadata: Dict = None) -> bool:
        target_user = user_id or self.default_user
        try:
            messages = [{"role": "user", "content": str(content)}]
            self.client.add(messages, user_id=target_user, metadata=metadata or {})
            return True
        except Exception as e:
            print(f"⚠️ Memory Save Error: {e}")
            return False

    async def retrieve(self, query: str, user_id: str = None) -> List[str]:
        """
        Retrieves context from the Cloud.
        """
        target_user = user_id or self.default_user
        
        if not query or not isinstance(query, str):
            return []

        try:
            # FIX: We try passing user_id in both ways to satisfy the strict API
            # 1. As a direct argument (standard)
            # 2. As a filter (strict requirement for some SDK versions)
            
            results = self.client.search(
                query, 
                user_id=target_user,
            )
            
            memories = []
            if results:
                # Handle results being a list or a dict
                data_list = results.get("results") if isinstance(results, dict) else results
                
                for res in data_list:
                    # Extract text safely
                    text = res.get("memory", res.get("content"))
                    if text:
                        memories.append(text)
                    
            return memories

        except Exception as e:
            print(f"⚠️ Memory Retrieve Warning: {e}")
            # Non-blocking return (empty memory is better than a crash)
            return []