from dataclasses import dataclass, field


@dataclass
class BeliefState:
    owner: str
    suspicion: dict[str, float] = field(default_factory=dict)
    notes: dict[str, list[str]] = field(default_factory=dict)
    inactive: set[str] = field(default_factory=set)

    def init_suspicion(self, agent_names: list[str], default: float = 0.5) -> None:
        for name in agent_names:
            if name != self.owner:
                self.suspicion[name] = default
                self.notes[name] = []

    def get_suspicion(self, target: str) -> float:
        if target not in self.suspicion:
            raise ValueError(f"'{self.owner}' has no belief recorded about '{target}'")
        return self.suspicion[target]

    def set_suspicion(self, target: str, value: float) -> None:
        clamped = max(0.0, min(1.0, value))
        self.suspicion[target] = clamped

    def adjust_suspicion(self, target: str, delta: float) -> None:
        current = self.get_suspicion(target)
        self.set_suspicion(target, current + delta)

    def add_note(self, target: str, note: str) -> None:
        if target not in self.notes:
            self.notes[target] = []
        self.notes[target].append(note)

    def get_notes(self, target: str) -> list[str]:
        return self.notes.get(target, [])

    def mark_inactive(self, target: str) -> None:
        # target is dead — exclude from voting/suspicion targeting,
        # but suspicion score and notes are kept fully intact for historical reasoning
        self.inactive.add(target)

    def most_suspicious(self, exclude: list[str] | None = None) -> str | None:
        exclude = set(exclude or []) | self.inactive
        candidates = {
            name: score for name, score in self.suspicion.items()
            if name not in exclude
        }
        if not candidates:
            return None
        return max(candidates, key=candidates.get)


@dataclass
class BeliefRegistry:
    beliefs: dict[str, BeliefState] = field(default_factory=dict)

    def create_belief(self, owner: str, all_agent_names: list[str]) -> None:
        belief = BeliefState(owner=owner)
        belief.init_suspicion(all_agent_names)
        self.beliefs[owner] = belief

    def get(self, owner: str) -> BeliefState:
        if owner not in self.beliefs:
            raise ValueError(f"No belief state exists for '{owner}'")
        return self.beliefs[owner]

    def mark_agent_dead(self, dead_agent: str) -> None:
        for belief in self.beliefs.values():
            belief.mark_inactive(dead_agent)