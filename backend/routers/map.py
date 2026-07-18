from fastapi import APIRouter, HTTPException
from backend.engine.phase_engine import PhaseEngine
from backend.routers.game import _require_engine

router = APIRouter(prefix="/map", tags=["map"])


@router.get("/state")
def map_state():
    engine = _require_engine()
    location_resolver = engine.location_resolver

    # build room → occupants map from live agent positions
    room_occupants: dict[str, list[str]] = {}
    for agent_name, agent_state in engine.game_state.agents.items():
        room = agent_state.room
        if room not in room_occupants:
            room_occupants[room] = []
        if agent_state.is_alive():
            room_occupants[room].append(agent_name)

    return {
        "rooms": room_occupants,
        "agent_positions": {
            name: state.room
            for name, state in engine.game_state.agents.items()
            if state.is_alive()
        },
    }


@router.get("/adjacency")
def map_adjacency():
    engine = _require_engine()
    graph = engine.location_resolver.graph
    adjacency = {}
    for room in graph.all_rooms():
        adjacency[room] = list(graph.neighbors(room))
    return {"adjacency": adjacency}