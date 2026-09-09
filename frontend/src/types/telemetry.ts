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

export interface ClientTrustRecord {
  client_id: string;
  trust_score: number;
  trust_level: "TRUSTED" | "MONITORED" | "SUSPICIOUS" | "HIGH_RISK" | "QUARANTINED";
  anomaly_count: number;
  mars_incident_count: number;
  clean_round_count: number;
  incident_count: number;
  last_updated_round?: number | null;
  history: Array<{
    round_id: number;
    delta: number;
    new_score: number;
    reason: string;
    trust_level_after: string;
  }>;
}

export interface SecurityDecisionData {
  round_id: number;
  threat_level: "MINIMAL" | "LOW" | "ELEVATED" | "HIGH" | "CRITICAL";
  risk_level: string;
  threat_score: number;
  routing_action: "STANDARD" | "HEIGHTENED_MONITORING" | "ISOLATE_SUSPECTS" | "EMERGENCY_FALLBACK";
  recommended_action: string;
  active_defenses: string[];
  escalation_triggered: boolean;
  monitoring_required: boolean;
  aggregation_recommendation: string;
  reason: string;
  evidence: Record<string, any>;
  recommended_actions: string[];
  confidence: number;
  coverage: number;
  mode: string;
}

export interface SecurityIntelligenceSummary {
  trust_summary: {
    total_clients: number;
    average_trust_score: number;
    trust_level_counts: Record<string, number>;
    quarantined_clients: string[];
    monitored_clients: string[];
  };
  latest_decision: SecurityDecisionData | null;
  threat_trend: number[];
  is_escalated: boolean;
  mode: string;
  active_defenses: string[];
}

