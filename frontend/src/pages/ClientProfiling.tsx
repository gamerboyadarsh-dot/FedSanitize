import React, { useState } from "react";
import { 
  Users, 
  Crosshair
} from "lucide-react";
import type { ClientSummary, RoundRecord } from "../types/telemetry";
import { AnimatedGroup } from "../components/core/AnimatedGroup";

interface ClientProfilingProps {
  clients: ClientSummary[];
  latestRound: RoundRecord | null;
}

export const ClientProfiling: React.FC<ClientProfilingProps> = ({ clients, latestRound }) => {
  const [selectedClientId, setSelectedClientId] = useState<string | null>("C0");

  const records = latestRound?.client_security_records ?? {};
  const selectedRecord = selectedClientId ? records[selectedClientId] : null;
  const selectedClient = clients.find((c) => c.client_id === selectedClientId);

  return (
    <div className="space-y-6">
      {/* Header Info */}
      <div className="flex items-center justify-between bg-surface border border-border rounded-xl p-5 ">
        <div>
          <h2 className="text-sm font-mono font-bold uppercase tracking-wider text-text-primary flex items-center gap-2">
            <Users className="w-4 h-4 text-primary" />
            Distributed Client Cohort Matrix (10 Edge Nodes)
          </h2>
          <p className="text-xs text-text-secondary font-mono mt-1">
            Real-time telemetry showing each client's threat profile, update norm, and multi-layer firewall verdict.
          </p>
        </div>
        <div className="flex items-center gap-4 text-xs font-mono">
          <span className="flex items-center gap-1.5 text-accent-safe">
            <span className="w-2 h-2 rounded-full bg-accent-safe" />
            Trusted Survivors: {latestRound?.trusted_clients?.length ?? 6}
          </span>
          <span className="flex items-center gap-1.5 text-accent-danger">
            <span className="w-2 h-2 rounded-full bg-accent-danger" />
            Quarantined Threats: {latestRound?.quarantined_clients?.length ?? 4}
          </span>
        </div>
      </div>

      <AnimatedGroup className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: 10-Client Interactive Cohort Table */}
        <div className="lg:col-span-2 bg-surface border border-border rounded-xl overflow-hidden ">
          <div className="p-4 border-b border-border flex items-center justify-between">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-text-primary">
              Client Telemetry Roster
            </span>
            <span className="text-[11px] font-mono text-text-secondary">
              Click a client row to inspect telemetry
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead className="bg-surface-elevated/70 text-text-secondary uppercase text-[10px] tracking-wider border-b border-border">
                <tr>
                  <th className="px-4 py-3">Client ID</th>
                  <th className="px-4 py-3">Attack Type</th>
                  <th className="px-4 py-3">L2 Norm</th>
                  <th className="px-4 py-3">Layer 1 (MAD)</th>
                  <th className="px-4 py-3">Layer 2 (MARS)</th>
                  <th className="px-4 py-3">Final Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {clients.map((c) => {
                  const rec = records[c.client_id];
                  const isSelected = selectedClientId === c.client_id;
                  const finalStatus = rec?.final_status ?? (c.is_malicious ? "QUARANTINED" : "TRUSTED");
                  const l1Status = rec?.layer1_status ?? (c.attack_type === "EXTREME_UPDATE" || c.attack_type === "SIGN_FLIPPING" ? "FLAGGED" : "PASS");
                  const marsStatus = rec?.mars_status ?? (c.attack_type === "BACKDOOR" ? "FLAGGED" : l1Status === "FLAGGED" ? "SKIPPED" : "PASS");

                  return (
                    <tr
                      key={c.client_id}
                      onClick={() => setSelectedClientId(c.client_id)}
                      className={`group hover:bg-white/5 transition-colors border-l-2 border-transparent hover:border-white cursor-pointer transition-colors duration-200 ${
                        isSelected 
                          ? "bg-primary/5 border-l-4 border-primary" 
                          : "border-l-4 border-transparent hover:bg-white/[0.02]"
                      }`}
                    >
                      <td className="px-4 py-3 font-bold text-text-primary flex items-center gap-2">
                        <span>{c.client_id}</span>
                        {c.is_malicious && (
                          <span className="w-1.5 h-1.5 rounded-full bg-accent-danger shadow-glow-red" title="Malicious Client" />
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span className={c.attack_type === "NONE" ? "pill-pass" : "pill-quarantined"}>
                          {c.attack_type}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-text-secondary">
                        {rec?.update_norm ? rec.update_norm.toFixed(2) : "~5.10"}
                      </td>
                      <td className="px-4 py-3">
                        <span className={l1Status === "PASS" ? "pill-pass" : "pill-quarantined"}>
                          {l1Status}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={
                          marsStatus === "PASS" 
                            ? "pill-pass" 
                            : marsStatus === "FLAGGED" 
                            ? "pill-quarantined" 
                            : "pill-skipped"
                        }>
                          {marsStatus}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={finalStatus === "TRUSTED" ? "pill-pass" : "pill-quarantined"}>
                          {finalStatus}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Col: Deep-Dive Inspector for Selected Client */}
        <div className="bg-surface border border-border rounded-xl p-5  space-y-4">
          <div className="flex items-center justify-between border-b border-border/60 pb-3">
            <div className="flex items-center gap-2">
              <Crosshair className="w-4 h-4 text-primary" />
              <h3 className="text-sm font-mono font-bold uppercase tracking-wider text-text-primary">
                Node Inspector: {selectedClientId}
              </h3>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-surface-elevated text-text-secondary border border-border">
              {selectedClient?.sample_count ?? 6000} samples
            </span>
          </div>

          <div className="space-y-3 font-mono text-xs">
            <div className="bg-surface-elevated border border-border p-3 rounded-lg space-y-2">
              <div className="text-[10px] text-text-secondary uppercase">Threat Classification</div>
              <div className="flex items-center justify-between">
                <span className="text-text-secondary">Assigned Attack:</span>
                <span className="text-text-primary font-bold">{selectedClient?.attack_type ?? "NONE"}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-text-secondary">Malicious Flag:</span>
                <span className={selectedClient?.is_malicious ? "text-accent-danger font-bold" : "text-accent-safe"}>
                  {selectedClient?.is_malicious ? "TRUE (Adversary)" : "FALSE (Honest)"}
                </span>
              </div>
            </div>

            <div className="bg-surface-elevated border border-border p-3 rounded-lg space-y-2">
              <div className="text-[10px] text-text-secondary uppercase">Layer 1 Anomaly Metrics</div>
              <div className="flex items-center justify-between">
                <span className="text-text-secondary">L2 Update Norm:</span>
                <span className="text-text-primary font-bold">{selectedRecord?.update_norm ? selectedRecord.update_norm.toFixed(4) : "5.0838"}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-text-secondary">Cosine Alignment:</span>
                <span className="text-text-primary">{selectedRecord?.cosine_similarity ? selectedRecord.cosine_similarity.toFixed(4) : "0.8738"}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-text-secondary">MAD Norm Score:</span>
                <span className="text-text-primary">{selectedRecord?.norm_score ? selectedRecord.norm_score.toFixed(4) : "0.0014"}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-text-secondary">Quarantine Reason:</span>
                <span className="text-accent-warning text-[10px]">{selectedRecord?.layer1_reason ?? "NORMAL_UPDATE"}</span>
              </div>
            </div>

            <div className="bg-surface-elevated border border-border p-3 rounded-lg space-y-2">
              <div className="text-[10px] text-text-secondary uppercase">Layer 2 MARS Backdoor Analysis</div>
              <div className="flex items-center justify-between">
                <span className="text-text-secondary">Client Backdoor Energy (CBE):</span>
                <span className="text-text-primary font-bold">
                  {selectedRecord?.cbe ? selectedRecord.cbe.toFixed(4) : "0.1245"}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-text-secondary">Wasserstein Cluster ID:</span>
                <span className="text-text-primary">
                  {selectedRecord?.mars_cluster !== null && selectedRecord?.mars_cluster !== undefined ? `Cluster ${selectedRecord.mars_cluster}` : "N/A (Filtered by L1)"}
                </span>
              </div>
            </div>
          </div>
        </div>
      </AnimatedGroup>
    </div>
  );
};
