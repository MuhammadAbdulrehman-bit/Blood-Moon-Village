import os
from dotenv import load_dotenv

load_dotenv()

# ── Groq API keys ────────────────────────────────────────
# Each agent role gets its own key where possible, to spread rate limits
# across separate accounts as you described earlier.
GROQ_API_KEY_WOLVES = os.getenv("GROQ_API_KEY_WOLVES")
GROQ_API_KEY_DOCTOR = os.getenv("GROQ_API_KEY_DOCTOR")
GROQ_API_KEY_SEER = os.getenv("GROQ_API_KEY_SEER")
GROQ_API_KEY_VILLAGERS = os.getenv("GROQ_API_KEY_VILLAGERS")

# Maps role -> which key to use. Villagers (the most numerous, least
# tool-heavy role) share one key since they make simple calls.
ROLE_API_KEYS = {
    "wolf": GROQ_API_KEY_WOLVES,
    "doctor": GROQ_API_KEY_DOCTOR,
    "seer": GROQ_API_KEY_SEER,
    "villager": GROQ_API_KEY_VILLAGERS,
}

# ── Model settings ───────────────────────────────────────
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_TEMPERATURE = 0.8
GROQ_MAX_TOKENS = 1000

# ── Game roster ──────────────────────────────────────────
NUM_WOLVES = 2
NUM_DOCTORS = 1
NUM_SEERS = 1
NUM_VILLAGERS = 4
TOTAL_AGENTS = NUM_WOLVES + NUM_DOCTORS + NUM_SEERS + NUM_VILLAGERS

# ── Doctor rules ─────────────────────────────────────────
DOCTOR_TOTAL_SAVES = 2

# ── Tick limits per phase ────────────────────────────────
NIGHT_TICKS = 5
CONFERENCE_DISCUSSION_TICKS = 2
CONFERENCE_VOTE_TICKS = 1
DAY_TICKS = 4

# ── Teleport mechanic ────────────────────────────────────
# Chance, checked once per night, that exactly one wolf is granted
# the blind teleport ability for that night only.
TELEPORT_CHANCE_PER_NIGHT = 0.15

# ── Map ───────────────────────────────────────────────────
DEFAULT_STARTING_ROOM = "Hall"

# ── Server ────────────────────────────────────────────────
HOST = "0.0.0.0"
PORT = 8000

# ── Redis (currently unused — kept here for later if needed) ─
REDIS_URL = os.getenv("REDIS_URL", None)