"""Agent loop — residents and sentinel.

Turn order, board access, objective injection, OpenRouter calls.
Residents act against the target; the sentinel does its own task and reports.

Status: not implemented.
"""

from .llm import LLM

class Agent:
    def __init__(self, name, sentinel=False):
        self.name = name
        self.memory = []
        self.client = LLM()
    
    def _use_tool(self, tool_name, *args, **kwargs):
        """Use a tool by name."""
        # Placeholder for tool usage logic
        pass
    
    def _build_messages(self):
        """Build messages to post to the board."""
        # Placeholder for message building logic
        pass
        
    def loop(self):
        """Main loop for the agent."""
        print(self.client.chat([{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "Hello!"}]))
        while True:
            # Placeholder for agent logic
            pass
    
if __name__ == "__main__":
    agent = Agent(name="Resident1")
    agent.loop()
