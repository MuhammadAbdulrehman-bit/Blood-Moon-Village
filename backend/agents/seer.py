from backend.agents.base_agent import BaseAgent
from backend.state.game_state import Role


class SeerAgent(BaseAgent):
    def __init__(self, name: str):
        personality = (
            f"You are {name}, the seer. Once per night you may inspect any agent in the same room as you to get their true role. "
            f"Perception will tell you when inspect is available and who is valid to inspect. "
            f"This does not protect you against wolves! However, in a room of 2 or more agents, you might be safe "
            f"since wolves avoid killing anyone when there are multiple people present. "
            f"Guard your information carefully: revealing yourself as the seer makes you "
            f"the wolves' highest-priority target the following night. "
            f"Use your knowledge to steer votes during the day without exposing yourself — "
            f"plant suspicion indirectly, corroborate others' accusations, build a paper trail "
            f"before you ever claim seer. Only reveal your role as a last resort when the "
            f"village is about to lynch an innocent and you have confirmed wolf knowledge. "
        )
        super().__init__(
            name=name,
            role=Role.SEER,
            personality_prompt=personality,
        )
        self.inspected_this_night = False
        self.inspection_log: dict[str, Role] = {}

    def available_tools(self) -> list[str]:
        tools = ["move", "speak"]
        if not self.inspected_this_night:
            tools.append("inspect")
        return tools

    def record_inspection(self, target_name: str, role: Role):
        # called by night_resolver after a successful inspect tool call —
        # stores the confirmed role so perception.py can inject it into
        # future prompts as accumulated seer knowledge
        self.inspection_log[target_name] = role
        self.inspected_this_night = True

    def reset_night(self):
        # called by phase_engine at the start of each new night —
        # clears the flag so inspect becomes available again
        self.inspected_this_night = False