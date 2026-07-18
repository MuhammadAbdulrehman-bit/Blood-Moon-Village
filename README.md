# Blood Moon Village

An AI-driven simulation where Large Language Model (LLM) agents play a spatial version of the classic social deduction game **Werewolf** (also known as Mafia). 

Unlike standard Werewolf, agents in this simulation navigate through physical rooms on a map, adding a completely new layer of deduction. To kill, inspect, or save someone, agents must physically move to be in the same room as their target.

<img width="1705" height="859" alt="Night Phase general" src="https://github.com/user-attachments/assets/026dfe64-4f0e-4b63-9fd3-18c31c69db0c" />


##  Features

- **Autonomous LLM Agents:** Fully autonomous agents powered by **Groq** that reason, plan, and execute actions based on their hidden roles.
- **Spatial Deduction:** Agents move between adjacent rooms. Villagers can use movement logs to deduce who might have been in the room with the victim during the night.
- **Standard Roles:**
  -  **Wolves:** Wake up at night to hunt. They have a secret encrypted communication channel.
  -  **Doctor:** Can protect one player per night from death.
  -  **Seer:** Can inspect one player per night to reveal their true identity.
  -  **Villagers:** Must use logic, discussion, and movement logs to find the wolves.
- **Dynamic Phases:** The engine cycles through continuous Day, Night, and Conference (Discussion & Voting) phases.
- **Rich Tool Calling:** Agents interact via a suite of tools including `move`, `speak`, `kill`, `teleport`, `save`, `inspect`, `wolf_communicate`, `accuse`, and `vote_lynch`.
- **Full Observability:** Deeply integrated with **LangSmith** to provide full transparency into agent reasoning, tool call traces, and exact token usage.

##  Architecture

- **Backend:** Built with **FastAPI** and Python. Handles the game engine tick loop, state management, agent logic, and spatial resolving.
- **Frontend:** Built with **React** & **Vite**. Visualizes the map, agent locations, and streams the public logs dynamically.
- **AI Integration:** Uses `groq` for ultra-low latency LLM inference and `langsmith` for detailed tracing and debugging.

##  Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+ (for frontend)
- [Groq API Key](https://console.groq.com/keys)
- [LangSmith API Key](https://smith.langchain.com/) (Optional, but highly recommended for tracing)

### 1. Backend Setup

Navigate to the root directory and create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

Install the required Python dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the root directory based on your keys:

```env
# Default role keys (Fallback)
GROQ_API_KEY_WOLVES="your-groq-key-here"
GROQ_API_KEY_DOCTOR="your-groq-key-here"
GROQ_API_KEY_SEER="your-groq-key-here"
GROQ_API_KEY_VILLAGERS="your-groq-key-here"

# (Optional) Agent-specific override keys
GROQ_API_KEY_ALDRIC="your-groq-key-here"
# ... 

# LangSmith Observability (Highly Recommended)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"
LANGCHAIN_API_KEY="your-langsmith-key-here"
LANGCHAIN_PROJECT="werewolf-village"
```

Start the FastAPI server:

```bash
uvicorn backend.main:app --reload
```
*The API will be available at `http://127.0.0.1:8000`.*

### 2. Frontend Setup

Open a new terminal and navigate to the frontend folder:

```bash
cd frontend
npm install
npm run dev
```

*The frontend will be available at `http://localhost:5173`.*

## 📈 Observability & Tracing

Because complex multi-agent systems can be difficult to debug, this project uses **LangSmith** to trace the exact thoughts of the agents. Once you run the game with tracing enabled in your `.env` file, head over to your [LangSmith Dashboard](https://smith.langchain.com/) to monitor:
- Which tools the agents are calling and why
- Raw reasoning logs (Chain-of-Thought)
- Token usage statistics per agent

<img width="1444" height="811" alt="image" src="https://github.com/user-attachments/assets/6622f69a-5480-4b79-8958-c4dd34df9d3e" />


## 📜 License
Made by: Muhammad Abdul Rehman
BS AI Student, Shifa Tameer-e-Millat University
[MIT License](LICENSE)
