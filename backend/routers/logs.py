from fastapi import APIRouter, Query
from backend.routers.game import _require_engine

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("/public")
def public_log(last_n: int = Query(default=50, ge=1, le=500)):
    engine = _require_engine()
    log = engine.game_state.public_log
    return {
        "total_entries": len(log),
        "entries": log[-last_n:],
    }


@router.get("/wolf_channel")
def wolf_channel_log(last_n: int = Query(default=50, ge=1, le=500)):
    engine = _require_engine()
    log = engine.game_state.wolf_channel_log
    return {
        "total_entries": len(log),
        "entries": log[-last_n:],
    }


@router.get("/reasoning")
def reasoning_log(
    agent: str | None = None,
    last_n: int = Query(default=200, ge=1, le=1000),
):
    engine = _require_engine()
    entries = engine.game_state.reasoning_log
    if agent:
        entries = [e for e in entries if e["agent"] == agent]
    return {
        "total_entries": len(entries),
        "entries": entries[-last_n:],
    }


@router.get("/full_transcript")
def full_transcript():
    engine = _require_engine()
    return {
        "public_log": engine.game_state.public_log,
        "wolf_channel": engine.game_state.wolf_channel_log,
        "reasoning": engine.game_state.reasoning_log,
        "round": engine.game_state.current_round,
        "winner": engine.winner,
    }