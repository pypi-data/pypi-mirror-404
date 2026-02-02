import json
from typing import List, Dict, Any, Optional, Callable
from anti_sentinel.container import ServiceContainer
from anti_sentinel.tools import Tool

class BaseAgent:
    def __init__(self, name: str = "Agent", model: Optional[str] = None, user_id: str = "default"):
        self.name = name
        self.user_id = user_id
        self.model = model 
        
        container = ServiceContainer.get_instance()
        self.llm = container.get_llm()
        self.memory = container.get_memory()
        
        self.history: List[Dict[str, Any]] = []
        self.tools: Dict[str, Tool] = {}  # Registry of available tools
        self._set_system_prompt()

    def register_tool(self, func: Callable):
        """
        Give this agent a new ability.
        """
        tool = Tool(func)
        self.tools[tool.name] = tool
        print(f"🛠️ Agent '{self.name}' equipped with tool: {tool.name}")

    def _set_system_prompt(self, context_notes: List[str] = None):
        base_prompt = f"You are {self.name}. Use your tools when needed."
        if context_notes:
            memory_block = "\n".join([f"- {note}" for note in context_notes])
            base_prompt += f"\n\nContext from Memory:\n{memory_block}"
        self.history = [{"role": "system", "content": base_prompt}]

    async def think(self, user_input: str) -> str:
        # 1. Recall & Setup
        if self.memory:
            mems = await self.memory.retrieve(user_input, user_id=self.user_id)
            if mems: self._set_system_prompt(context_notes=mems)

        self.history.append({"role": "user", "content": user_input})

        # 2. Get Tools List for the LLM
        tool_schemas = [t.schema for t in self.tools.values()]

        # 3. LLM Interaction Loop
        response = await self.llm.generate(
            self.history, 
            model=self.model,
            tools=tool_schemas
        )

        # 4. Handle Tool Calls
        # If response is NOT a string, it means it's a list of tool requests
        if not isinstance(response, str):
            tool_calls = response
            
            # Append the LLM's "Thought" (Request to call tool) to history
            self.history.append({
                "role": "assistant",
                "content": None,
                "tool_calls": tool_calls
            })

            # Execute each requested tool
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                print(f"🤖 Agent is using tool: {function_name}({arguments})")

                if function_name in self.tools:
                    # Run the python code
                    result = self.tools[function_name].execute(**arguments)
                    
                    # Feed result back to LLM
                    self.history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": str(result)
                    })
                else:
                    print(f"❌ Error: Tool {function_name} not found.")

            # 5. Final Answer (LLM sees tool results and answers user)
            final_response = await self.llm.generate(self.history, model=self.model)
            self.history.append({"role": "assistant", "content": final_response})
            return final_response
        
        # If no tool called, just return the text
        self.history.append({"role": "assistant", "content": response})
        return response