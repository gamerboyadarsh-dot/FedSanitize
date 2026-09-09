"""
FedSanitize — Security Intelligence: Trust Policy
=================================================
Centralized, deterministic, configuration-driven scoring logic.
No randomness. No side effects. Pure computation only.

All scoring rules live here. To change policy, change SecurityIntelligenceConfig.
"""

from __future__ import annotations
from typing import Optional

from ..contracts.security_context import SecurityContext
from ..contracts.client_record import ClientSecurityRecord
from ..contracts.security_decision import TrustUpdate
from .trust_models import TrustLevel, score_to_level, clamp_score


class TrustPolicy:
    """
    Pure, stateless scoring engine.

    Computes the trust score delta for a client given a SecurityContext
    and the client's current record. Returns a fully explainable TrustUpdate.

    All thresholds are injected via the config dict (sourced from
    SecurityIntelligenceConfig). No hardcoded magic numbers.
    """

    def __init__(self, config: dict):
        """
        Parameters
        ----------
        config : dict
            Policy thresholds. Expected keys (all have safe defaults):
              initial_score             : float = 75.0
              layer1_anomaly_penalty    : float = 10.0
              mars_suspect_penalty      : float = 20.0
              repeated_incident_penalty : float = 5.0
              clean_round_reward        : float = 3.0
              max_reward_per_round      : float = 3.0
              quarantine_penalty        : float = 15.0
        """
        self._cfg = config

    def _p(self, key: str, default: float) -> float:
        """Safe config lookup with type coercion."""
        try:
            return float(self._cfg.get(key, default))
        except (TypeError, ValueError):
            return default

    def compute_update(
        self,
        context: SecurityContext,
        record: ClientSecurityRecord,
    ) -> TrustUpdate:
        """
        Computes a TrustUpdate for a single client in a single round.

        Scoring logic (applied in order, all additive):
        -----------------------------------------------
        1. Layer 1 anomaly penalty  → -layer1_anomaly_penalty
        2. MARS suspect penalty     → -mars_suspect_penalty
        3. Repeated incident penalty → -(repeated_incident_penalty * penalty_multiplier)
           (penalty_multiplier = 1 if first offense, 2 if >= 3 incidents, 3 if >= 6)
        4. Quarantine penalty        → -quarantine_penalty (if final_status == QUARANTINED)
        5. Clean round reward        → +clean_round_reward (only if no anomaly this round)
        6. All deltas accumulated, score clamped to [0, 100]

        Returns
        -------
        TrustUpdate
            Explainable change record with previous score, delta, new score,
            reason text, and evidence dict.
        """
        prev_score = record.trust_score
        prev_level = score_to_level(prev_score)

        delta = 0.0
        reasons = []
        evidence = {}

        is_l1_anomaly = context.layer1_is_anomaly()
        is_mars_suspect = context.mars_is_suspect()
        is_quarantined_this_round = context.final_status() == "QUARANTINED"
        is_clean_this_round = (not is_l1_anomaly) and (not is_mars_suspect)

        evidence["layer1_anomaly"] = is_l1_anomaly
        evidence["mars_suspect"] = is_mars_suspect
        evidence["final_status"] = context.final_status()
        evidence["clean_this_round"] = is_clean_this_round
        evidence["prior_incident_count"] = record.incident_count
        evidence["prior_clean_rounds"] = record.clean_round_count

        # --- 1. Layer 1 anomaly penalty ---
        if is_l1_anomaly and context.has_layer1_signal():
            pen = self._p("layer1_anomaly_penalty", 10.0)
            delta -= pen
            reasons.append(f"L1_ANOMALY(-{pen:.1f})")
            evidence["layer1_reason"] = context.layer1_summary.get("reason", "UNKNOWN")

        # --- 2. MARS suspect penalty ---
        if is_mars_suspect and context.has_mars_signal():
            pen = self._p("mars_suspect_penalty", 20.0)
            delta -= pen
            reasons.append(f"MARS_SUSPECT(-{pen:.1f})")
            evidence["mars_reason"] = context.mars_summary.get("reason", "UNKNOWN")
            evidence["cbe_ratio"] = context.mars_cbe_ratio()

        # --- 3. Repeated incident penalty (escalating) ---
        if is_l1_anomaly or is_mars_suspect:
            total_incidents = record.incident_count  # prior count before this round
            rep_pen = self._p("repeated_incident_penalty", 5.0)
            if total_incidents >= 6:
                multiplier = 3
            elif total_incidents >= 3:
                multiplier = 2
            else:
                multiplier = 1
            # Only apply repeated penalty if there were prior incidents
            if total_incidents > 0:
                extra_pen = rep_pen * multiplier
                delta -= extra_pen
                reasons.append(f"REPEAT_INCIDENT_x{multiplier}(-{extra_pen:.1f})")
                evidence["repeat_multiplier"] = multiplier

        # --- 4. Quarantine penalty (on top of anomaly penalties) ---
        if is_quarantined_this_round:
            q_pen = self._p("quarantine_penalty", 15.0)
            delta -= q_pen
            reasons.append(f"QUARANTINED(-{q_pen:.1f})")

        # --- 5. Clean round reward (only if no incident at all this round) ---
        if is_clean_this_round:
            reward = self._p("clean_round_reward", 3.0)
            max_reward = self._p("max_reward_per_round", 3.0)
            actual_reward = min(reward, max_reward)
            delta += actual_reward
            reasons.append(f"CLEAN_ROUND(+{actual_reward:.1f})")

        # --- Apply delta and clamp ---
        new_score = clamp_score(prev_score + delta)
        new_level = score_to_level(new_score)

        # Build human-readable reason string
        if reasons:
            reason_str = " | ".join(reasons)
        else:
            reason_str = "NO_CHANGE"

        evidence["delta_components"] = reasons
        evidence["anomaly_count_after"] = record.anomaly_count + (1 if is_l1_anomaly else 0)
        evidence["incident_count_after"] = record.incident_count + (1 if (is_l1_anomaly or is_mars_suspect) else 0)

        return TrustUpdate(
            client_id=record.client_id,
            previous_score=prev_score,
            delta=round(delta, 4),
            new_score=round(new_score, 4),
            reason=reason_str,
            evidence=evidence,
            round_id=context.round_id,
            trust_level_before=prev_level.value,
            trust_level_after=new_level.value,
        )

    def apply_update(
        self,
        update: TrustUpdate,
        record: ClientSecurityRecord,
        context: SecurityContext,
    ) -> None:
        """
        Applies a TrustUpdate to a ClientSecurityRecord in-place.
        Updates all counters and appends to history.

        Parameters
        ----------
        update : TrustUpdate
            The computed update (from compute_update).
        record : ClientSecurityRecord
            The mutable record to update.
        context : SecurityContext
            Used to update per-round counters.
        """
        is_l1_anomaly = context.layer1_is_anomaly()
        is_mars_suspect = context.mars_is_suspect()
        is_quarantined = context.final_status() == "QUARANTINED"
        is_clean = (not is_l1_anomaly) and (not is_mars_suspect)

        # Update score and level
        record.trust_score = update.new_score
        record.trust_level = update.trust_level_after

        # Update counters
        if is_l1_anomaly:
            record.anomaly_count += 1
        if is_mars_suspect:
            record.mars_incident_count += 1
        if is_l1_anomaly or is_mars_suspect:
            record.incident_count += 1
            record.clean_round_count = 0  # reset consecutive clean streak
        if is_clean:
            record.clean_round_count += 1
        if is_quarantined:
            record.quarantine_count += 1

        record.last_updated_round = context.round_id

        # Append history entry
        record.append_history(update.to_dict())
