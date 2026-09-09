/**
 * NetworkTopologyGraph — SVG Radial Network Topology
 * Mirrors the Plotly network graph from the Streamlit arena.
 * Central FED SERVER + 10 client nodes in deterministic radial layout.
 */

import React from "react";
import type { ArenaNetworkNode, VisualState } from "../../types/telemetry";

interface NetworkTopologyGraphProps {
  nodes: Record<string, ArenaNetworkNode>;
  selectedClient: string | null;
  onSelectClient: (cid: string) => void;
}

const STATE_COLORS: Record<string, string> = {
  TRUSTED: "#00E676",
  TRAINING: "#00E5FF",
  TRANSMITTING: "#00E5FF",
  FLAGGED: "#FF7043",
  QUARANTINED: "#FF1744",
};

const STATE_LABELS: Record<string, string> = {
  TRUSTED: "Trusted",
  TRAINING: "Training",
  TRANSMITTING: "Transmitting",
  FLAGGED: "Flagged",
  QUARANTINED: "Quarantined",
};

export const NetworkTopologyGraph: React.FC<NetworkTopologyGraphProps> = ({
  nodes,
  selectedClient,
  onSelectClient,
}) => {
  const W = 520;
  const H = 420;
  const CX = W / 2;
  const CY = H / 2;

  const toSVG = (x: number, y: number): [number, number] => [x * W, y * H];

  const clientList = Object.values(nodes);

  return (
    <div className="relative w-full" style={{ background: "#0D1117", borderRadius: 8, border: "1px solid #30363D" }}>
      <div className="flex items-center justify-between px-4 pt-3 pb-1">
        <span className="text-xs font-bold font-mono text-[#00E5FF] uppercase tracking-wider">
          🌐 Federated Network Topology
        </span>
        <div className="flex gap-3">
          {[["TRUSTED","#00E676"],["FLAGGED","#FF7043"],["QUARANTINED","#FF1744"],["TRAINING","#00E5FF"]].map(([s,c]) => (
            <span key={s} className="flex items-center gap-1 text-[10px] font-mono text-[#8B949E]">
              <span className="w-2 h-2 rounded-full inline-block" style={{ background: c }} />
              {STATE_LABELS[s]}
            </span>
          ))}
        </div>
      </div>

      <svg viewBox={`0 0 ${W} ${H}`} width="100%" height="auto">
        <defs>
          <radialGradient id="serverGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#00E5FF" stopOpacity="0.25" />
            <stop offset="100%" stopColor="#00E5FF" stopOpacity="0" />
          </radialGradient>
        </defs>

        {clientList.map((node) => {
          const [nx, ny] = toSVG(node.x, node.y);
          const isQuarantined = node.visual_state === "QUARANTINED";
          const color = STATE_COLORS[node.visual_state] || "#58A6FF";
          return (
            <line
              key={`link-${node.client_id}`}
              x1={nx} y1={ny} x2={CX} y2={CY}
              stroke={isQuarantined ? "#FF1744" : color}
              strokeWidth={isQuarantined ? 1 : 1.5}
              strokeOpacity={isQuarantined ? 0.25 : 0.4}
              strokeDasharray={isQuarantined ? "4 4" : "none"}
            />
          );
        })}

        <circle cx={CX} cy={CY} r={36} fill="url(#serverGlow)" />
        <circle cx={CX} cy={CY} r={26} fill="#161B22" stroke="#00E5FF" strokeWidth={2} />
        <text x={CX} y={CY - 5} textAnchor="middle" fontSize={8} fontWeight="bold" fill="#00E5FF" fontFamily="monospace">FED</text>
        <text x={CX} y={CY + 7} textAnchor="middle" fontSize={8} fontWeight="bold" fill="#00E5FF" fontFamily="monospace">SERVER</text>

        {clientList.map((node) => {
          const [nx, ny] = toSVG(node.x, node.y);
          const color = STATE_COLORS[node.visual_state] || "#58A6FF";
          const isSelected = selectedClient === node.client_id;
          const isQuarantined = node.visual_state === "QUARANTINED";

          return (
            <g key={node.client_id} onClick={() => onSelectClient(node.client_id)} style={{ cursor: "pointer" }}>
              {isSelected && (
                <circle cx={nx} cy={ny} r={19} fill="none" stroke={color} strokeWidth={2} strokeDasharray="3 2" strokeOpacity={0.8} />
              )}
              {isQuarantined && (
                <>
                  <line x1={nx-8} y1={ny-8} x2={nx+8} y2={ny+8} stroke="#FF1744" strokeWidth={1.5} strokeOpacity={0.6} />
                  <line x1={nx+8} y1={ny-8} x2={nx-8} y2={ny+8} stroke="#FF1744" strokeWidth={1.5} strokeOpacity={0.6} />
                </>
              )}
              <circle cx={nx} cy={ny} r={14} fill="#161B22" stroke={color} strokeWidth={isSelected ? 2.5 : 1.5} />
              <text x={nx} y={ny + 4} textAnchor="middle" fontSize={9} fontWeight="bold" fill={color} fontFamily="monospace">
                {node.client_id}
              </text>
            </g>
          );
        })}
      </svg>

      <div className="px-4 pb-3 flex items-center justify-between text-[10px] font-mono text-[#6E7681]">
        <span>10 Edge Clients · 1 Federated Server · Deterministic Radial Layout</span>
        {selectedClient && <span className="text-[#00E5FF]">Selected: <b>{selectedClient}</b></span>}
      </div>
    </div>
  );
};
