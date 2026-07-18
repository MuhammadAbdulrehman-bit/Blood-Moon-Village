from backend.state.game_state import GameState, Role


def check_win(game_state: GameState) -> str | None:
    # returns "wolves", "village", or None if game continues
    # called after every phase resolution, not mid-tick

    alive = [a for a in game_state.agents.values() if a.is_alive()]
    wolves_alive = [a for a in alive if a.role == Role.WOLF]
    villagers_alive = [a for a in alive if a.role != Role.WOLF]

    if len(wolves_alive) == 0:
        return "village"

    # wolves win when they equal or outnumber non-wolf agents
    if len(wolves_alive) >= len(villagers_alive):
        return "wolves"

    return None