from typing import List, Any, Callable, Union
from sentinel_core.agents.base import BaseAgent

class Workflow:
    """
    Chains multiple agents or functions together.
    Output of Step 1 -> Input of Step 2.
    """
    def __init__(self, name: str):
        self.name = name
        self.steps: List[Union[BaseAgent, Callable]] = []

    def add_step(self, step: Union[BaseAgent, Callable]):
        """
        Add an Agent or a Function to the pipeline.
        """
        self.steps.append(step)
        return self # Allow chaining: wf.add_step(a).add_step(b)

    async def run(self, initial_input: str) -> str:
        """
        Executes the pipeline sequentially.
        """
        print(f"🔄 Starting Workflow: {self.name}")
        current_data = initial_input

        for i, step in enumerate(self.steps):
            print(f"   ➡ Step {i+1} starting...")
            
            # CASE A: It's an Agent
            if isinstance(step, BaseAgent):
                # Agents use the 'think' method
                current_data = await step.think(current_data)
                
            # CASE B: It's a standard Function
            elif callable(step):
                # Check if it's async or sync
                if hasattr(step, '__call__') and  step.__code__.co_flags & 0x80: # Check for coroutine
                     current_data = await step(current_data)
                else:
                    current_data = step(current_data)
            
            print(f"   ✅ Step {i+1} complete.")

        print(f"🏁 Workflow {self.name} finished.")
        return current_data