import { RoundRecord, ClientSummary, ConfigData } from "../types/telemetry";

const API_BASE = "http://127.0.0.1:8000";

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error("API offline");
  return res.json();
}

export async function fetchConfig(): Promise<ConfigData> {
  const res = await fetch(`${API_BASE}/config`);
  if (!res.ok) throw new Error("Failed to fetch configuration");
  return res.json();
}

export async function updateConfig(updates: Partial<ConfigData>): Promise<ConfigData> {
  const res = await fetch(`${API_BASE}/config`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updates),
  });
  if (!res.ok) throw new Error("Failed to update configuration");
  return res.json();
}

export async function fetchClients(): Promise<ClientSummary[]> {
  const res = await fetch(`${API_BASE}/clients`);
  if (!res.ok) throw new Error("Failed to fetch client roster");
  return res.json();
}

export async function setClientAttack(clientId: string, attackType: string) {
  const res = await fetch(`${API_BASE}/clients/${clientId}/attack`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ attack_type: attackType }),
  });
  if (!res.ok) throw new Error(`Failed to assign attack to ${clientId}`);
  return res.json();
}

export async function runRound(): Promise<RoundRecord> {
  const res = await fetch(`${API_BASE}/simulation/round`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to execute secure round");
  return res.json();
}

export async function resetSimulation() {
  const res = await fetch(`${API_BASE}/simulation/reset`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to reset simulation");
  return res.json();
}

export async function loadDemo(): Promise<{ rounds: number; history: RoundRecord[] }> {
  const res = await fetch(`${API_BASE}/simulation/load-demo`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to load demo experiment");
  return res.json();
}

export async function fetchHistory(): Promise<RoundRecord[]> {
  const res = await fetch(`${API_BASE}/experiments/history`);
  if (!res.ok) throw new Error("Failed to fetch experiment history");
  return res.json();
}

export async function fetchSecuritySummary(): Promise<any> {
  const res = await fetch(`${API_BASE}/security/summary`);
  if (!res.ok) throw new Error("Failed to fetch security summary");
  return res.json();
}

export async function fetchClientTrust(clientId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/security/clients/${clientId}/trust`);
  if (!res.ok) throw new Error(`Failed to fetch trust for ${clientId}`);
  return res.json();
}

export async function fetchAllClientTrust(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/security/clients/trust`);
  if (!res.ok) throw new Error("Failed to fetch all client trust records");
  return res.json();
}

export async function fetchSecurityDecisions(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/security/decisions`);
  if (!res.ok) throw new Error("Failed to fetch security decisions");
  return res.json();
}

