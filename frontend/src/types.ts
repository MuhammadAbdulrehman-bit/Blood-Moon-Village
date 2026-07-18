export type Phase = "night" | "conference" | "day";
export type Winner = "wolves" | "village" | null;

export interface GameStartResponse {
  status: string;
  round: number;
  phase: Phase;
  agents: string[];
}

export interface GameAdvanceResponse {
  phase_completed: Phase;
  winner: Winner;
  round: number;
  alive_agents: string[];
}

export interface GameStatusResponse {
  round: number;
  phase: Phase;
  tick: number;
  winner: Winner;
  alive_agents: string[];
  dead_agents: string[];
}

export interface PublicLogResponse {
  total_entries: number;
  entries: string[];
}

export interface WolfChannelLogResponse {
  total_entries: number;
  entries: string[];
}

export interface MapStateResponse {
  rooms: Record<string, string[]>;
  agent_positions: Record<string, string>;
}

export interface MapAdjacencyResponse {
  adjacency: Record<string, string[]>;
}