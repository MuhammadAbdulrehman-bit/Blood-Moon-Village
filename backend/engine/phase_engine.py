from backend.state.game_state import GameState, Phase
from backend.state.state_manager import StateManager
from backend.agents.base_agent import BaseAgent, AgentAction
from backend.agents.wolf import WolfAgent
from backend.agents.doctor import DoctorAgent
from backend.agents.seer import SeerAgent
from backend.channels.wolf_channel import WolfChannel
from backend.tools.tool_registry import ToolRegistry
from backend.engine.night_resolver import NightResolver
from backend.engine.teleport_resolver import TeleportResolver
from backend.engine.day_resolver import DayResolver
from backend.engine.win_condition import check_win
from backend.engine.reveal_rules import (
    night_start_announcement,
    day_start_announcement,
    conference_entry_announcement,
)
from backend.agents.perception import build_perception
from backend.agents.llm_client import LLMClient


class PhaseEngine:
    def __init__(
        self,
        game_state: GameState,
        state_manager: StateManager,
        agents: dict[str, BaseAgent],
        wolf_channel: WolfChannel,
        tool_registry: ToolRegistry,
        llm_clients: dict[str, LLMClient],
        night_ticks: int,
        conference_ticks: int,
        day_ticks: int,
        teleport_probability: float,
    ):
        self.game_state = game_state
        self.state_manager = state_manager
        self.agents = agents
        self.wolf_channel = wolf_channel
        self.tool_registry = tool_registry
        self.llm_clients = llm_clients
        self.night_ticks = night_ticks
        self.conference_ticks = conference_ticks
        self.day_ticks = day_ticks

        # pulled from state_manager — not constructed independently
        self.belief_registry = state_manager.beliefs
        self.location_resolver = state_manager.get_resolver()

        # role-typed subsets for resolvers that need them
        self.wolf_agents = {n: a for n, a in agents.items() if isinstance(a, WolfAgent)}
        self.doctor_agents = {n: a for n, a in agents.items() if isinstance(a, DoctorAgent)}
        self.seer_agents = {n: a for n, a in agents.items() if isinstance(a, SeerAgent)}

        # resolvers
        self.night_resolver = NightResolver(state_manager, tool_registry, wolf_channel)
        self.teleport_resolver = TeleportResolver(state_manager, teleport_probability)
        self.day_resolver = DayResolver(state_manager, tool_registry)

        self.winner: str | None = None

    # ------------------------------------------------------------------ #
    #  Top-level game loop                                                 #
    # ------------------------------------------------------------------ #

    def run_game(self) -> str:
        while not self.winner:
            self._run_night()
            if self._check_win():
                break
            self._run_conference()
            if self._check_win():
                break
            self._run_day()
            if self._check_win():
                break
            self.game_state.start_new_round()

        result = f"[GAME OVER] {self.winner.upper()} WIN."
        self.game_state.public_log.append(result)
        return result

    # ------------------------------------------------------------------ #
    #  Phase runners                                                       #
    # ------------------------------------------------------------------ #

    def run_current_phase_to_completion(self):
        start_phase = self.game_state.current_phase
        while self.game_state.current_phase == start_phase and not self.winner:
            self.advance_one_tick()

    def advance_one_tick(self):
        if self.winner:
            return

        phase = self.game_state.current_phase
        tick = self.game_state.current_tick

        if phase == Phase.NIGHT:
            if tick == 0:
                ann = night_start_announcement(self.game_state.current_round)
                self.game_state.public_log.append(ann)
                granted = self.teleport_resolver.roll_and_grant(self.wolf_agents, self.game_state)
                if granted:
                    self.wolf_channel.post("SYSTEM", f"Teleport granted to {granted} this night.")
                for seer in self.seer_agents.values():
                    seer.reset_night()

            tick_actions = self._collect_actions()

            results = self.night_resolver.resolve_tick(
                tick_actions=tick_actions,
                game_state=self.game_state,
                seer_agents=self.seer_agents,
                doctor_agents=self.doctor_agents,
            )
            for r in results:
                if not r.startswith(("[INVALID]", "[SAVE_VALID]", "[KILL_VALID]", "[SAVE]", "[DEATH CONFIRMED]")):
                    self.game_state.public_log.append(r)

            end_night = False
            if any("[DEATH CONFIRMED]" in r or "[SAVE]" in r for r in results):
                end_night = True
                self._check_win()

            self.game_state.advance_tick()
            if self.game_state.current_tick >= self.night_ticks or end_night:
                self.teleport_resolver.revoke_all(self.wolf_agents)
                if not self.winner:
                    self.game_state.set_phase(Phase.CONFERENCE)

        elif phase == Phase.CONFERENCE:
            if tick == 0:
                ann = conference_entry_announcement(self.game_state.current_round)
                self.game_state.public_log.append(ann)

            tick_actions = self._collect_actions()
            results = self.day_resolver.resolve_tick(
                tick_actions=tick_actions,
                game_state=self.game_state,
            )
            for r in results:
                if not r.startswith(("[INVALID]", "[SAVE_VALID]", "[KILL_VALID]", "[SAVE]", "[DEATH CONFIRMED]")):
                    self.game_state.public_log.append(r)

            self.game_state.advance_tick()
            if self.game_state.current_tick >= self.conference_ticks:
                lynch_result = self.day_resolver.resolve_vote(self.game_state)
                self.game_state.public_log.append(lynch_result)
                self._check_win()
                if not self.winner:
                    self.game_state.set_phase(Phase.DAY)

        elif phase == Phase.DAY:
            if tick == 0:
                ann = day_start_announcement(self.game_state.current_round)
                self.game_state.public_log.append(ann)

            tick_actions = self._collect_actions()
            results = self.day_resolver.resolve_tick(
                tick_actions=tick_actions,
                game_state=self.game_state,
            )
            for r in results:
                if not r.startswith(("[INVALID]", "[SAVE_VALID]", "[KILL_VALID]", "[SAVE]", "[DEATH CONFIRMED]")):
                    self.game_state.public_log.append(r)

            self.game_state.advance_tick()
            if self.game_state.current_tick >= self.day_ticks:
                self._check_win()
                if not self.winner:
                    self.game_state.start_new_round()

    # ------------------------------------------------------------------ #
    #  Action collection                                                   #
    # ------------------------------------------------------------------ #

    def _collect_actions(self) -> dict[str, AgentAction]:
        from backend.engine.state_graph import build_tick_graph
        
        graph = build_tick_graph(self)
        
        initial_state = {
            "agent_names": list(self.agents.keys()),
            "current_index": 0,
            "tick_actions": {},
            "tick_logs": [],
        }
        
        final_state = graph.invoke(initial_state)
        return final_state.get("tick_actions", {})

    # ------------------------------------------------------------------ #
    #  Win condition                                                       #
    # ------------------------------------------------------------------ #

    def _check_win(self) -> bool:
            result = check_win(self.game_state)
            if result:
                self.winner = result
                return True
            return False