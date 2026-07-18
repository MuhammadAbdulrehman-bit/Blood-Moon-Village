import React, { useState, useEffect, useMemo } from "react";
import "./AgentCards.css";

interface AgentCardsProps {
  allAgents: string[];
  deadAgents: Set<string>;
}

// Aesthetic mock data for agents
const AGENT_MOCK_DATA: Record<string, { human: string; role: string; roleClass: string; bio: string; isWolfClass?: boolean }> = {
  Aldric: { human: "👨‍🌾", role: "Villager", roleClass: "role-wolf", bio: "A quiet, hard-working blacksmith. Keeps his head down during discussions.", isWolfClass: true },
  Maren: { human: "🔮", role: "Seer", roleClass: "role-seer", bio: "An eccentric elder who studies constellations. Capable of probing deeply." },
  Corvus: { human: "👩‍⚕️", role: "Villager", roleClass: "role-villager", bio: "The village botanist. Observant and precise, tracks physical anomalies." },
  Sylva: { human: "👨‍⚕️", role: "Doctor", roleClass: "role-doctor", bio: "Equipped with critical medical contingencies. Protects targets from termination." },
  Brennan: { human: "🪵", role: "Villager", roleClass: "role-wolf", bio: "A robust woodcutter known for his boisterous laugh. Instincts can betray.", isWolfClass: true },
  Isolde: { human: "📜", role: "Villager", roleClass: "role-villager", bio: "The local scribe. Documenting environmental events and logs carefully." },
  Theron: { human: "🍞", role: "Villager", roleClass: "role-villager", bio: "Always energetic, baking bread for everyone." },
  Wren: { human: "🧵", role: "Villager", roleClass: "role-villager", bio: "The village tailor, quietly stitching secrets." },
};

const DEFAULT_MOCK = { human: "👤", role: "Villager", roleClass: "role-villager", bio: "An enigmatic resident of the village." };

export default function AgentCards({ allAgents, deadAgents }: AgentCardsProps) {
  const [rotation, setRotation] = useState(0);
  const [isHovered, setIsHovered] = useState(false);

  // Orbital rotation
  useEffect(() => {
    if (isHovered) return;
    const interval = setInterval(() => {
      setRotation((r) => r - 0.15);
    }, 30);
    return () => clearInterval(interval);
  }, [isHovered]);

  const handleCardClick = (index: number) => {
    const total = allAgents.length;
    if (total === 0) return;
    const targetAngle = -(index * (360 / total));
    setRotation(targetAngle);
  };

  const fireflies = useMemo(() => {
    return Array.from({ length: 14 }).map((_, i) => ({
      id: i,
      left: `${Math.random() * 100}vw`,
      top: `${55 + Math.random() * 40}vh`,
      animationDuration: `${7 + Math.random() * 6}s`,
      animationDelay: `${i * 120}ms`,
    }));
  }, []);

  const totalAlive = allAgents.filter((a) => !deadAgents.has(a)).length;

  return (
    <div className="cards-tab-container">
      <div className="vignette"></div>
      <div className="fx-layer">
        <div className="fog"></div>
        {fireflies.map((ff) => (
          <div
            key={ff.id}
            className="firefly"
            style={{
              left: ff.left,
              top: ff.top,
              animationDuration: ff.animationDuration,
              animationDelay: ff.animationDelay,
            }}
          ></div>
        ))}
      </div>

      <div className="masthead">
        <p className="subline">
          By candlelight they are neighbors. Beneath the crimson moon, something else answers to their names.
        </p>
        <div className="moon-dial"></div>
      </div>

      <div className="cards-controls">
        <span className="count-pill">
          {totalAlive === 1 ? "1 soul remains" : `${totalAlive} souls remain`}
        </span>
      </div>

      <div
        className="scene"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <div
          className="carousel"
          style={{ transform: `rotateX(-6deg) rotateY(${rotation}deg)` }}
        >
          {allAgents.map((agentName, index) => {
            const isDead = deadAgents.has(agentName);
            const data = AGENT_MOCK_DATA[agentName] || DEFAULT_MOCK;
            const angle = index * (360 / allAgents.length);
            const baseTransform = `rotateY(${angle}deg) translateZ(330px)`;
            
            // Generate visual ID A1, A2, etc.
            const agentId = `A${index + 1}`;

            let classNames = "card";
            if (isDead) classNames += " is-dead";
            else if (data.isWolfClass) classNames += " is-wolf";

            return (
              <div
                key={agentName}
                className={classNames}
                onClick={() => {
                  if (!isDead) handleCardClick(index);
                }}
                style={{
                  "--card-base-transform": baseTransform,
                  transform: isDead
                    ? `${baseTransform} translateY(44px) scale(0.95)`
                    : baseTransform,
                } as React.CSSProperties}
              >
                {data.isWolfClass && <div className="claw-marks"></div>}
                <div className="blood-splatter"></div>
                <div className="death-stamp">Cast Out</div>
                <div className="seal">{agentId}</div>
                <div className="avatar-frame">
                  <span className="human-form">{data.human}</span>
                  {data.isWolfClass && <span className="wolf-true-form">🐺</span>}
                  <span className="agent-id-badge">{agentId}</span>
                </div>
                <div className="agent-name">{agentName}</div>
                <div className={`role-badge ${data.roleClass}`}>
                  {/* Just showing the aesthetic role, will switch to 'Werewolf' via CSS styling natively during night if they are a wolf */}
                  {data.role}
                </div>
                <p className="agent-bio">{data.bio}</p>
              </div>
            );
          })}
        </div>
      </div>

      <footer className="cards-footer">Turn the wheel · click a face to draw it near</footer>
    </div>
  );
}
