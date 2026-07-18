from backend.state.game_state import GameState, Phase
from backend.state.state_manager import StateManager
from backend.agents.base_agent import AgentAction
from backend.agents.seer import SeerAgent
from backend.agents.doctor import DoctorAgent
from backend.channels.wolf_channel import WolfChannel
from backend.tools.tool_registry import ToolRegistry
from backend.engine.reveal_rules import (
    public_death_announcement,
    save_hint_for_wolves,
)


class NightResolver:
    def __init__(
        self,
        state_manager: StateManager,
        tool_registry: ToolRegistry,
        wolf_channel: WolfChannel,
    ):
        self.state_manager = state_manager
        self.tool_registry = tool_registry
        self.wolf_channel = wolf_channel

    def resolve_tick(
        self,
        tick_actions: dict[str, AgentAction],
        game_state: GameState,
        seer_agents: dict[str, SeerAgent],
        doctor_agents: dict[str, DoctorAgent],
    ) -> list[str]:
        results = []
        kill_action: tuple[str, AgentAction] | None = None

        for agent_name, action in tick_actions.items():
            agent = game_state.agents[agent_name]
            if not agent.is_alive():
                continue

            if action.tool_name == "kill":
                kill_action = (agent_name, action)
                continue

            if action.tool_name == "inspect" and agent_name in seer_agents:
                result = self.tool_registry.execute(agent_name, action, game_state)
                # DO NOT append inspect details to public results
                target = action.target
                if target and target in game_state.agents:
                    revealed_role = game_state.agents[target].role
                    seer_agents[agent_name].record_inspection(target, revealed_role)
                continue

            result = self.tool_registry.execute(agent_name, action, game_state)
            # DO NOT append private actions (save, wolf_communicate) to public results
            if action.tool_name not in ["save", "wolf_communicate"]:
                results.append(result)

        if kill_action:
            results.extend(
                self._resolve_kill(kill_action, game_state, doctor_agents, tick_actions)
            )

        return results

    def _resolve_kill(
        self,
        kill_action: tuple[str, AgentAction],
        game_state: GameState,
        doctor_agents: dict[str, DoctorAgent],
        tick_actions: dict[str, AgentAction],
    ) -> list[str]:
        results = []
        killer_name, action = kill_action
        target_name = action.target

        if not target_name or target_name not in game_state.agents:
            results.append(f"[INVALID] Kill failed — unknown target '{target_name}'.")
            return results

        target = game_state.agents[target_name]
        killer = game_state.agents[killer_name]

        if not target.is_alive():
            results.append(f"[INVALID] Kill failed — {target_name} already dead.")
            return results

        if target.room != killer.room:
            results.append(
                f"[INVALID] Kill failed — {target_name} not in same room as {killer_name}."
            )
            return results

        success = self.state_manager.attempt_kill(
            attacker=killer_name,
            victim=target_name,
            tick=game_state.current_tick,
        )
        if not success:
            results.append(f"[INVALID] Kill attempt rejected.")
            return results

        victim_room = target.room
        death_announcement = public_death_announcement(target_name, victim_room)
        results.append(death_announcement)

        saved = self._resolve_save_window(
            target_name, victim_room, game_state, doctor_agents, tick_actions
        )

        if saved:
            game_state.wolf_channel_log.append("[WOLF CHANNEL] SYSTEM: Your target survived the night. Someone intervened.")
            results.append("[SAVE] Target was saved. (wolf channel notified privately)")
        else:
            self.state_manager.resolve_save_window(doctor_used_save=False)
            results.append(f"[DEATH CONFIRMED] {target_name} is eliminated.")

        return results

    def _resolve_save_window(
        self,
        target_name: str,
        target_room: str,
        game_state: GameState,
        doctor_agents: dict[str, DoctorAgent],
        tick_actions: dict[str, AgentAction],
    ) -> bool:
        # save only counts if the doctor actually chose to save THIS victim,
        # via a genuine tool call, this tick — not merely by standing nearby
        for doctor_name, doctor_agent in doctor_agents.items():
            doctor_state = game_state.agents[doctor_name]
            if not doctor_state.is_alive():
                continue
            if doctor_state.saves_remaining <= 0:
                continue
            if doctor_name == target_name:
                continue

            doctor_action = tick_actions.get(doctor_name)
            if not doctor_action:
                continue
            if doctor_action.tool_name != "save":
                continue
            if doctor_action.target != target_name:
                continue

            self.state_manager.resolve_save_window(doctor_used_save=True)
            return True

        return False