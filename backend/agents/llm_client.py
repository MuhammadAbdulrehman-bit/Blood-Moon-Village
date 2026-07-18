import os
import json
from groq import Groq
from backend.state.game_state import Role
from backend.agents.base_agent import AgentAction
import time
from langsmith import traceable
from langsmith.wrappers import wrap_openai

# role → env key mapping, loaded once at module level
_ROLE_KEY_MAP = {
    Role.WOLF:     "GROQ_API_KEY_WOLVES",
    Role.DOCTOR:   "GROQ_API_KEY_DOCTOR",
    Role.SEER:     "GROQ_API_KEY_SEER",
    Role.VILLAGER: "GROQ_API_KEY_VILLAGERS",
}


def _get_client(role: Role, agent_name: str | None = None) -> Groq:
    api_key = None
    if agent_name:
        env_key = f"GROQ_API_KEY_{agent_name.upper()}"
        val = os.getenv(env_key)
        if val and val.strip() and val != "YOUR_API_KEY_HERE":
            api_key = val
            print(f"[LLM CONFIG] Using agent-specific key {env_key} for {agent_name}")

    if not api_key:
        role_env_key = _ROLE_KEY_MAP[role]
        val = os.getenv(role_env_key)
        if val and val.strip() and val != "YOUR_API_KEY_HERE":
            api_key = val
            if agent_name:
                print(f"[LLM CONFIG] Using role fallback key {role_env_key} for {agent_name}")
            else:
                print(f"[LLM CONFIG] Using role key {role_env_key}")

    if not api_key:
        agent_desc = f"agent {agent_name} " if agent_name else ""
        expected_keys = f"GROQ_API_KEY_{agent_name.upper()} or " if agent_name else ""
        expected_keys += _ROLE_KEY_MAP[role]
        raise EnvironmentError(
            f"Missing API key for {agent_desc}(role: {role.value}). "
            f"Expected env variable: {expected_keys}"
        )
    
    client = Groq(api_key=api_key)
    # Mock completions so wrap_openai doesn't crash on Groq
    if not hasattr(client, "completions"):
        client.completions = type("Mock", (), {"create": None})()
        
    return wrap_openai(client)


def _build_groq_tools(available_tools: list[str]) -> list[dict]:
    # maps tool names to their Groq function-call schema
    # only the tools available to this agent this turn are included —
    # the LLM cannot attempt to call something not in this list
    tool_schemas = {
        "move": {
            "type": "function",
            "function": {
                "name": "move",
                "description": "Move to an adjacent room.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target": {
                            "type": "string",
                            "description": "The name of the adjacent room to move into."
                        }
                    },
                    "required": ["target"]
                }
            }
        },
        "speak": {
            "type": "function",
            "function": {
                "name": "speak",
                "description": "Say something aloud to agents in the same room.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "What you want to say."
                        }
                    },
                    "required": ["message"]
                }
            }
        },
        "kill": {
            "type": "function",
            "function": {
                "name": "kill",
                "description": "Kill a villager who is in the same room as you. Only usable at night.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target": {
                            "type": "string",
                            "description": "The name of the agent to kill."
                        }
                    },
                    "required": ["target"]
                }
            }
        },
        "teleport": {
            "type": "function",
            "function": {
                "name": "teleport",
                "description": (
                    "Pull a named villager into your current room. "
                    "They receive no information about where they were taken from. "
                    "One-time use, granted randomly."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target": {
                            "type": "string",
                            "description": "The name of the villager to teleport to your room."
                        }
                    },
                    "required": ["target"]
                }
            }
        },
        "save": {
            "type": "function",
            "function": {
                "name": "save",
                "description": (
                    "Spend one of your saves to protect an agent ANYWHERE on the map from death tonight. "
                    "You cannot save yourself."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target": {
                            "type": "string",
                            "description": "The name of the agent to protect."
                        }
                    },
                    "required": ["target"]
                }
            }
        },
        "inspect": {
            "type": "function",
            "function": {
                "name": "inspect",
                "description": (
                    "Reveal the true role of an agent in the same room. "
                    "One use per night, same-room targets only."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target": {
                            "type": "string",
                            "description": "The name of the agent to inspect."
                        }
                    },
                    "required": ["target"]
                }
            }
        },
        "wolf_communicate": {
            "type": "function",
            "function": {
                "name": "wolf_communicate",
                "description": (
                    "Securely send a message to your wolf partner to coordinate strategy. "
                    "This message will not be heard by villagers. Only usable at night."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "The strategic message for your partner."
                        }
                    },
                    "required": ["message"]
                }
            }
        },
        "accuse": {
            "type": "function",
            "function": {
                "name": "accuse",
                "description": "Publicly accuse an agent of being a wolf during conference phase.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target": {
                            "type": "string",
                            "description": "The name of the agent you are accusing."
                        },
                        "reason": {
                            "type": "string",
                            "description": "Your stated reason for the accusation."
                        }
                    },
                    "required": ["target", "reason"]
                }
            }
        },
        "vote_lynch": {
            "type": "function",
            "function": {
                "name": "vote_lynch",
                "description": "Cast your vote to lynch an agent during the conference vote tick.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target": {
                            "type": "string",
                            "description": "The name of the agent you are voting to lynch."
                        }
                    },
                    "required": ["target"]
                }
            }
        },
        "defend_self": {
            "type": "function",
            "function": {
                "name": "defend_self",
                "description": "Make a public statement defending yourself against accusations.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Your defense statement."
                        }
                    },
                    "required": ["message"]
                }
            }
        },
    }

    return [tool_schemas[t] for t in available_tools if t in tool_schemas]


