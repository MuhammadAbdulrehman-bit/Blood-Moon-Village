from backend.agents.base_agent import BaseAgent
from backend.state.game_state import Role


class WolfAgent(BaseAgent):
    def __init__(self, name: str, has_teleport: bool = False):
        personality = (
            f"You are {name}, a werewolf. You must appear cooperative and trustworthy "
            f"to the village while secretly coordinating with your fellow wolf to eliminate "
            f"villagers. Make sure no one doubts you. "
            f"Deflect suspicion onto others, build false alibis, and vote to lynch innocents during the day. "
            f"At night, actively use the 'wolf_communicate' tool to strategize with your partner. "
            f"DO NOT kill someone with a lot of people present! "
            f"You can strategize together: one wolf can convince some villagers to lead them into a room, "
            f"so that another wolf can come, corner an agent in a room, and kill them. "
            f"DO NOT use the 'kill' tool on the very first tick unless absolutely necessary; use early ticks to maneuver. "
            f"CRITICAL: The night only lasts for a maximum of 5 ticks! If you reach tick 3 or 4, you MUST coordinate and execute a kill with your partner using the 'kill' tool, or the night will end without a kill, which is disastrous for wolves!"
            f"Never reveal your true role — not even under direct accusation. "
            f"If accused, defend yourself calmly and redirect suspicion to someone else."
        )
        super().__init__(
            name=name,
            role=Role.WOLF,
            personality_prompt=personality,
        )
        self.has_teleport = has_teleport

    def available_tools(self) -> list[str]:
        tools = ["move", "speak", "wolf_communicate", "kill"]
        if self.has_teleport:
            tools.append("teleport")
        return tools

    def grant_teleport(self):
        # called by teleport_resolver when the nightly 15% roll succeeds
        # for this wolf — sets the flag so available_tools() exposes it
        self.has_teleport = True

    def revoke_teleport(self):
        # called by teleport_resolver at end of night to clean up,
        # whether or not the wolf used it — ensures it doesn't persist
        self.has_teleport = False