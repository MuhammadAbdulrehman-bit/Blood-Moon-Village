from fastapi import APIRouter, HTTPException
from backend.engine.phase_engine import PhaseEngine

router = APIRouter(prefix="/game", tags=["game"])

_engine: PhaseEngine | None = None
_advance_in_progress = False


def set_engine(engine: PhaseEngine):
    global _engine
    _engine = engine


def _require_engine() -> PhaseEngine:
    if _engine is None:
        raise HTTPException(status_code=503, detail="Game engine not initialized.")
    return _engine


@router.post("/start")
def start_game():
    engine = _require_engine()
    if engine.winner:
        raise HTTPException(status_code=400, detail="Game already finished.")
    return {
        "status": "started",
        "round": engine.game_state.current_round,
        "phase": engine.game_state.current_phase.value,
        "agents": list(engine.agents.keys()),
    }


@router.post("/advance")
def advance_tick():
    global _advance_in_progress

    if _advance_in_progress:
        raise HTTPException(
            status_code=409,
            detail="A phase is already advancing. Please wait for it to finish."
        )

    engine = _require_engine()
    if engine.winner:
        raise HTTPException(status_code=400, detail=f"Game over. Winner: {engine.winner}")

    _advance_in_progress = True
    try:
        engine.run_current_phase_to_completion()

        return {
            "phase_completed": engine.game_state.current_phase.value,
            "winner": engine.winner,
            "round": engine.game_state.current_round,
            "alive_agents": [
                name for name, a in engine.game_state.agents.items() if a.is_alive()
            ],
        }
    finally:
        _advance_in_progress = False


@router.post("/advance_one_tick")
def advance_one_tick():
    global _advance_in_progress

    if _advance_in_progress:
        raise HTTPException(
            status_code=409,
            detail="A phase is already advancing. Please wait for it to finish."
        )

    engine = _require_engine()
    if engine.winner:
        raise HTTPException(status_code=400, detail=f"Game over. Winner: {engine.winner}")

    _advance_in_progress = True
    try:
        engine.advance_one_tick()

        return {
            "winner": engine.winner,
            "round": engine.game_state.current_round,
            "phase": engine.game_state.current_phase.value,
            "tick": engine.game_state.current_tick,
            "alive_agents": [
                name for name, a in engine.game_state.agents.items() if a.is_alive()
            ],
        }
    finally:
        _advance_in_progress = False


@router.get("/status")
def game_status():
    engine = _require_engine()
    return {
        "round": engine.game_state.current_round,
        "phase": engine.game_state.current_phase.value,
        "tick": engine.game_state.current_tick,
        "winner": engine.winner,
        "alive_agents": [
            name for name, a in engine.game_state.agents.items() if a.is_alive()
        ],
        "dead_agents": [
            name for name, a in engine.game_state.agents.items() if not a.is_alive()
        ],
    }