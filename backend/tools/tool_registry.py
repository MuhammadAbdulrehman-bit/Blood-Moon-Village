from backend.state.state_manager import StateManager
from backend.agents.base_agent import AgentAction
from backend.state.game_state import GameState, Phase


class ToolRegistry:
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager

    @property
    def location_resolver(self):
        return self.state_manager.get_resolver()

    def execute(self, agent_name: str, action: AgentAction, game_state: GameState) -> str:
        tool = action.tool_name
        target = action.target
        message = action.message

        handlers = {
            "move":        self._handle_move,
            "speak":       self._handle_speak,
            "kill":        self._handle_kill,
            "teleport":    self._handle_teleport,
            "save":        self._handle_save,
            "inspect":     self._handle_inspect,
            "accuse":      self._handle_accuse,
            "vote_lynch":  self._handle_vote_lynch,
            "defend_self": self._handle_defend_self,
            "wolf_communicate": self._handle_wolf_communicate,
        }

        handler = handlers.get(tool)
        if not handler:
            return f"[INVALID] {agent_name} attempted unknown tool '{tool}' — action ignored."

        return handler(agent_name, target, message, game_state)

    # --- movement ---

    def _handle_move(self, agent_name, target, message, game_state) -> str:
        if not target:
            return f"[INVALID] {agent_name} tried to move without specifying a room."

        current_room = game_state.agents[agent_name].room
        valid = self.location_resolver.valid_moves(agent_name)

        if target == current_room:
            return f"[INVALID] {agent_name} tried to move to {target}, but is already there. Action ignored."

        if target not in valid:
            return (
                f"[INVALID] {agent_name} tried to move to '{target}' "
                f"but it is not adjacent to {current_room}. Action ignored."
            )

        self.state_manager.move_agent(agent_name, target)
        return f"[MOVE] {agent_name} moved from {current_room} to {target}."

    # --- speech ---

    def _handle_speak(self, agent_name, target, message, game_state) -> str:
        if not message:
            return f"[SPEAK] {agent_name} said nothing."
        room = game_state.agents[agent_name].room
        entry = f"[SPEAK] {agent_name} (in {room}): {message}"
        return entry

    def _handle_accuse(self, agent_name, target, message, game_state) -> str:
        if not target:
            return f"[INVALID] {agent_name} tried to accuse without naming a target."
        reason_str = f" Reason: {message}" if message else ""
        entry = f"[ACCUSE] {agent_name} accuses {target}.{reason_str}"
        return entry

    def _handle_defend_self(self, agent_name, target, message, game_state) -> str:
        if not message:
            return f"[DEFEND] {agent_name} offered no defense."
        entry = f"[DEFEND] {agent_name}: {message}"
        return entry

    # --- night tools ---

    def _handle_kill(self, agent_name, target, message, game_state) -> str:
        if game_state.current_phase != Phase.NIGHT:
            return f"[INVALID] {agent_name} tried to kill outside of night phase."
        if not target:
            return f"[INVALID] {agent_name} tried to kill without a target."

        killer_room = game_state.agents[agent_name].room
        target_agent = game_state.agents.get(target)

        if not target_agent:
            return f"[INVALID] {agent_name} targeted unknown agent '{target}'."
        if not target_agent.is_alive():
            return f"[INVALID] {agent_name} targeted '{target}' who is already dead."
        if target_agent.room != killer_room:
            return (
                f"[INVALID] {agent_name} tried to kill {target} "
                f"but they are not in the same room."
            )

        # spatial validation passed — night_resolver owns the actual kill execution
        return f"[KILL_VALID] {agent_name} targets {target}."

    def _handle_teleport(self, agent_name, target, message, game_state) -> str:
        if game_state.current_phase != Phase.NIGHT:
            return f"[INVALID] {agent_name} tried to teleport outside of night phase."
        if not target:
            return f"[INVALID] {agent_name} tried to teleport without naming a target."

        target_agent = game_state.agents.get(target)
        if not target_agent:
            return f"[INVALID] {agent_name} tried to teleport unknown agent '{target}'."
        if not target_agent.is_alive():
            return f"[INVALID] {agent_name} tried to teleport dead agent '{target}'."

        wolf_room = game_state.agents[agent_name].room
        self.state_manager.teleport_agent(target, wolf_room)
        return f"[TELEPORT] {target} was pulled into {wolf_room} by an unseen force."

    def _handle_save(self, agent_name, target, message, game_state) -> str:
        if game_state.current_phase != Phase.NIGHT:
            return f"[INVALID] {agent_name} tried to save outside of night phase."
        if not target:
            return f"[INVALID] {agent_name} tried to save without a target."
        if target == agent_name:
            return f"[INVALID] {agent_name} cannot save themselves."

        doctor_agent = game_state.agents[agent_name]
        if doctor_agent.saves_remaining <= 0:
            return f"[INVALID] {agent_name} has no saves remaining."

        target_agent = game_state.agents.get(target)
        if not target_agent:
            return f"[INVALID] {agent_name} tried to save unknown agent '{target}'."

        # valid — night_resolver owns execution via resolve_save_window
        return f"[SAVE_VALID] {agent_name} is positioned to save {target}."

    def _handle_inspect(self, agent_name, target, message, game_state) -> str:
        if game_state.current_phase != Phase.NIGHT:
            return f"[INVALID] {agent_name} tried to inspect outside of night phase."
        if not target:
            return f"[INVALID] {agent_name} tried to inspect without a target."

        seer_room = game_state.agents[agent_name].room
        target_agent = game_state.agents.get(target)

        if not target_agent:
            return f"[INVALID] {agent_name} tried to inspect unknown agent '{target}'."
        if not target_agent.is_alive():
            return f"[INVALID] {agent_name} tried to inspect dead agent '{target}'."
            
        if seer_room != target_agent.room:
            return f"[INVALID] {agent_name} tried to inspect {target} but they are not in the same room."
            
        revealed_role = target_agent.role
        return f"[INSPECT] {agent_name} inspected {target}: they are a {revealed_role.value}."

    def _handle_wolf_communicate(self, agent_name, target, message, game_state) -> str:
        if game_state.current_phase != Phase.NIGHT:
            return f"[INVALID] {agent_name} tried to use wolf_communicate outside of night phase."
        if not message:
            return f"[INVALID] {agent_name} tried to communicate an empty message."

        # Note: state_graph.py appends the message to wolf_channel_log in real-time
        # so we don't append it again here to avoid duplicates.
        return f"[WOLF STRATEGY] {agent_name}: {message}"

    # --- voting ---

    def _handle_vote_lynch(self, agent_name, target, message, game_state) -> str:
        if game_state.current_phase != Phase.CONFERENCE:
            return f"[INVALID] {agent_name} tried to vote outside of conference phase."
        if not target:
            return f"[INVALID] {agent_name} tried to vote without a target."

        target_agent = game_state.agents.get(target)
        if not target_agent:
            return f"[INVALID] {agent_name} tried to vote for unknown agent '{target}'."
        if not target_agent.is_alive():
            return f"[INVALID] {agent_name} tried to vote for dead agent '{target}'."
        if target == agent_name:
            return f"[INVALID] {agent_name} cannot vote to lynch themselves."

        entry = f"[VOTE] {agent_name} votes to lynch {target}."
        return entry