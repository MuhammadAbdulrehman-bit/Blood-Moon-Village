from backend.map.map_graph import MapGraph


def build_map() -> MapGraph:
    graph = MapGraph()

    graph.add_connection("Attic", "Library")
    graph.add_connection("Library", "Hall")
    graph.add_connection("Hall", "Kitchen")

    graph.add_connection("Study", "Courtyard")
    graph.add_connection("Courtyard", "Cellar")

    graph.add_connection("Library", "Study")
    graph.add_connection("Hall", "Courtyard")
    graph.add_connection("Kitchen", "Cellar")

    return graph


GAME_MAP = build_map()