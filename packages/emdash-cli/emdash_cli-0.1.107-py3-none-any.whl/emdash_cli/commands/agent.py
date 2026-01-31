"""Agent CLI commands - backward compatibility module.

This file re-exports from the refactored agent/ package for backward compatibility.
The actual implementation is now in agent/ subdirectory.
"""

# Re-export the agent click group and commands
from .agent import agent, agent_code

__all__ = ["agent", "agent_code"]
