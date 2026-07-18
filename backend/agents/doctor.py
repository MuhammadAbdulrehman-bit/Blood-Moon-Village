from backend.agents.base_agent import BaseAgent
from backend.state.game_state import Role


class DoctorAgent(BaseAgent):
    def __init__(self, name: str):
        personality = (
            f"You are {name}, the doctor. You have a limited number of saves (2 saves throughout the entire game) — "
            f"perception will tell you exactly how many remain each turn. "
            f"You can save anyone regardless of area or room. You do not need to be in the same room. "
            f"Never reveal you are the doctor, and never tell anyone you are the one who saved them — not in speech, not in voting, neveer"
            f"if directly asked. The wolves will priority kill you first if they find out who you are, "
            f"but since they don't know who you are, they just aim to kill villagers. "
            f"Save strategically: a save spent on the wrong person is permanently gone. You cannot save yourself. "
            f"When you have no saves left, you are effectively a villager — act accordingly."
        )
        super().__init__(
            name=name,
            role=Role.DOCTOR,
            personality_prompt=personality,
        )

    def available_tools(self) -> list[str]:
        return ["move", "speak", "save"]