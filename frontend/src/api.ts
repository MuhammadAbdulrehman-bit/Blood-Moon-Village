import type {
  GameStartResponse,
  GameAdvanceResponse,
  GameStatusResponse,
  PublicLogResponse,
  MapStateResponse,
  MapAdjacencyResponse,
  WolfChannelLogResponse,
} from "./types";

const API_BASE = "http://127.0.0.1:8000";

async function post<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { method: "POST" });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`POST ${path} failed (${res.status}): ${text}`);
  }
  return res.json() as Promise<T>;
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`GET ${path} failed (${res.status}): ${text}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  startGame: () => post<GameStartResponse>("/game/start"),
  advanceTick: () => post<GameAdvanceResponse>("/game/advance"),
  advanceOneTick: () => post<GameStatusResponse>("/game/advance_one_tick"),
  getStatus: () => get<GameStatusResponse>("/game/status"),
  getPublicLog: (lastN = 500) =>
    get<PublicLogResponse>(`/logs/public?last_n=${lastN}`),
  getWolfChannelLog: (lastN = 500) =>
    get<WolfChannelLogResponse>(`/logs/wolf_channel?last_n=${lastN}`),
  getMapState: () => get<MapStateResponse>("/map/state"),
  getMapAdjacency: () => get<MapAdjacencyResponse>("/map/adjacency"),
};