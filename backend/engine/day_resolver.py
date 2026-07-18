from collections import Counter
from backend.state.game_state import GameState, Phase
from backend.state.state_manager import StateManager
from backend.agents.base_agent import AgentAction
from backend.tools.tool_registry import ToolRegistry
from backend.engine.reveal_rules import lynch_announcement, no_lynch_announcement


class DayResolver:
    def __init__(self, state_manager: StateManager, tool_registry: ToolRegistry):
        self.state_manager = state_manager
        self.tool_registry = tool_registry
        self.votes: dict[str, str] = {}  # voter → target

    def resolve_tick(
        self,
        tick_actions: dict[str, AgentAction],
        game_state: GameState,
    ) -> list[str]:
        results = []

        for agent_name, action in tick_actions.items():
            if not game_state.agents[agent_name].is_alive():
                continue

            if action.tool_name == "vote_lynch":
                if action.target:
                    self.votes[agent_name] = action.target
                result = self.tool_registry.execute(agent_name, action, game_state)
                results.append(result)
                continue

            result = self.tool_registry.execute(agent_name, action, game_state)
            results.append(result)

        return results

    def resolve_vote(self, game_state: GameState) -> str:
        # called once at end of conference phase after all vote ticks complete
        # tallies votes, applies lynch if majority reached, resets vote state
        if not self.votes:
            announcement = no_lynch_announcement()
            self._reset_votes()
            return announcement

        alive_count = sum(1 for a in game_state.agents.values() if a.is_alive())
        majority = (alive_count // 2) + 1

        tally = Counter(self.votes.values())
        top_target, top_votes = tally.most_common(1)[0]

        if top_votes < majority:
            announcement = no_lynch_announcement()
            self._reset_votes()
            return announcement

        # majority reached — lynch the target
        target_agent = game_state.agents[top_target]
        role_name = target_agent.role.value
        self.state_manager.lynch_agent(top_target)

        announcement = lynch_announcement(top_target, role_name)
        self._reset_votes()
        return announcement

    def _reset_votes(self):
        self.votes.clear()