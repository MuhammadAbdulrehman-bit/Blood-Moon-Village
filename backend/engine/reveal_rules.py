from backend.state.game_state import GameState


def public_death_announcement(victim_name: str, room: str) -> str:
    # only fact the public log ever gets on a kill:
    # victim name and room — no killer, no role reveal
    return f"[DEATH] {victim_name} was found dead in the {room}."


def save_hint_for_wolves() -> str:
    # vague, unattributed, delivered only to wolf channel —
    # wolves know their kill failed, nothing more
    return "[WOLF CHANNEL] SYSTEM: Your target survived the night. Someone intervened."


def conference_entry_announcement(round_number: int) -> str:
    return f"[CONFERENCE] Round {round_number} conference begins. Discuss and vote."


def lynch_announcement(victim_name: str, role_name: str) -> str:
    # unlike a night kill, lynch DOES reveal role — village needs this feedback
    return f"[LYNCH] {victim_name} was lynched. They were a {role_name}."


def no_lynch_announcement() -> str:
    return "[LYNCH] The village could not reach a majority. Nobody was lynched."


def night_start_announcement(round_number: int) -> str:
    return f"[NIGHT] Round {round_number} night begins. Agents disperse."


def day_start_announcement(round_number: int) -> str:
    return f"[DAY] Round {round_number} day begins. Move freely."