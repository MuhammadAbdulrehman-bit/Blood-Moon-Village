from dataclasses import dataclass, field
from backend.state.belief_state import BeliefState
from backend.state.game_state import Role


@dataclass
class AgentAction:
    # the standardized shape every agent decision collapses into,
    # regardless of role, so the engine can handle them uniformly
    tool_name: str          # e.g. "move", "speak", "kill", "save", "inspect", "vote_lynch"
    target: str | None      # room name, agent name, or None for tools with no target
    message: str | None     # spoken dialogue text, if the action includes speech
    raw_reasoning: str      # the LLM's full response text, kept for logging/debugging


class BaseAgent:
    def __init__(self, name: str, role: Role, personality_prompt: str):
        self.name = name
        self.role = role
        self.personality_prompt = personality_prompt

    def available_tools(self) -> list[str]:
        # Subclasses (Wolf, Doctor, Seer, Villager) override this
        # to return their role-specific tool list. Base agent only
        # knows about the universal tools every role shares.
        return ["move", "speak"]

    def build_system_prompt(self, game_context: str, override_tools: list[str] = None) -> str:
        # Combines personality with current game state context.
        # game_context is built by perception.py, passed in here —
        # this method just assembles the final prompt string.
        tools = override_tools if override_tools is not None else self.available_tools()
        tools_description = ", ".join(tools)
        return (
            f"You are {self.name}, playing a social deduction game.\n"
            f"{self.personality_prompt}\n\n"
            f"Current situation:\n{game_context}\n\n"
            f"Tools available to you this turn: {tools_description}\n"
            f"You must choose exactly one tool to use this turn."
        )

    def decide_action(self, game_context: str, llm_client, override_tools: list[str] = None) -> AgentAction:
        # llm_client is injected rather than imported directly here —
        # this keeps base_agent ignorant of HOW the LLM call actually
        # happens (which API, which key), it just knows it can ask
        # for a decision and get an AgentAction back.
        system_prompt = self.build_system_prompt(game_context, override_tools)
        return llm_client.get_agent_action(
            system_prompt=system_prompt,
            available_tools=override_tools if override_tools is not None else self.available_tools(),
        )

    def __repr__(self) -> str:
        return f"<{self.role.value.capitalize()}: {self.name}>"