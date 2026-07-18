import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from backend import config as cfg
from backend.state.game_state import Role
from backend.state.state_manager import StateManager
from backend.agents.wolf import WolfAgent
from backend.agents.doctor import DoctorAgent
from backend.agents.seer import SeerAgent
from backend.agents.villager import VillagerAgent
from backend.channels.wolf_channel import WolfChannel
from backend.tools.tool_registry import ToolRegistry
from backend.engine.phase_engine import PhaseEngine
from backend.agents.llm_client import LLMClient
from backend.routers import game as game_router
from backend.routers import map as map_router
from backend.routers import logs as logs_router
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI(title="Spatial Werewolf", version="1.0.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def build_engine() -> PhaseEngine:

    # --- agent definitions ---
    agent_definitions = [
        ("Aldric",  Role.WOLF),
        ("Maren",   Role.WOLF),
        ("Corvus",  Role.DOCTOR),
        ("Sylva",   Role.SEER),
        ("Brennan", Role.VILLAGER),
        ("Isolde",  Role.VILLAGER),
        ("Theron",  Role.VILLAGER),
        ("Wren",    Role.VILLAGER),
    ]

    # --- build agent instances ---
    agents = {}
    for name, role in agent_definitions:
        if role == Role.WOLF:
            agents[name] = WolfAgent(name=name)
        elif role == Role.DOCTOR:
            agents[name] = DoctorAgent(name=name)
        elif role == Role.SEER:
            agents[name] = SeerAgent(name=name)
        else:
            agents[name] = VillagerAgent(name=name)

    # --- state manager ---
    # StateManager owns game_state, belief_registry, and location_resolver internally
    state_manager = StateManager()
    roster = {name: role for name, role in agent_definitions}
    starting_rooms = {name: cfg.DEFAULT_STARTING_ROOM for name, _ in agent_definitions}
    state_manager.setup_game(roster=roster, starting_rooms=starting_rooms)

    # pull references out after setup — do not construct these separately
    game_state = state_manager.game_state

    # --- wolf channel ---
    wolf_channel = WolfChannel()

    # --- tool registry ---
    tool_registry = ToolRegistry(state_manager)

    # --- llm clients (one per agent, keyed by agent name) ---
    llm_clients = {
        name: LLMClient(role=agent.role, agent_name=name, model=cfg.GROQ_MODEL)
        for name, agent in agents.items()
    }

    # --- engine ---
    return PhaseEngine(
        game_state=game_state,
        state_manager=state_manager,
        agents=agents,
        wolf_channel=wolf_channel,
        tool_registry=tool_registry,
        llm_clients=llm_clients,
        night_ticks=cfg.NIGHT_TICKS,
        conference_ticks=cfg.CONFERENCE_DISCUSSION_TICKS + cfg.CONFERENCE_VOTE_TICKS,
        day_ticks=cfg.DAY_TICKS,
        teleport_probability=cfg.TELEPORT_CHANCE_PER_NIGHT,
    )


@app.on_event("startup")
def startup():
    engine = build_engine()
    game_router.set_engine(engine)


# --- routers ---
app.include_router(game_router.router)
app.include_router(map_router.router)
app.include_router(logs_router.router)

# --- frontend static files ---
if os.path.exists("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")