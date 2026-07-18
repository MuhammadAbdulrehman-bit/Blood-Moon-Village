from dataclasses import dataclass, field
from backend.state.game_state import GameState


@dataclass
class WolfChannel:
    # the wolves' private communication line —
    # also the only delivery point for the vague doctor-save hint
    # neither of these ever touches the public log
    messages: list[str] = field(default_factory=list)

    def post(self, sender: str, content: str) -> None:
        # wolves writing to each other during night ticks
        entry = f"[WOLF CHANNEL] {sender}: {content}"
        self.messages.append(entry)

    def post_save_hint(self) -> None:
        # called by state_manager after a successful doctor save —
        # deliberately vague: no room, no doctor identity, no victim name
        # the wolves know their target survived, nothing more
        hint = "[WOLF CHANNEL] SYSTEM: Your target survived the night. Someone intervened."
        self.messages.append(hint)

    def get_recent(self, n: int = 10) -> list[str]:
        # perception.py calls this to inject wolf channel context —
        # capped so it doesn't bloat the wolf's prompt
        return self.messages[-n:]

    def get_all(self) -> list[str]:
        # used by logs.py router for full transcript access post-game
        return list(self.messages)

    def clear(self) -> None:
        # not used in normal play — available for testing/reset scenarios
        self.messages.clear()