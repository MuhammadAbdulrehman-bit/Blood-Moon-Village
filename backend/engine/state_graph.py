from typing import TypedDict
from langgraph.graph import StateGraph, END
from backend.agents.base_agent import AgentAction
from backend.engine.phase_engine import PhaseEngine
from backend.agents.perception import build_perception
from backend.state.game_state import Phase

class TickState(TypedDict):
    agent_names: list[str]
    current_index: int
    tick_actions: dict[str, AgentAction]
    tick_logs: list[str]

def build_tick_graph(engine: PhaseEngine):
    builder = StateGraph(TickState)

    def agent_node(state: TickState) -> dict:
        idx = state["current_index"]
        agent_names = state["agent_names"]
        
        if idx >= len(agent_names):
            return {}
            
        agent_name = agent_names[idx]
        agent = engine.agents[agent_name]
        
        agent_state = engine.game_state.agents.get(agent_name)
        if not agent_state or not agent_state.is_alive():
            return {"current_index": idx + 1}
            
        seer = engine.seer_agents.get(agent_name)
        
        game_context = build_perception(
            agent_name=agent_name,
            game_state=engine.game_state,
            belief_registry=engine.belief_registry,
            location_resolver=engine.location_resolver,
            seer_agent=seer,
            tick_logs=state.get("tick_logs", [])
        )
        
        llm_client = engine.llm_clients[agent_name]
        phase = engine.game_state.current_phase
        tick = engine.game_state.current_tick
        
        if phase == Phase.NIGHT:
            allowed_tools = agent.available_tools()
        elif phase == Phase.CONFERENCE:
            import backend.config as cfg
            if tick < cfg.CONFERENCE_DISCUSSION_TICKS:
                allowed_tools = ["speak", "accuse", "defend_self"]
            else:
                allowed_tools = ["vote_lynch"]
        elif phase == Phase.DAY:
            allowed_tools = ["move", "speak"]
        else:
            allowed_tools = ["speak"]

        action = agent.decide_action(game_context, llm_client, override_tools=allowed_tools)
        
        engine.game_state.log_reasoning(
            agent_name=agent_name,
            tool_name=action.tool_name,
            target=action.target,
            message=action.message,
            raw_reasoning=action.raw_reasoning,
        )
        
        action_summary = f"Phase {phase.value} Tick {tick}: used '{action.tool_name}'"
        if action.target:
            action_summary += f" on {action.target}"
        if action.message:
            action_summary += f" with message '{action.message}'"
        agent_state.action_history.append(action_summary)

        new_logs = list(state.get("tick_logs", []))
        
        # Prevent secret night actions from leaking to other agents in the same tick
        public_tools = {"speak", "move", "accuse", "defend_self", "vote_lynch"}
        if action.tool_name in public_tools:
            log_entry = f"[{action.tool_name.upper()}] {agent_name} executed {action.tool_name}"
            if action.target:
                log_entry += f" on {action.target}"
            new_logs.append(log_entry)
        elif action.tool_name == "wolf_communicate":
            # wolves communicate in real-time instantly during the sequence so the other wolf can hear it
            entry = f"[WOLF STRATEGY] {agent_name}: {action.message}"
            engine.game_state.wolf_channel_log.append(entry)
        
        new_actions = dict(state.get("tick_actions", {}))
        new_actions[agent_name] = action
        
        return {
            "current_index": idx + 1,
            "tick_logs": new_logs,
            "tick_actions": new_actions
        }

    def router(state: TickState) -> str:
        if state["current_index"] < len(state["agent_names"]):
            return "agent_node"
        return END

    builder.add_node("agent_node", agent_node)
    builder.set_entry_point("agent_node")
    builder.add_conditional_edges("agent_node", router)
    
    return builder.compile()
