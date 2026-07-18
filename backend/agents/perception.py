from __future__ import annotations

from typing import TYPE_CHECKING

from backend.state.game_state import GameState, Role, Phase
from backend.state.belief_state import BeliefRegistry
from backend.map.location_resolver import LocationResolver

if TYPE_CHECKING:
    from backend.agents.seer import SeerAgent


def build_perception(
    agent_name: str,
    game_state: GameState,
    belief_registry: BeliefRegistry,
    location_resolver: LocationResolver,
    seer_agent: "SeerAgent | None" = None,
    tick_logs: list[str] | None = None,
) -> str:
    agent = game_state.agents[agent_name]
    role = agent.role
    current_room = agent.room
    blocks = []

    # --- identity block ---
    blocks.append(f"You are {agent_name} ({role.value}).")
    blocks.append(
        f"Current phase: {game_state.current_phase.value}, "
        f"tick {game_state.current_tick}, round {game_state.current_round}."
    )

    # --- spatial block ---
    # --- spatial block ---
    roommates = location_resolver.agents_in_room(current_room)
    roommates = [r for r in roommates if r != agent_name]
    neighbors = location_resolver.valid_moves(agent_name)

    blocks.append(f"You are in the {current_room}.")
    if roommates:
        blocks.append(f"Also in this room: {', '.join(roommates)}.")
    else:
        blocks.append("You are alone in this room.")
    blocks.append(f"You may move to: {', '.join(neighbors)} (staying in {current_room} is also valid).")

    # --- role-specific block ---
    if role == Role.WOLF:
        partner = _wolf_partner(agent_name, game_state)
        wolf_channel_lines = game_state.wolf_channel_log[-10:]  # last 10 entries only
        blocks.append(f"Your wolf partner is: {partner}.")
        if wolf_channel_lines:
            blocks.append("Recent wolf channel messages:")
            for line in wolf_channel_lines:
                blocks.append(f"  {line}")
        else:
            blocks.append("No messages on the wolf channel yet.")

    elif role == Role.DOCTOR:
        saves_remaining = agent.saves_remaining
        blocks.append(f"You have {saves_remaining} save(s) remaining.")
        if saves_remaining == 0:
            blocks.append("You have no saves left. You cannot use the save tool.")

    elif role == Role.SEER:
        if seer_agent and seer_agent.inspection_log:
            blocks.append("Your confirmed inspection results so far:")
            for name, inspected_role in seer_agent.inspection_log.items():
                blocks.append(f"  {name}: {inspected_role.value}")
        else:
            blocks.append("You have not successfully inspected anyone yet.")

        # tell the seer who they can actually inspect right now
        if seer_agent and not seer_agent.inspected_this_night and game_state.current_phase == Phase.NIGHT:
            inspectable = [
                r for r in game_state.agents
                if game_state.agents[r].is_alive() 
                and r != agent_name 
                and game_state.agents[r].room == current_room
            ]
            if inspectable:
                blocks.append(f"You may inspect one of: {', '.join(inspectable)}.")
            else:
                blocks.append("No valid inspect targets.")

    # --- belief state block ---
    # --- belief state block ---
    belief = belief_registry.get(agent_name)
    if belief and belief.suspicion:
        active_agents = {
            name for name, a in game_state.agents.items()
            if a.is_alive() and name != agent_name
        }
        scored = {
            name: score
            for name, score in belief.suspicion.items()
            if name in active_agents and name not in belief.inactive
        }
        if scored:
            sorted_suspects = sorted(scored.items(), key=lambda x: x[1], reverse=True)
            blocks.append("Your current suspicion levels (0.0 = innocent, 1.0 = certain wolf):")
            for name, score in sorted_suspects:
                notes = belief.get_notes(name)
                note_str = f" — {'; '.join(notes)}" if notes else ""
                blocks.append(f"  {name}: {score:.2f}{note_str}")

    # --- public log block ---
    recent_log = game_state.public_log[-15:]
    if recent_log:
        blocks.append("Recent public events (from previous ticks):")
        for entry in recent_log:
            blocks.append(f"  {entry}")

    if tick_logs:
        blocks.append("Events that happened so far THIS tick:")
        for entry in tick_logs:
            blocks.append(f"  {entry}")

    # --- dead agents block ---
    dead = [name for name, a in game_state.agents.items() if not a.is_alive()]
    if dead:
        blocks.append(f"Eliminated players: {', '.join(dead)}.")

    # --- short term memory block ---
    recent_actions = agent.action_history[-4:]
    if recent_actions:
        blocks.append("Your recent actions:")
        for a in recent_actions:
            blocks.append(f"  {a}")
        blocks.append("CRITICAL: Do NOT repeat an action (such as moving back and forth between the same rooms, or saying the exact same sentence). If you have nothing new to say, do NOT just say 'the night is quiet'. Instead, use the 'move' tool to investigate another room, or ask a specific new question to someone.")

    # --- phase-specific reminders ---
    if game_state.current_phase == Phase.NIGHT:
        blocks.append(
            "It is night. Movement and role actions are active. "
            "Wolves may kill any tick they choose. Stay alert."
        )
    elif game_state.current_phase == Phase.CONFERENCE:
        blocks.append(
            "It is the conference phase. All agents are in the shared space. "
            "Discuss, accuse, and vote to lynch a suspect."
        )
        # Explicit anti-repetition instruction
        my_conf_actions = [a for a in agent.action_history if "Phase conference" in a]
        if my_conf_actions:
            blocks.append(
                "CRITICAL: Here are the statements/actions you have already made this conference:\n" +
                "\n".join([f"  {a}" for a in my_conf_actions]) +
                "\nDo NOT repeat your previous statements verbatim. You must build on the conversation, "
                "respond directly to what others just said in the recent logs, or ask new questions. "
                "Repeating yourself makes you look highly suspicious."
            )
    elif game_state.current_phase == Phase.DAY:
        blocks.append(
            "It is daytime. Move freely, observe, and build your case "
            "before the next night falls."
        )

    return "\n".join(blocks)


def _wolf_partner(wolf_name: str, game_state: GameState) -> str:
    for name, agent in game_state.agents.items():
        if agent.role == Role.WOLF and name != wolf_name and agent.is_alive():
            return name
    return "unknown (your partner has been eliminated)"