import React from "react";
import type { ArenaClientRecord } from "../../types/telemetry";

interface Props {
  clientId: string;
  record: ArenaClientRecord;
  marsInfo?: Record<string, unknown>;
}

export const ClientDossier: React.FC<Props> = ({ clientId, record, marsInfo }) => {
  const isQuarantined = record.final_status === "QUARANTINED";
  const statusBg = isQuarantined ? "#FF1744" : "#00E676";
  const cbe = Number(record.cbe_concentration_ratio ?? (marsInfo?.cbe_concentration_ratio ?? 0));
  const clusterId = record.cluster_id ?? (marsInfo?.cluster_id as number | null) ?? null;
  const marsStatus = record.mars_status ?? "PASS";
  const marsReason = record.mars_reason ?? "BENIGN";

  return (
    <div style={{ background: "#161B22", border: "1px solid #30363D", borderRadius: 8, padding: 16, fontFamily: "monospace" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #30363D", paddingBottom: 10, marginBottom: 12 }}>
        <div>
          <span style={{ fontSize: 15, fontWeight: "bold", color: "#F0F6FC" }}>CLIENT FORENSIC DOSSIER: {clientId}</span>
          <span style={{ marginLeft: 8, fontSize: 11, background: record.is_malicious ? "#FF1744" : "#238636", color: "#FFF", padding: "2px 8px", borderRadius: 4 }}>
            {record.is_malicious ? "MALICIOUS" : "HONEST"}
          </span>
        </div>
        <div style={{ background: statusBg, color: "#0D1117", fontWeight: "bold", fontSize: 12, padding: "3px 10px", borderRadius: 4 }}>
          {record.final_status}
        </div>
      </div>

      {/* Attack profile */}
      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 11, color: "#8B949E", textTransform: "uppercase" }}>Adversarial Attack Profile</div>
        <div style={{ fontSize: 14, fontWeight: "bold", color: "#58A6FF" }}>{record.attack_type}</div>
      </div>

      {/* Layer 1 */}
      <div style={{ background: "#1C2128", border: "1px solid #30363D", borderRadius: 6, padding: 10, marginBottom: 10 }}>
        <div style={{ fontSize: 12, fontWeight: "bold", color: "#00E5FF", marginBottom: 6 }}>LAYER 1 — STATISTICAL ANOMALY FILTER</div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6, fontSize: 12 }}>
          <div><span style={{ color: "#8B949E" }}>Update Norm:</span> <b style={{ color: "#F0F6FC" }}>{record.update_norm.toFixed(4)}</b></div>
          <div><span style={{ color: "#8B949E" }}>Cosine Similarity:</span> <b style={{ color: "#F0F6FC" }}>{record.cosine_similarity.toFixed(4)}</b></div>
          <div><span style={{ color: "#8B949E" }}>L1 Status:</span> <b style={{ color: record.layer1_status === "FLAGGED" ? "#FF5252" : "#00E676" }}>{record.layer1_status}</b></div>
          <div><span style={{ color: "#8B949E" }}>L1 Diagnostic:</span> <span style={{ color: "#8B949E" }}>{record.layer1_reason}</span></div>
        </div>
      </div>

      {/* MARS */}
      <div style={{ background: "#1C2128", border: "1px solid #30363D", borderRadius: 6, padding: 10, marginBottom: 10 }}>
        <div style={{ fontSize: 12, fontWeight: "bold", color: "#00E5FF", marginBottom: 6 }}>LAYER 2 — MARS DEEP REPRESENTATION FORENSICS</div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6, fontSize: 12 }}>
          <div><span style={{ color: "#8B949E" }}>CBE Ratio:</span> <b style={{ color: "#F0F6FC" }}>{cbe.toFixed(4)} ({(cbe * 100).toFixed(1)}%)</b></div>
          <div><span style={{ color: "#8B949E" }}>Cluster ID:</span> <b style={{ color: "#F0F6FC" }}>{clusterId !== null ? clusterId : "N/A"}</b></div>
          <div><span style={{ color: "#8B949E" }}>MARS Status:</span> <b style={{ color: marsStatus === "FLAGGED" ? "#FF5252" : "#00E676" }}>{marsStatus}</b></div>
          <div><span style={{ color: "#8B949E" }}>MARS Reason:</span> <span style={{ color: "#8B949E" }}>{marsReason}</span></div>
        </div>
      </div>

      {/* Final decision */}
      <div style={{ background: isQuarantined ? "rgba(255,23,68,0.1)" : "rgba(0,230,118,0.1)", border: `1px solid ${statusBg}`, borderRadius: 6, padding: 10 }}>
        <div style={{ fontSize: 11, fontWeight: "bold", color: statusBg, textTransform: "uppercase" }}>FINAL SECURITY ACTION</div>
        <div style={{ fontSize: 13, fontWeight: "bold", color: "#F0F6FC", marginTop: 2 }}>
          {isQuarantined ? "QUARANTINED & ISOLATED" : "CLEARED FOR ROBUST AGGREGATION"}
        </div>
        <div style={{ fontSize: 12, color: "#8B949E", marginTop: 4 }}>
          Reason: {record.layer1_status === "FLAGGED" ? record.layer1_reason : marsReason}
        </div>
      </div>
    </div>
  );
};
