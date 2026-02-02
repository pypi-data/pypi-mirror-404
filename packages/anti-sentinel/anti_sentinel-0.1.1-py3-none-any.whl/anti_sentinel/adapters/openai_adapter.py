import os
from typing import Any, Dict, List
from openai import AsyncOpenAI
from sentinel_core.interfaces import BaseLLMProvider

class OpenAIAdapter(BaseLLMProvider):
    """
    A Universal Adapter that uses the OpenAI SDK.
    It can connect to OpenAI, Groq, DeepSeek, Ollama, or any 'OpenAI-Compatible' endpoint.
    """

    def __init__(self, config: Dict[str, Any]):
        # 1. Fetch credentials from Config or Environment
        # We prioritize the config file, then fallback to env vars
        self.api_key = config.get("api_key") or os.getenv("OPENAI_API_KEY")
        self.base_url = config.get("base_url") or os.getenv("OPENAI_BASE_URL")
        
        # 2. Defaults
        self.default_model = config.get("model", "gpt-4o")
        self.default_temp = config.get("temperature", 0.7)

        if not self.api_key:
            # Some local providers (like Ollama) don't require a key, so we use a dummy one
            if "localhost" in str(self.base_url) or "127.0.0.1" in str(self.base_url):
                self.api_key = "dummy-key"
            else:
                raise ValueError("❌ API Key is missing! Set it in sentinel.yaml or .env")

        # 3. Initialize the Client with the custom Base URL
        print(f"🔌 Connecting to LLM via OpenAI SDK...")
        print(f"   ➡ Target: {self.base_url if self.base_url else 'Official OpenAI API'}")
        print(f"   ➡ Model:  {self.default_model}")

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url # <--- The Magic Parameter
        )

    async def generate(self, prompt: Any, tools: List[Dict] = None, **kwargs) -> Any:
        """
        Generates text, potentially using tools.
        Returns either a String (text response) or a Dict (tool call request).
        """
        model = kwargs.get("model") or self.default_model
        temperature = kwargs.get("temperature") or self.default_temp

        messages = prompt if isinstance(prompt, list) else [
            {"role": "system", "content": "You are a helpful agent."},
            {"role": "user", "content": prompt}
        ]

        try:
            # We pass the 'tools' list to OpenAI/Gemini
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None
            )
            
            response_message = response.choices[0].message

            # CASE A: The LLM wants to call a tool
            if response_message.tool_calls:
                return response_message.tool_calls  # We return the list of tool requests

            # CASE B: Standard text response
            return response_message.content

        except Exception as e:
            print(f"⚠️ LLM Error: {e}")
            return f"Error: {str(e)}"