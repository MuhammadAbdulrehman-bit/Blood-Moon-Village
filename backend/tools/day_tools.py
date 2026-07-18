from backend.state.game_state import GameState


def speak(agent_name: str, message: str, game_state: GameState) -> str:
    room = game_state.agents[agent_name].room
    entry = f"[SPEAK] {agent_name} (in {room}): {message}"
    game_state.public_log.append(entry)
    return entry


def accuse(agent_name: str, target_name: str, reason: str, game_state: GameState) -> str:
    if target_name not in game_state.agents:
        return f"[INVALID] {agent_name} accused unknown agent '{target_name}'."
    entry = f"[ACCUSE] {agent_name} accuses {target_name}. Reason: {reason}"
    game_state.public_log.append(entry)
    return entry


def vote_lynch(voter_name: str, target_name: str, game_state: GameState) -> str:
    if target_name not in game_state.agents:
        return f"[INVALID] {voter_name} voted for unknown agent '{target_name}'."
    if not game_state.agents[target_name].is_alive:
        return f"[INVALID] {voter_name} voted for dead agent '{target_name}'."
    entry = f"[VOTE] {voter_name} votes to lynch {target_name}."
    game_state.public_log.append(entry)
    return entry


def defend_self(agent_name: str, message: str, game_state: GameState) -> str:
    entry = f"[DEFEND] {agent_name}: {message}"
    game_state.public_log.append(entry)
    return entry