import type { MapStateResponse, MapAdjacencyResponse } from "./types";
import "./MapView.css";

interface MapViewProps {
  mapState: MapStateResponse | null;
  adjacency?: MapAdjacencyResponse | null;
}

interface RoomConfig {
  id: string;
  name: string;
  subtitle?: string;
}

const ROOMS: RoomConfig[] = [
  { id: "attic", name: "Attic", subtitle: "The Hiding Spot" },
  { id: "library", name: "Library" },
  { id: "study", name: "Study" },
  { id: "hall", name: "Hall" },
  { id: "courtyard", name: "Courtyard" },
  { id: "kitchen", name: "Kitchen" },
  { id: "cellar", name: "Cellar" },
];

const agentInitials: Record<string, string> = {
  "Aldric": "Al",
  "Maren": "Ma",
  "Corvus": "Co",
  "Sylva": "Sy",
  "Brennan": "Br",
  "Isolde": "Is",
  "Theron": "Th",
  "Wren": "Wr",
};

const agentColors: Record<string, string> = {
  "Aldric": "#a6e3a1",
  "Maren": "#89b4fa",
  "Corvus": "#f9e2af",
  "Sylva": "#f38ba8",
  "Brennan": "#cba6f7",
  "Isolde": "#fab387",
  "Theron": "#94e2d5",
  "Wren": "#f5c2e7",
};

const getInitials = (name: string): string => {
  return agentInitials[name] || name.substring(0, 2);
};

const getColor = (name: string): string => {
  if (agentColors[name]) return agentColors[name];
  // Deterministic fallback color generation for any other agent names
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  const h = Math.abs(hash) % 360;
  return `hsl(${h}, 70%, 75%)`;
};

export default function MapView({ mapState, adjacency: _adjacency }: MapViewProps) {
  return (
    <div style={{ width: "100%", display: "flex", flexDirection: "column", alignItems: "center", position: "relative", zIndex: 2 }}>
      <div className="eyebrow">Seven Souls · One Hollow</div>
      <h2 style={{ fontFamily: "'Cinzel Decorative', serif", fontWeight: 900, fontSize: "1.9rem", margin: "6px 0 2px" }}>The Manor, Mapped</h2>
      <div className="subtitle-main">Where each soul stands, by candlelight and by blood moon</div>

      <div className="map-container">
        {ROOMS.map((room) => {
          const occupants = Array.from(new Set(mapState?.rooms[room.name] || []));
          const isOccupied = occupants.length > 0;
          return (
            <div key={room.id} id={room.id} className={`room ${isOccupied ? "occupied" : ""}`}>
              <span className="room-title">{room.name}</span>
              <span className="room-subtitle">{room.subtitle || "\u00A0"}</span>
              <div className="agent-dock">
                {occupants.map((agent) => (
                  <div
                    key={agent}
                    className="agent-badge"
                    style={{ backgroundColor: getColor(agent) }}
                    title={agent}
                  >
                    {getInitials(agent)}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
