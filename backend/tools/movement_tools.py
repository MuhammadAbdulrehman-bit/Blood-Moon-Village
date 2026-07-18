from backend.state.state_manager import StateManager
from backend.map.location_resolver import LocationResolver


def move(
    agent_name: str,
    target_room: str,
    state_manager: StateManager,
    location_resolver: LocationResolver,
) -> str:
    current_room = state_manager.game_state.agents[agent_name].room
    valid = location_resolver.valid_moves(current_room)

    if target_room not in valid:
        return (
            f"[INVALID] {agent_name} cannot move to '{target_room}' "
            f"from {current_room}. Valid moves: {', '.join(valid)}."
        )

    state_manager.move_agent(agent_name, target_room)
    return f"[MOVE] {agent_name} moved from {current_room} to {target_room}."