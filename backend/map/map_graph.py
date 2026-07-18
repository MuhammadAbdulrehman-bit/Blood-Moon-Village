from dataclasses import dataclass, field


@dataclass
class MapGraph:
    adjacency: dict[str, set[str]] = field(default_factory=dict)

    def add_room(self, room_name: str) -> None:
        if room_name not in self.adjacency:
            self.adjacency[room_name] = set()

    def add_connection(self, room_a: str, room_b: str) -> None:
        self.add_room(room_a)
        self.add_room(room_b)
        self.adjacency[room_a].add(room_b)
        self.adjacency[room_b].add(room_a)

    def neighbors(self, room_name: str) -> set[str]:
        if room_name not in self.adjacency:
            raise ValueError(f"Unknown room: '{room_name}'")
        return self.adjacency[room_name]

    def is_connected(self, room_a: str, room_b: str) -> bool:
        return room_b in self.neighbors(room_a)

    def all_rooms(self) -> list[str]:
        return list(self.adjacency.keys())

    def room_count(self) -> int:
        return len(self.adjacency)