def _parse_tool_call(response, available_tools: list[str]) -> AgentAction:
    message = response.choices[0].message

    # gpt-oss / reasoning models often put chain-of-thought in a separate
    # 'reasoning' field, distinct from 'content' — capture both defensively
    reasoning_field = getattr(message, "reasoning", None) or ""
    content_field = message.content or ""
    raw_reasoning = reasoning_field or content_field

    if not message.tool_calls:
        return AgentAction(
            tool_name="speak",
            target=None,
            message=content_field.strip() or "(silence)",
            raw_reasoning=raw_reasoning,
        )

    call = message.tool_calls[0]
    tool_name = call.function.name
    
    if tool_name not in available_tools:
        # The LLM hallucinated a tool it doesn't have access to!
        return AgentAction(
            tool_name="speak",
            target=None,
            message=content_field.strip() or f"(tried to use invalid tool '{tool_name}')",
            raw_reasoning=raw_reasoning + f"\n[SYSTEM: Fallback applied because '{tool_name}' is not in available_tools]",
        )
        
    args = json.loads(call.function.arguments)

    target = args.get("target") or args.get("reason") and args.get("target") or None
    message_text = args.get("message") or args.get("reason") or None

    if tool_name == "accuse":
        target = args.get("target")
        message_text = args.get("reason")

    return AgentAction(
        tool_name=tool_name,
        target=target,
        message=message_text,
        raw_reasoning=raw_reasoning,
    )


class LLMClient:
    def __init__(self, role: Role, agent_name: str | None = None, model: str = "openai/gpt-oss-120b"):
        self.role = role
        self.agent_name = agent_name
        self.model = model
        self.client = _get_client(role, agent_name)

    @traceable(name="get_agent_action")
    def get_agent_action(self, system_prompt: str, available_tools: list[str]) -> AgentAction:
        tools = _build_groq_tools(available_tools)

        max_retries = 3
        last_error = None

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": "What is your action this tick?"},
                    ],
                    tools=tools,
                    tool_choice="auto",
                    temperature=0.8,
                    max_tokens=2048,
                )
                return _parse_tool_call(response, available_tools)

            except Exception as e:
                last_error = e
                print(f"[LLM ERROR] {self.role.value} attempt {attempt + 1}/{max_retries} failed: {e}")
                time.sleep(1.5 * (attempt + 1))  # simple backoff

        # all retries exhausted — fail safe instead of crashing the whole game loop
        print(f"[LLM FALLBACK] {self.role.value} exhausted retries, defaulting to silence.")
        return AgentAction(
            tool_name="speak",
            target=None,
            message="(silence)",
            raw_reasoning=f"[LLM call failed after {max_retries} attempts: {last_error}]",
        )