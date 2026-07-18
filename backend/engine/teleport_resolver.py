import random
from backend.state.game_state import GameState, Role
from backend.state.state_manager import StateManager
from backend.agents.wolf import WolfAgent


class TeleportResolver:
    def __init__(self, state_manager: StateManager, teleport_probability: float = 0.15):
        self.state_manager = state_manager
        self.teleport_probability = teleport_probability

    def roll_and_grant(
        self,
        wolf_agents: dict[str, WolfAgent],
        game_state: GameState,
    ) -> str | None:
        # called once at the start of each night before ticks begin
        # only one wolf per night can receive teleport
        # returns the name of the wolf granted teleport, or None

        living_wolves = [
            name for name, agent in wolf_agents.items()
            if game_state.agents[name].is_alive()
        ]

        if not living_wolves:
            return None

        if random.random() > self.teleport_probability:
            return None

        chosen_wolf = random.choice(living_wolves)
        wolf_agents[chosen_wolf].grant_teleport()
        return chosen_wolf

    def revoke_all(self, wolf_agents: dict[str, WolfAgent]) -> None:
        # called at end of night regardless of whether teleport was used
        for agent in wolf_agents.values():
            agent.revoke_teleport()

    def resolve_teleport_action(
        self,
        wolf_name: str,
        target_name: str,
        game_state: GameState,
    ) -> str:
        target = game_state.agents.get(target_name)

        if not target:
            return f"[INVALID] Teleport failed — unknown target '{target_name}'."
        if not target.is_alive():
            return f"[INVALID] Teleport failed — {target_name} is already dead."
        if target.role == Role.WOLF:
            return f"[INVALID] Teleport failed — cannot teleport another wolf."

        wolf_room = game_state.agents[wolf_name].room
        self.state_manager.teleport_agent(agent_name=target_name, target_room=wolf_room)

        # public log gets zero information about this —
        # victim just finds themselves in a new room with no explanation
        return f"[TELEPORT] {target_name} was moved to {wolf_room} by unseen means."