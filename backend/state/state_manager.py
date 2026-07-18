from backend.state.game_state import GameState, Role, Phase, NightEvent
from backend.state.belief_state import BeliefRegistry
from backend.map.map_layout import GAME_MAP
from backend.map.location_resolver import LocationResolver


class StateManager:
    def __init__(self):
        self.game_state = GameState()
        self.beliefs = BeliefRegistry()
        self.location_resolver: LocationResolver | None = None

    def setup_game(self, roster: dict[str, Role], starting_rooms: dict[str, str]) -> None:
        for name, role in roster.items():
            room = starting_rooms.get(name, "Hall")
            self.game_state.add_agent(name, role, room)

        all_names = list(roster.keys())
        for name in all_names:
            self.beliefs.create_belief(name, all_names)

        self.location_resolver = LocationResolver(GAME_MAP, self.game_state.positions())
        self.game_state.log_public("Game initialized. Night falls for the first time.")

    def get_resolver(self) -> LocationResolver:
        if self.location_resolver is None:
            raise RuntimeError("Game not set up yet — call setup_game() first.")
        return self.location_resolver

    def move_agent(self, agent_name: str, target_room: str) -> None:
        resolver = self.get_resolver()
        resolver.move_agent(agent_name, target_room)
        self.game_state.agents[agent_name].room = target_room

    def teleport_agent(self, agent_name: str, target_room: str) -> None:
        resolver = self.get_resolver()
        resolver.teleport_agent(agent_name, target_room)
        self.game_state.agents[agent_name].room = target_room

    def attempt_kill(self, attacker: str, victim: str, tick: int) -> bool:
        resolver = self.get_resolver()
        attacker_state = self.game_state.get_agent(attacker)
        victim_state = self.game_state.get_agent(victim)

        if not attacker_state.is_alive() or not victim_state.is_alive():
            return False

        room = resolver.current_room(victim)
        event = NightEvent(tick=tick, attacker=attacker, victim=victim, room=room)
        self.game_state.active_night_event = event
        return True

    def resolve_save_window(self, doctor_used_save: bool) -> None:
        event = self.game_state.active_night_event
        if event is None:
            raise RuntimeError("No active night event to resolve.")

        if doctor_used_save:
            doctor = self._get_doctor()
            doctor.saves_remaining -= 1
            event.saved = True
            self.game_state.log_wolf_channel("Your target survived the night.")
        else:
            victim_state = self.game_state.get_agent(event.victim)
            victim_state.kill()
            self.game_state.deaths_this_round.append(event.victim)
            self.beliefs.mark_agent_dead(event.victim)

        self.game_state.active_night_event = None

    def _get_doctor(self):
        doctors = self.game_state.agents_by_role(Role.DOCTOR)
        if not doctors:
            raise RuntimeError("No doctor exists in this game.")
        return doctors[0]

    def doctor_can_save(self) -> bool:
        doctor = self._get_doctor()
        return doctor.is_alive() and doctor.saves_remaining > 0

    def lynch_agent(self, target: str) -> None:
        target_state = self.game_state.get_agent(target)
        target_state.kill()
        self.beliefs.mark_agent_dead(target)

    def check_win_condition(self) -> str | None:
        wolves = len(self.game_state.living_wolves())
        villagers = len(self.game_state.living_villagers())

        if wolves == 0:
            return "village"
        if wolves >= villagers:
            return "wolves"
        return None

    def finalize_win_check(self) -> None:
        result = self.check_win_condition()
        if result is not None:
            self.game_state.game_over = True
            self.game_state.winner = result