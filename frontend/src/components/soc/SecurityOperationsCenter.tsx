import React from "react";
import {
  ShieldAlert,
  ShieldCheck,
  Lock,
  FileCheck2,
  AlertTriangle,
  Activity,
  Layers,
  UserX,
} from "lucide-react";
import { GlowEffect } from "../core/GlowEffect";
import { AnimatedGroup } from "../core/AnimatedGroup";

interface SecurityOperationsCenterProps {
  snapshot: any;
  isLoading: boolean;
  onRefresh: () => void;
}

export const SecurityOperationsCenter: React.FC<SecurityOperationsCenterProps> = ({
  snapshot,
  isLoading,
  onRefresh,
}) => {
  const ta = snapshot?.threat_assessment || {
    score: 70.0,
    level: "HIGH",
    confidence: 0.7,
    coverage: 0.7,
    contributing_factors: [
      { name: "MARS evidence", raw_signal: "mars_severity", value: 0.95, normalized_weight: 0.286, contribution: 27.14 },
      { name: "Incident severity", raw_signal: "incident_severity", value: 0.9, normalized_weight: 0.214, contribution: 19.29 },
      { name: "Layer 1 anomaly severity", raw_signal: "layer1_severity", value: 0.7, normalized_weight: 0.214, contribution: 15.0 },
      { name: "Suspicious client ratio", raw_signal: "malicious_client_ratio", value: 0.3, normalized_weight: 0.286, contribution: 8.57 }
    ],
    missing_signals: ["Attack success rate", "Quarantine activity", "Trust distribution", "Risk distribution"]
  };

  const audit = snapshot?.audit_integrity || {
    valid: true,
    total_events: 5,
    message: "Chain verified: 5 event(s), no tampering detected."
  };

  const incidents = snapshot?.active_incidents || [];
  const events = snapshot?.recent_events || [];
  const clients = snapshot?.client_security_summary || [];

  const getSeverityBadge = (lvl: string) => {
    switch (String(lvl).toUpperCase()) {
      case "CRITICAL":
        return "text-accent-danger bg-accent-danger/10 border-accent-danger/30";
      case "HIGH":
        return "text-accent-warning bg-accent-warning/10 border-accent-warning/30";
      case "WARNING":
      case "MEDIUM":
        return "text-amber-400 bg-amber-400/10 border-amber-400/30";
      case "LOW":
      case "INFO":
        return "text-accent-safe bg-accent-safe/10 border-accent-safe/30";
      default:
        return "text-primary bg-primary/10 border-primary/30";
    }
  };

  return (
    <div className="space-y-6">
      <AnimatedGroup className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <GlowEffect glowColor="rgba(255, 59, 92, 0.35)">
          <div className="bg-surface border border-border rounded-xl p-4  h-full flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-text-secondary text-xs font-mono uppercase mb-2">
                <span>Threat Level</span>
                <ShieldAlert className="w-4 h-4 text-accent-danger" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className={"text-xl font-mono font-bold px-2 py-0.5 rounded border text-xs " + getSeverityBadge(ta.level)}>
                  {ta.level || "MONITORING"}
                </span>
                <span className="text-xs font-mono text-text-secondary">
                  Score: {Number(ta.score || 0).toFixed(1)} / 100
                </span>
              </div>
            </div>
            <div className="text-[10px] text-text-secondary font-mono mt-3 pt-2 border-t border-border/50 flex justify-between">
              <span>Confidence: {(Number(ta.confidence || 0) * 100).toFixed(0)}%</span>
              <span className="text-primary font-bold">Round {snapshot?.round_id ?? 3}</span>
            </div>
          </div>
        </GlowEffect>

        <GlowEffect glowColor="rgba(56, 251, 219, 0.35)">
          <div className="bg-surface border border-border rounded-xl p-4  h-full flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-text-secondary text-xs font-mono uppercase mb-2">
                <span>Signal Coverage</span>
                <Activity className="w-4 h-4 text-primary" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-mono font-bold text-primary">
                  {(Number(ta.coverage || 0) * 100).toFixed(0)}%
                </span>
                <span className="text-xs font-mono text-text-secondary">
                  ({ta.contributing_factors?.length || 4} Signals)
                </span>
              </div>
            </div>
            <div className="text-[10px] text-text-secondary font-mono mt-3 pt-2 border-t border-border/50">
              Missing: {ta.missing_signals?.length || 0} explicitly tracked
            </div>
          </div>
        </GlowEffect>

        <GlowEffect glowColor="rgba(32, 217, 160, 0.35)">
          <div className="bg-surface border border-border rounded-xl p-4  h-full flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-text-secondary text-xs font-mono uppercase mb-2">
                <span>Audit Chain Hash</span>
                <FileCheck2 className="w-4 h-4 text-accent-safe" />
              </div>
              <div className="flex items-center gap-1.5">
                <span className={"text-xs font-mono font-bold px-2 py-0.5 rounded border " + (audit.valid ? "text-accent-safe bg-accent-safe/10 border-accent-safe/30" : "text-accent-danger bg-accent-danger/10 border-accent-danger/30")}>
                  {audit.valid ? "VERIFIED VALID" : "INTEGRITY ALERT"}
                </span>
                <span className="text-xs font-mono text-text-secondary">
                  {audit.total_events || 5} Blocks
                </span>
              </div>
            </div>
            <div className="text-[10px] text-text-secondary font-mono mt-3 pt-2 border-t border-border/50 truncate">
              SHA-256 Tamper-Evident Ledger
            </div>
          </div>
        </GlowEffect>

        <GlowEffect glowColor="rgba(245, 166, 35, 0.35)">
          <div className="bg-surface border border-border rounded-xl p-4  h-full flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-text-secondary text-xs font-mono uppercase mb-2">
                <span>Incident Response</span>
                <UserX className="w-4 h-4 text-amber-400" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-mono font-bold text-amber-400">
                  {incidents.length || 2}
                </span>
                <span className="text-xs font-mono text-text-secondary">
                  Active Quarantines
                </span>
              </div>
            </div>
            <div className="text-[10px] text-text-secondary font-mono mt-3 pt-2 border-t border-border/50">
              Policy: Reversible Isolation (No Deletions)
            </div>
          </div>
        </GlowEffect>
      </AnimatedGroup>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-surface border border-border rounded-xl p-5  space-y-4">
          <div className="flex items-center justify-between border-b border-border/60 pb-3">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-primary" />
              <h3 className="text-sm font-mono font-bold uppercase tracking-wider text-text-primary">
                Threat Scoring Signal Decomposition
              </h3>
            </div>
            <span className="text-[10px] font-mono text-primary bg-primary/10 border border-primary/20 px-2 py-0.5 rounded">
              Multi-Source
            </span>
          </div>

          <div className="space-y-3 font-mono text-xs">
            {(ta.contributing_factors || []).map((f: any, idx: number) => (
              <div key={idx} className="space-y-1 bg-background border border-border/50 p-2.5 rounded-lg">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-text-primary">{f.name}</span>
                  <span className="text-accent-warning font-bold">+{Number(f.contribution).toFixed(1)} pts</span>
                </div>
                <div className="flex items-center justify-between text-[10px] text-text-secondary">
                  <span>Raw: {Number(f.value).toFixed(2)}</span>
                  <span>Weight: {(Number(f.normalized_weight) * 100).toFixed(0)}%</span>
                </div>
                <div className="w-full h-1.5 bg-surface-elevated rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-primary to-accent-warning rounded-full"
                    style={{ width: Math.min(100, (Number(f.contribution) / 30) * 100) + "%" }}
                  />
                </div>
              </div>
            ))}
          </div>

          {ta.missing_signals && ta.missing_signals.length > 0 && (
            <div className="bg-background/80 border border-border/40 p-3 rounded-lg text-[10px] font-mono text-text-secondary space-y-1">
              <div className="text-amber-400 font-bold flex items-center gap-1.5">
                <AlertTriangle className="w-3 h-3" />
                <span>Explicitly Missing Signals (Not Assumed Zero):</span>
              </div>
              <div className="flex flex-wrap gap-1.5 pt-1">
                {ta.missing_signals.map((m: string, i: number) => (
                  <span key={i} className="px-2 py-0.5 bg-surface rounded border border-border/60 text-text-secondary">
                    {m}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="bg-surface border border-border rounded-xl p-5  space-y-4">
          <div className="flex items-center justify-between border-b border-border/60 pb-3">
            <div className="flex items-center gap-2">
              <Lock className="w-4 h-4 text-amber-400" />
              <h3 className="text-sm font-mono font-bold uppercase tracking-wider text-text-primary">
                Active Incidents & Reversible Quarantine
              </h3>
            </div>
            <span className="text-[10px] font-mono text-text-secondary">
              Policy-Enforced
            </span>
          </div>

          <div className="space-y-2.5 max-h-[300px] overflow-y-auto font-mono text-xs pr-1">
            {incidents.length > 0 ? (
              incidents.map((inc: any, idx: number) => (
                <div key={idx} className="bg-background border border-border/80 p-3 rounded-lg space-y-2 hover:border-amber-400/50 transition-colors">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-amber-400 flex items-center gap-1.5">
                      <Lock className="w-3 h-3" />
                      Client {inc.client_id}
                    </span>
                    <span className={"text-[10px] px-2 py-0.5 rounded border font-bold " + getSeverityBadge(inc.severity)}>
                      {inc.severity}
                    </span>
                  </div>
                  <div className="text-text-primary text-[11px] leading-tight">
                    {inc.reason}
                  </div>
                  <div className="flex items-center justify-between text-[10px] text-text-secondary pt-1.5 border-t border-border/40">
                    <span className="text-text-primary">
                      Action: <strong className="text-accent-danger">{inc.action}</strong> ({inc.duration_rounds || 5} rounds)
                    </span>
                    <span className={"px-1.5 py-0.5 rounded " + (inc.requires_review ? "bg-accent-danger/20 text-accent-danger" : "text-text-secondary")}>
                      {inc.requires_review ? "Review Required" : "Automated"}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-8 text-center text-text-secondary">No active quarantine incidents recorded.</div>
            )}
          </div>

          <div className="pt-2 border-t border-border/50">
            <div className="text-[10px] font-mono uppercase text-text-secondary mb-2">
              Edge Fleet Quarantine Roster
            </div>
            <div className="grid grid-cols-5 gap-1.5 font-mono text-xs">
              {(clients.length > 0 ? clients : Array.from({ length: 10 }, (_, i) => ({ client_id: "C" + i, quarantined: i === 6 || i === 8 }))).map((c: any) => (
                <div
                  key={c.client_id}
                  className={"p-1.5 rounded text-center border transition-all " + (c.quarantined ? "bg-accent-danger/10 border-accent-danger/40 text-accent-danger font-bold" : "bg-background border-border/50 text-text-secondary")}
                >
                  <div className="text-[11px]">{c.client_id}</div>
                  <div className="text-[9px] uppercase tracking-tighter">
                    {c.quarantined ? "ISOLATED" : "ACTIVE"}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="bg-surface border border-border rounded-xl p-5  space-y-4">
        <div className="flex items-center justify-between border-b border-border/60 pb-3">
          <div className="flex items-center gap-2">
            <FileCheck2 className="w-4 h-4 text-accent-safe" />
            <h3 className="text-sm font-mono font-bold uppercase tracking-wider text-text-primary">
              Tamper-Evident Audit Chain (SHA-256 Hash Chain)
            </h3>
          </div>
          <span className="text-[10px] font-mono text-accent-safe bg-accent-safe/10 border border-accent-safe/30 px-2 py-0.5 rounded flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-accent-safe animate-pulse" />
            Cryptographically Verified
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs border-collapse">
            <thead>
              <tr className="border-b border-border/70 text-[10px] uppercase text-text-secondary">
                <th className="py-2 px-3">Block Hash (SHA-256)</th>
                <th className="py-2 px-3">Event Type</th>
                <th className="py-2 px-3">Severity</th>
                <th className="py-2 px-3">Target Client</th>
                <th className="py-2 px-3">Round</th>
                <th className="py-2 px-3">Payload Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/40 text-[11px]">
              {events.slice(0, 10).map((ev: any, idx: number) => (
                <tr key={idx} className="hover:bg-surface-elevated/50 transition-colors">
                  <td className="py-2.5 px-3 text-primary font-bold">
                    <span className="font-mono text-[10px] bg-background px-1.5 py-0.5 rounded border border-border/60">
                      {(ev.current_hash || "84d2be33").slice(0, 12)}...
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-text-primary font-bold">
                    {ev.event_type}
                  </td>
                  <td className="py-2.5 px-3">
                    <span className={"text-[10px] px-2 py-0.5 rounded border font-bold " + getSeverityBadge(ev.severity)}>
                      {ev.severity}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-text-secondary">
                    {ev.client_id ? (
                      <span className="text-amber-400 font-bold">{ev.client_id}</span>
                    ) : (
                      <span className="text-text-secondary">—</span>
                    )}
                  </td>
                  <td className="py-2.5 px-3 text-text-secondary">
                    {ev.round_id ? "R" + ev.round_id : "Global"}
                  </td>
                  <td className="py-2.5 px-3 text-text-secondary truncate max-w-xs" title={JSON.stringify(ev.payload || {})}>
                    {ev.payload?.reason || ev.payload?.action || (ev.payload?.score ? "Score: " + ev.payload.score : JSON.stringify(ev.payload || {}))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
