/**
 * NetworkTopologyGraph — SVG Radial Network Topology
 * Responsive, viewport-safe, design-token compliant.
 * Central FED SERVER + 10 client nodes in deterministic radial layout.
 */

import React from "react";
import type { ArenaNetworkNode } from "../../types/telemetry";

interface NetworkTopologyGraphProps {
  nodes: Record<string, ArenaNetworkNode>;
  selectedClient: string | null;
  onSelectClient: (cid: string) => void;
}

const STATE_COLORS: Record<string, string> = {
  TRUSTED: "var(--green)",
  TRAINING: "var(--cyan)",
  TRANSMITTING: "var(--cyan)",
  FLAGGED: "var(--amber)",
  QUARANTINED: "var(--red)",
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
  const H = 400;
  const CX = W / 2;
  const CY = H / 2;

  const toSVG = (x: number, y: number): [number, number] => [x * W, y * H];

  const clientList = Object.values(nodes);

  return (
    <div className="flex flex-col justify-between h-full bg-[var(--bg-base)] rounded-xl border border-[var(--border-subtle)] p-4">
      {/* Header with Title & Legend Chips */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-[var(--border-subtle)] shrink-0">
        <span className="text-xs font-semibold text-[var(--cyan)] uppercase tracking-wider flex items-center gap-1.5">
          <span>🌐</span> Federated Network Topology
        </span>
        <div className="flex flex-wrap gap-2">
          {[
            ["TRUSTED", "var(--green)", "ds-chip-trusted"],
            ["TRAINING", "var(--cyan)", "ds-chip-info"],
            ["FLAGGED", "var(--amber)", "ds-chip-warning"],
            ["QUARANTINED", "var(--red)", "ds-chip-quarantined"],
          ].map(([s, c, chipCls]) => (
            <span key={s} className={`ds-chip ${chipCls} text-[10px] py-0.5 px-2`}>
              {STATE_LABELS[s]}
            </span>
          ))}
        </div>
      </div>

      {/* SVG Canvas - Scales Responsively */}
      <div className="relative flex-1 flex items-center justify-center min-h-[300px] max-h-[400px] overflow-hidden">
        <svg 
          viewBox={`0 0 ${W} ${H}`} 
          preserveAspectRatio="xMidYMid meet"
          className="w-full h-full max-h-[380px]"
        >
          <defs>
            <radialGradient id="serverGlow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#22D3EE" stopOpacity="0.30" />
              <stop offset="100%" stopColor="#22D3EE" stopOpacity="0" />
            </radialGradient>
            <radialGradient id="quarantineGlow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#FF4D6D" stopOpacity="0.35" />
              <stop offset="100%" stopColor="#FF4D6D" stopOpacity="0" />
            </radialGradient>
          </defs>

          {/* Links between Clients and Federated Server */}
          {clientList.map((node) => {
            const [nx, ny] = toSVG(node.x, node.y);
            const isQuarantined = node.visual_state === "QUARANTINED";
            const color = STATE_COLORS[node.visual_state] || "#22D3EE";
            return (
              <line
                key={`link-${node.client_id}`}
                x1={nx} y1={ny} x2={CX} y2={CY}
                stroke={isQuarantined ? "#FF4D6D" : color}
                strokeWidth={isQuarantined ? 1 : 1.5}
                strokeOpacity={isQuarantined ? 0.2 : 0.45}
                strokeDasharray={isQuarantined ? "4 4" : "none"}
              />
            );
          })}

          {/* Central Federated Server Node */}
          <circle cx={CX} cy={CY} r={42} fill="url(#serverGlow)" />
          <circle cx={CX} cy={CY} r={28} fill="#0A1330" stroke="#22D3EE" strokeWidth={2.5} />
          <text x={CX} y={CY - 5} textAnchor="middle" fontSize={8} fontWeight="bold" fill="#22D3EE" fontFamily="JetBrains Mono">
            FED
          </text>
          <text x={CX} y={CY + 8} textAnchor="middle" fontSize={8} fontWeight="bold" fill="#22D3EE" fontFamily="JetBrains Mono">
            SERVER
          </text>

          {/* Client Nodes in Radial Ring */}
          {clientList.map((node) => {
            const [nx, ny] = toSVG(node.x, node.y);
            const color = STATE_COLORS[node.visual_state] || "#22D3EE";
            const isSelected = selectedClient === node.client_id;
            const isQuarantined = node.visual_state === "QUARANTINED";

            return (
              <g 
                key={node.client_id} 
                onClick={() => onSelectClient(node.client_id)} 
                className="cursor-pointer transition-transform hover:scale-110"
              >
                {isSelected && (
                  <circle 
                    cx={nx} cy={ny} r={22} 
                    fill="none" 
                    stroke="#22D3EE" 
                    strokeWidth={2} 
                    strokeDasharray="4 2" 
                    strokeOpacity={0.8} 
                  />
                )}
                {isQuarantined && (
                  <>
                    <circle cx={nx} cy={ny} r={20} fill="url(#quarantineGlow)" />
                    <line x1={nx-9} y1={ny-9} x2={nx+9} y2={ny+9} stroke="#FF4D6D" strokeWidth={2} strokeOpacity={0.8} />
                    <line x1={nx+9} y1={ny-9} x2={nx-9} y2={ny+9} stroke="#FF4D6D" strokeWidth={2} strokeOpacity={0.8} />
                  </>
                )}
                <circle 
                  cx={nx} cy={ny} r={15} 
                  fill="#0F1C42" 
                  stroke={color} 
                  strokeWidth={isSelected ? 3 : 2} 
                />
                <text 
                  x={nx} y={ny + 4} 
                  textAnchor="middle" 
                  fontSize={9} 
                  fontWeight="bold" 
                  fill={color} 
                  fontFamily="JetBrains Mono"
                >
                  {node.client_id}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Footer Info */}
      <div className="pt-3 border-t border-[var(--border-subtle)] flex items-center justify-between text-[11px] font-mono text-[var(--text-muted)] shrink-0">
        <span>10 Edge Nodes · 1 Central Coordinator</span>
        {selectedClient ? (
          <span className="text-[var(--cyan)] font-medium">Selected Inspector: <b>{selectedClient}</b></span>
        ) : (
          <span>Click any node to inspect</span>
        )}
      </div>
    </div>
  );
};
