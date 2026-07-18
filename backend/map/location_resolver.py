from backend.map.map_graph import MapGraph


class LocationResolver:
    """
    Takes the map graph and a live positions dict, and answers
    spatial questions about agents.

    positions format:
        { "agent_name": "room_name", ... }
        e.g. { "Elias": "Kitchen", "Mira": "Hall", "Dawn": "Kitchen" }

    This object is created once at game start and updated each tick
    as agents move. It never owns the positions dict — it just reads it.
    The positions dict itself lives in game_state.py.
    """

    def __init__(self, graph: MapGraph, positions: dict[str, str]):
        self.graph = graph
        self.positions = positions  # shared reference, not a copy

    def current_room(self, agent_name: str) -> str:
        """Returns the room this agent is currently in."""
        if agent_name not in self.positions:
            raise ValueError(f"Unknown agent: '{agent_name}'")
        return self.positions[agent_name]

    def agents_in_room(self, room_name: str) -> list[str]:
        """
        Returns every agent currently in this room.
        This is what an agent "sees" when they look around —
        their perception of the room is exactly this list minus themselves.
        """
        return [
            agent for agent, room in self.positions.items()
            if room == room_name
        ]

    def roommates(self, agent_name: str) -> list[str]:
        """
        Returns everyone in the same room as this agent, excluding themselves.
        This is the core perception call — what an agent sees around them.
        """
        my_room = self.current_room(agent_name)
        return [
            other for other in self.agents_in_room(my_room)
            if other != agent_name
        ]

    def valid_moves(self, agent_name: str) -> list[str]:
        """
        Returns the rooms this agent can legally move to next tick.
        Includes their current room (staying put is always a valid move).
        """
        my_room = self.current_room(agent_name)
        neighbors = self.graph.neighbors(my_room)
        return [my_room] + list(neighbors)

    def can_move_to(self, agent_name: str, target_room: str) -> bool:
        """True if moving to target_room is a legal one-step move for this agent."""
        return target_room in self.valid_moves(agent_name)

    def move_agent(self, agent_name: str, target_room: str) -> None:
        """
        Moves an agent to target_room if the move is legal.
        Raises if the move is illegal — callers should validate first
        using can_move_to() or valid_moves().
        """
        if not self.can_move_to(agent_name, target_room):
            current = self.current_room(agent_name)
            raise ValueError(
                f"Illegal move: '{agent_name}' cannot move from "
                f"'{current}' to '{target_room}' in one step."
            )
        self.positions[agent_name] = target_room

    def are_in_same_room(self, agent_a: str, agent_b: str) -> bool:
        """
        True if two agents share a room right now.
        Used by: wolf kill validation, doctor save validation, seer inspect validation.
        All three mechanics require same-room co-location.
        Note: doctor save is an exception — distance doesn't matter for saves.
        """
        return self.current_room(agent_a) == self.current_room(agent_b)

    def teleport_agent(self, agent_name: str, target_room: str) -> None:
        """
        Moves an agent to any room on the map, ignoring adjacency.
        Used exclusively by the wolf's blind teleport ability.
        Does NOT validate adjacency — that's intentional, teleport bypasses movement rules.
        Does validate that the target room actually exists on the map.
        """
        if target_room not in self.graph.all_rooms():
            raise ValueError(f"Teleport target '{target_room}' is not a valid room.")
        self.positions[agent_name] = target_room