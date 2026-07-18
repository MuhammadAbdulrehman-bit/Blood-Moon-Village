from dataclasses import dataclass, field
from enum import Enum


class Phase(Enum):
    NIGHT = "night"
    CONFERENCE = "conference"
    DAY = "day"


class Role(Enum):
    WOLF = "wolf"
    DOCTOR = "doctor"
    SEER = "seer"
    VILLAGER = "villager"


class AgentStatus(Enum):
    ALIVE = "alive"
    DEAD = "dead"


@dataclass
class AgentState:
    name: str
    role: Role
    status: AgentStatus = AgentStatus.ALIVE
    room: str = "Hall"

    # role-specific counters
    saves_remaining: int = 0        # only meaningful for doctor, set to 2 at game start
    inspections_used: int = 0       # only meaningful for seer, tracked for research/logging
    
    action_history: list[str] = field(default_factory=list)

    def is_alive(self) -> bool:
        return self.status == AgentStatus.ALIVE

    def kill(self) -> None:
        self.status = AgentStatus.DEAD

    def revive(self) -> None:
        self.status = AgentStatus.ALIVE


@dataclass
class NightEvent:
    tick: int
    attacker: str
    victim: str
    room: str
    saved: bool = False


@dataclass
class GameState:
    # core agent registry
    agents: dict[str, AgentState] = field(default_factory=dict)
    current_phase: Phase = Phase.NIGHT
    current_tick: int = 0
    current_round: int = 1
    night_ticks: int = 5
    conference_ticks: int = 2
    day_ticks: int = 3
    teleport_available: bool = False
    teleport_holder: str | None = None
    active_night_event: NightEvent | None = None
    public_log: list[str] = field(default_factory=list)
    wolf_channel_log: list[str] = field(default_factory=list)
    deaths_this_round: list[str] = field(default_factory=list)
    game_over: bool = False
    winner: str | None = None

    # NEW — per-agent reasoning trail, not shown to other agents, only for observability
    reasoning_log: list[dict] = field(default_factory=list)
    # phase tracking
    current_phase: Phase = Phase.NIGHT
    current_tick: int = 0
    current_round: int = 1

    # tick limits per phase — tunable via config
    night_ticks: int = 5
    conference_ticks: int = 2
    day_ticks: int = 3

    # teleport mechanic
    teleport_available: bool = False
    teleport_holder: str | None = None

    # night event — populated when a kill happens mid-night
    active_night_event: NightEvent | None = None

    # game log — append-only record of everything that happened
    public_log: list[str] = field(default_factory=list)
    wolf_channel_log: list[str] = field(default_factory=list)

    # round-by-round death record for conference reveals
    deaths_this_round: list[str] = field(default_factory=list)

    # game over flag
    game_over: bool = False
    winner: str | None = None  # "wolves" or "village"

    def add_agent(self, name: str, role: Role, starting_room: str) -> None:
        state = AgentState(name=name, role=role, room=starting_room)
        if role == Role.DOCTOR:
            state.saves_remaining = 2
        self.agents[name] = state

    def get_agent(self, name: str) -> AgentState:
        if name not in self.agents:
            raise ValueError(f"Unknown agent: '{name}'")
        return self.agents[name]

    def living_agents(self) -> list[AgentState]:
        return [a for a in self.agents.values() if a.is_alive()]

    def living_names(self) -> list[str]:
        return [a.name for a in self.living_agents()]

    def dead_agents(self) -> list[AgentState]:
        return [a for a in self.agents.values() if not a.is_alive()]

    def agents_by_role(self, role: Role) -> list[AgentState]:
        return [a for a in self.agents.values() if a.role == role]

    def living_wolves(self) -> list[AgentState]:
        return [a for a in self.agents_by_role(Role.WOLF) if a.is_alive()]

    def living_villagers(self) -> list[AgentState]:
        return [
            a for a in self.living_agents()
            if a.role != Role.WOLF
        ]

    def positions(self) -> dict[str, str]:
        return {name: agent.room for name, agent in self.agents.items() if agent.is_alive()}

    def log_public(self, message: str) -> None:
        entry = f"[Round {self.current_round} | {self.current_phase.value} | Tick {self.current_tick}] {message}"
        self.public_log.append(entry)

    def log_wolf_channel(self, message: str) -> None:
        entry = f"[Round {self.current_round} | Tick {self.current_tick}] {message}"
        self.wolf_channel_log.append(entry)

    def advance_tick(self) -> None:
        self.current_tick += 1

    def set_phase(self, phase: Phase) -> None:
        self.current_phase = phase
        self.current_tick = 0

    def start_new_round(self) -> None:
        self.current_round += 1
        self.deaths_this_round = []
        self.active_night_event = None
        self.teleport_available = False
        self.teleport_holder = None
        self.set_phase(Phase.NIGHT)

    def log_reasoning(self, agent_name: str, tool_name: str, target: str | None,
                       message: str | None, raw_reasoning: str) -> None:
        self.reasoning_log.append({
            "round": self.current_round,
            "phase": self.current_phase.value,
            "tick": self.current_tick,
            "agent": agent_name,
            "tool_name": tool_name,
            "target": target,
            "message": message,
            "raw_reasoning": raw_reasoning,
        })    