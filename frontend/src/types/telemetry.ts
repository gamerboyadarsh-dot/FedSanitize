export interface ClientSecurityRecord {
  client_id: string;
  is_malicious: boolean;
  attack_type: string;
  update_norm: number;
  cosine_similarity: number;
  norm_score: number;
  layer1_status: "PASS" | "FLAGGED";
  layer1_reason: string;
  cbe: number | null;
  mars_cluster: number | null;
  mars_status: "PASS" | "FLAGGED" | "SKIPPED";
  final_status: "TRUSTED" | "QUARANTINED";
}

export interface DetectionMetrics {
  tp: number;
  fp: number;
  tn: number;
  fn: number;
  precision: number;
  recall: number;
  f1_score: number;
  detection_rate: number;
}

export interface AggregationMeta {
  method: string;
  beta?: number;
  num_inputs?: number;
}

export interface RoundRecord {
  round: number;
  attack_type: string;
  total_clients: number;
  clean_accuracy: number;
  backdoor_asr: number;
  trusted_clients: string[];
  quarantined_clients: string[];
  layer1_quarantined: string[];
  mars_quarantined: string[];
  detection: DetectionMetrics;
  client_security_records: Record<string, ClientSecurityRecord>;
  aggregation: AggregationMeta;
  distance_matrix?: number[][];
  log: string;
}

export interface ClientSummary {
  client_id: string;
  is_malicious: boolean;
  attack_type: string;
  sample_count: number;
  latest_record?: ClientSecurityRecord | null;
}

export interface FederatedConfig {
  num_clients: number;
  num_rounds: number;
  local_epochs: number;
  local_batch_size: number;
  local_lr: number;
  local_momentum: number;
  iid: boolean;
}

export interface DefenseConfig {
  layer1_norm_threshold: number;
  layer1_mad_multiplier: number;
  layer1_min_cosine: number;
  mars_cbe_top_p: number;
  mars_malignity_threshold: number;
  mars_wasserstein_p: number;
  trimmed_mean_beta: number;
}

export interface AttackConfig {
  num_malicious_clients: number;
  sign_flip_gamma: number;
  random_byzantine_scale: number;
  extreme_update_gamma: number;
  backdoor_trigger_size: number;
  backdoor_target_class: number;
  backdoor_poison_ratio: number;
}

export interface ConfigData {
  system: {
    random_seed: number;
    device: string;
    log_level: string;
  };
  model: {
    num_classes: number;
    fc_hidden: number;
  };
  federated: FederatedConfig;
  defense: DefenseConfig;
  attack: AttackConfig;
}

// ─────────────────────────────────────────────────────────────
// Live Attack Arena Types
// ─────────────────────────────────────────────────────────────

export type VisualState = "TRUSTED" | "FLAGGED" | "QUARANTINED" | "TRAINING" | "TRANSMITTING";

export interface ArenaNetworkNode {
  client_id: string;
  x: number;
  y: number;
  visual_state: VisualState;
  is_malicious: boolean;
}

export interface ArenaSecurityEvent {
  event_type: string;
  severity: "INFO" | "WARNING" | "HIGH" | "CRITICAL";
  message: string;
  client_id: string | null;
  layer: string | null;
  timestamp: number;
  payload: Record<string, unknown>;
}

export interface ArenaTimelineStep {
  step_index: number;
  scene: string;
  description: string;
  event: ArenaSecurityEvent;
}

export interface ArenaClientRecord {
  attack_type: string;
  is_malicious: boolean;
  update_norm: number;
  cosine_similarity: number;
  layer1_status: "PASS" | "FLAGGED";
  layer1_reason: string;
  cbe_concentration_ratio: number;
  cluster_id: number | null;
  mars_status: "PASS" | "FLAGGED" | "SKIPPED";
  mars_reason: string;
  final_status: "TRUSTED" | "QUARANTINED";
}

export interface ArenaScenarioNarrative {
  attack_type: string;
  title: string;
  headline: string;
  story_steps: string[];
  mitigating_layer: string;
  forensic_focus: string;
  technical_explanation: string;
  threat_severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
}

export interface ArenaSummary {
  round_id: number;
  attack_type: string;
  clean_accuracy: number;
  backdoor_asr: number;
  threat_tier: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  threat_score: number;
  quarantined_count: number;
  trusted_count: number;
  quarantined_clients: string[];
  trusted_clients: string[];
  l1_quarantined: string[];
  mars_quarantined: string[];
}

export interface ArenaData {
  round_index: number;
  total_rounds: number;
  round_record: Record<string, unknown>;
  network_nodes: Record<string, ArenaNetworkNode>;
  timeline_steps: ArenaTimelineStep[];
  client_security_records: Record<string, ArenaClientRecord>;
  mars_data: Record<string, unknown>;
  scenario_narrative: ArenaScenarioNarrative;
  summary: ArenaSummary;
  scenario_labels: Record<string, string>;
}

