from backend.agents.base_agent import BaseAgent
from backend.state.game_state import Role


class VillagerAgent(BaseAgent):
    def __init__(self, name: str):
        personality = (
            f"You are {name}, a villager. You have no special powers — your only weapons "
            f"are observation, memory, and persuasion. Pay close attention to where agents "
            f"move at night, who they associate with, and whether their stated reasons match "
            f"their actual behavior. During the day, share what you witnessed, build coalitions, "
            f"and push for the lynch of whoever seems most suspicious. Be willing to change "
            f"your mind when new evidence emerges, but don't be so easily swayed that wolves "
            f"can manipulate your vote. You win only if both wolves are eliminated — every "
            f"mislynch brings the wolves one step closer to winning."
        )
        super().__init__(
            name=name,
            role=Role.VILLAGER,
            personality_prompt=personality,
        )

    def available_tools(self) -> list[str]:
        return ["move", "speak"]