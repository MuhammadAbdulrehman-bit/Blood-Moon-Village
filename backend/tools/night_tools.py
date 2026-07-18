from backend.state.state_manager import StateManager
from backend.map.location_resolver import LocationResolver
from backend.state.game_state import GameState


def kill_same_room(
    killer_name: str,
    target_name: str,
    state_manager: StateManager,
    game_state: GameState,
) -> str:
    killer_room = game_state.agents[killer_name].room
    target = game_state.agents.get(target_name)

    if not target or not target.is_alive:
        return f"[INVALID] Kill failed — {target_name} is not a valid target."
    if target.room != killer_room:
        return f"[INVALID] Kill failed — {target_name} is not in the same room."

    return state_manager.attempt_kill(killer_name=killer_name, target_name=target_name)


def teleport(
    wolf_name: str,
    target_name: str,
    state_manager: StateManager,
    game_state: GameState,
) -> str:
    wolf_room = game_state.agents[wolf_name].room
    target = game_state.agents.get(target_name)

    if not target or not target.is_alive:
        return f"[INVALID] Teleport failed — {target_name} is not a valid target."

    state_manager.teleport_agent(target_name=target_name, destination=wolf_room)
    return f"[TELEPORT] {target_name} was pulled into {wolf_room}."


def save(
    doctor_name: str,
    target_name: str,
    state_manager: StateManager,
    game_state: GameState,
) -> str:
    doctor = game_state.agents[doctor_name]

    if doctor.saves_remaining <= 0:
        return f"[INVALID] Save failed — {doctor_name} has no saves remaining."
    if target_name == doctor_name:
        return f"[INVALID] Save failed — doctor cannot save themselves."

    target = game_state.agents.get(target_name)
    if not target or not target.is_alive:
        return f"[INVALID] Save failed — {target_name} is not a valid target."
    if target.room != doctor.room:
        return f"[INVALID] Save failed — {target_name} is not in the same room."

    return state_manager.attempt_save(doctor_name=doctor_name, target_name=target_name)


def inspect(
    seer_name: str,
    target_name: str,
    game_state: GameState,
) -> str:
    seer_room = game_state.agents[seer_name].room
    target = game_state.agents.get(target_name)

    if not target or not target.is_alive:
        return f"[INVALID] Inspect failed — {target_name} is not a valid target."
    if target.room != seer_room:
        return f"[INVALID] Inspect failed — {target_name} is not in the same room."

    return f"[INSPECT] {seer_name} inspected {target_name}: they are a {target.role.value}."