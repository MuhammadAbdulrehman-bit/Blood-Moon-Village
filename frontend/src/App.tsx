import { useState, useRef, useCallback, useEffect } from "react";
import { api } from "./api";
import type { GameStatusResponse, MapStateResponse, MapAdjacencyResponse } from "./types";
import MapView from "./MapView";
import AgentCards from "./AgentCards";
import "./index.css";

function classifyEntry(entry: string): string {
  if (entry.includes("[DEATH")) return "death";
  if (entry.includes("[SPEAK]")) return "speak";
  if (entry.includes("[MOVE]")) return "move";
  if (entry.includes("[VOTE]") || entry.toLowerCase().includes("lynch")) return "vote";
  if (entry.includes("[INSPECT]")) return "inspect";
  return "";
}

export default function App() {
  const [status, setStatus] = useState<GameStatusResponse | null>(null);
  const [mapState, setMapState] = useState<MapStateResponse | null>(null);
  const [mapAdjacency, setMapAdjacency] = useState<MapAdjacencyResponse | null>(null);
  const [log, setLog] = useState<string[]>([]);
  const [wolfLog, setWolfLog] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [autoOn, setAutoOn] = useState(false);
  const [intervalSec, setIntervalSec] = useState(4);
  const autoTimerRef = useRef<number | null>(null);
  const logEndRef = useRef<HTMLDivElement | null>(null);
  const wolfLogEndRef = useRef<HTMLDivElement | null>(null);
  const [isAdvancing, setIsAdvancing] = useState(false);
  const [activeTab, setActiveTab] = useState<"game" | "map" | "cards" | "wolves">("game");

  useEffect(() => {
    document.body.classList.toggle("night", status?.phase === "night");
  }, [status?.phase]);

  const refresh = useCallback(async () => {
    try {
      const [statusRes, logRes, wolfLogRes, mapRes, adjacencyRes] = await Promise.all([
        api.getStatus(),
        api.getPublicLog(500),
        api.getWolfChannelLog(500),
        api.getMapState(),
        api.getMapAdjacency(),
      ]);
      setStatus(statusRes);
      setLog(logRes.entries);
      setWolfLog(wolfLogRes.entries);
      setMapState(mapRes);
      setMapAdjacency(adjacencyRes);
      setError(null);
      setTimeout(() => {
        logEndRef.current?.scrollIntoView({ behavior: "smooth" });
        wolfLogEndRef.current?.scrollIntoView({ behavior: "smooth" });
      }, 50);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const handleStart = async () => {
    try {
      await api.startGame();
      setLog([]);
      setWolfLog([]);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

    const handleAdvance = useCallback(async () => {
    if (isAdvancing) return;
    setIsAdvancing(true);
    try {
      await api.advanceTick();
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setAutoOn(false);
    } finally {
      setIsAdvancing(false);
    }
  }, [refresh, isAdvancing]);

  const handleAdvanceOneTick = useCallback(async () => {
    if (isAdvancing) return;
    setIsAdvancing(true);
    try {
      await api.advanceOneTick();
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setAutoOn(false);
    } finally {
      setIsAdvancing(false);
    }
  }, [refresh, isAdvancing]);

  const toggleAuto = (checked: boolean) => {
    setAutoOn(checked);
    if (checked) {
      autoTimerRef.current = window.setInterval(handleAdvance, intervalSec * 1000);
    } else if (autoTimerRef.current !== null) {
      clearInterval(autoTimerRef.current);
      autoTimerRef.current = null;
    }
  };

  const deadSet = new Set(status?.dead_agents ?? []);
  const aliveSet = new Set(status?.alive_agents ?? []);
  const allAgents = [...aliveSet, ...deadSet];

  return (
    <div id="app">
      <header>
        <div className="eyebrow">Seven Souls · One Hollow</div>
        <h1>Blood Moon Village — Dashboard</h1>
        <div id="status-bar">
          <span>Round {status?.round ?? "-"}</span>
          <span>Phase: {status?.phase ?? "-"}</span>
          <span>Tick {status?.tick ?? "-"}</span>
          {status?.winner && <span id="winner-label">WINNER: {status.winner.toUpperCase()}</span>}
        </div>
        <div id="controls">
          <button onClick={handleStart}>Start Game</button>
          <button onClick={handleAdvance} disabled={isAdvancing}>
            {isAdvancing ? "Advancing..." : "Advance"}
          </button>
          <button onClick={handleAdvanceOneTick} disabled={isAdvancing}>
            Advance 1 Tick
          </button>
          <label>
            <input
              type="checkbox"
              checked={autoOn}
              onChange={(e) => toggleAuto(e.target.checked)}
            />
            Auto-advance every
          </label>
          <input
            type="number"
            value={intervalSec}
            min={1}
            style={{ width: 50 }}
            onChange={(e) => setIntervalSec(Math.max(1, parseInt(e.target.value, 10) || 4))}
          />
          s
        </div>
        {error && <div id="error-banner">{error}</div>}
      </header>

      <div id="tabs">
        <button
          className={activeTab === "game" ? "tab-btn active" : "tab-btn"}
          onClick={() => setActiveTab("game")}
        >
          Game Dashboard
        </button>
        <button
          className={activeTab === "map" ? "tab-btn active" : "tab-btn"}
          onClick={() => setActiveTab("map")}
        >
          Live Map
        </button>
        <button
          className={activeTab === "cards" ? "tab-btn active" : "tab-btn"}
          onClick={() => setActiveTab("cards")}
        >
          Agent Cards
        </button>
        <button
          className={activeTab === "wolves" ? "tab-btn active" : "tab-btn"}
          onClick={() => setActiveTab("wolves")}
        >
          Wolf Channel
        </button>
      </div>

      {activeTab === "game" ? (
        <main>
          <section id="agents-panel">
            <h2>Agents</h2>
            <div id="agent-list">
              {allAgents.map((name) => {
                const isDead = deadSet.has(name);
                const room = mapState?.agent_positions[name];
                return (
                  <div key={name} className={`agent-row${isDead ? " dead" : ""}`}>
                    <span>{name}</span>
                    <span className="agent-room">{isDead ? "eliminated" : room ?? "?"}</span>
                  </div>
                );
              })}
            </div>
          </section>

          <section id="log-panel">
            <h2>Log</h2>
            <div id="log-feed">
              {log.map((entry, i) => (
                <div key={i} className={`log-entry ${classifyEntry(entry)}`}>
                  {entry}
                </div>
              ))}
              <div ref={logEndRef} />
            </div>
          </section>
        </main>
      ) : activeTab === "map" ? (
        <div style={{ padding: "0 20px" }}>
          <MapView mapState={mapState} adjacency={mapAdjacency} />
        </div>
      ) : activeTab === "cards" ? (
        <div style={{ padding: "0 20px" }}>
          <AgentCards allAgents={allAgents} deadAgents={deadSet} />
        </div>
      ) : (
        <main>
          <section id="wolf-panel" style={{ width: "100%", maxWidth: "800px", margin: "0 auto" }}>
            <h2>Wolf Channel (Internal)</h2>
            <div id="wolf-feed" className="wolf-feed">
              {wolfLog.map((entry, i) => (
                <div key={i} className="log-entry wolf-entry">
                  {entry}
                </div>
              ))}
              <div ref={wolfLogEndRef} />
            </div>
          </section>
        </main>
      )}
    </div>
  );
}