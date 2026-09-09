"""
FedSanitize — Security Intelligence: Pipeline Adapter
======================================================
Converts existing FedSanitize backend outputs into normalized SecurityContext
objects WITHOUT modifying any existing code.

Design rules:
  1. Never rename or rewrite existing fields — use adapters only.
  2. Never crash the FL pipeline; all extraction is guarded.
  3. Tolerate dicts, dataclasses, and plain objects uniformly.
  4. Distinguish "field absent" from "field present but benign/zero".
  5. Return warnings alongside contexts when data is incomplete.
  6. Never copy tensors, gradients, or state_dicts into SecurityContext.

Supported input formats:
  - SecurityPipelineResult (dataclass from services/security_service.py)
  - round_record dict (output of SimulationService.run_round)
  - Per-client security record dict (client_security_records[cid])
  - Arbitrary dicts with unknown structures (best-effort extraction)
"""

from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional, Tuple

from ..contracts.security_context import SecurityContext

logger = logging.getLogger("FedSanitize.SecurityIntelligence.PipelineAdapter")


# ---------------------------------------------------------------------------
# Safe field extraction helpers
# ---------------------------------------------------------------------------

def _safe_get(obj: Any, *keys: str, default: Any = None) -> Any:
    """
    Safely extracts a value from a dict, dataclass, or object by trying
    attribute access and key access, following a chain of keys.

    Parameters
    ----------
    obj : Any
        Source object (dict, dataclass, or generic object).
    *keys : str
        Chain of keys/attributes to traverse.
    default : Any
        Value returned when any step in the chain fails.

    Returns
    -------
    Any
        The extracted value, or `default` on any failure.
    """
    current = obj
    for key in keys:
        if current is None:
            return default
        # Try dict-style first
        if isinstance(current, dict):
            if key in current:
                current = current[key]
            else:
                return default
        else:
            # Try attribute access (dataclass / object)
            try:
                current = getattr(current, key)
            except AttributeError:
                return default
    return current


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Converts value to float, returning default on failure."""
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_bool(value: Any, default: bool = False) -> bool:
    """Converts value to bool, returning default on failure."""
    if value is None:
        return default
    try:
        return bool(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    """Converts value to int, returning default on failure."""
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_list(value: Any, default: Optional[list] = None) -> list:
    """Ensures value is a list, returning default on failure."""
    if default is None:
        default = []
    if value is None:
        return default
    if isinstance(value, list):
        return value
    return default


# ---------------------------------------------------------------------------
# Layer 1 Summary Extraction
# ---------------------------------------------------------------------------

def _extract_layer1_summary(
    l1_result: Any,
    warnings: List[str],
    client_id: str,
) -> Dict[str, Any]:
    """
    Extracts Layer 1 anomaly signals from a ClientSecurityResult object or dict.
    Compatible with the actual ClientSecurityResult dataclass fields:
      client_id, update_norm, norm_score, cosine_similarity,
      anomaly_flag, reason, status, metadata
    """
    if l1_result is None:
        warnings.append(f"[{client_id}] Layer 1 result absent — using defaults")
        return {
            "status": "UNKNOWN",
            "reason": "ABSENT",
            "anomaly_flag": False,
            "norm_score": 0.0,
            "cosine_similarity": 0.0,
            "update_norm": 0.0,
            "mad_deviation": 0.0,
            "specific_reasons": [],
            "_signal_present": False,
        }

    status = _safe_get(l1_result, "status", default=None)
    if status is None:
        status = "UNKNOWN"
        warnings.append(f"[{client_id}] Layer 1 'status' field missing")

    # metadata sub-dict (from ClientSecurityResult.metadata)
    metadata_sub = _safe_get(l1_result, "metadata", default={})
    if not isinstance(metadata_sub, dict):
        metadata_sub = {}

    return {
        "status": str(status),
        "reason": str(_safe_get(l1_result, "reason", default="UNKNOWN")),
        "anomaly_flag": _safe_bool(_safe_get(l1_result, "anomaly_flag", default=False)),
        "norm_score": _safe_float(_safe_get(l1_result, "norm_score", default=0.0)),
        "cosine_similarity": _safe_float(_safe_get(l1_result, "cosine_similarity", default=0.0)),
        "update_norm": _safe_float(_safe_get(l1_result, "update_norm", default=0.0)),
        "mad_deviation": _safe_float(metadata_sub.get("mad_deviation", 0.0)),
        "specific_reasons": _safe_list(metadata_sub.get("specific_reasons", [])),
        "_signal_present": True,
    }


# ---------------------------------------------------------------------------
# MARS Summary Extraction
# ---------------------------------------------------------------------------

def _extract_mars_summary(
    mars_result: Any,
    warnings: List[str],
    client_id: str,
) -> Dict[str, Any]:
    """
    Extracts Layer 2 MARS signals from a mars_results[cid] dict or object.
    Compatible with the actual MARS result dict fields:
      client_id, cluster_id, status, reason,
      cbe_concentration_ratio, is_backdoor_suspect
    """
    if mars_result is None:
        warnings.append(f"[{client_id}] MARS result absent — using defaults")
        return {
            "status": "UNKNOWN",
            "reason": "ABSENT",
            "cbe_concentration_ratio": 0.0,
            "is_backdoor_suspect": False,
            "cluster_id": None,
            "_signal_present": False,
        }

    status = str(_safe_get(mars_result, "status", default="UNKNOWN"))
    # Distinguish SKIPPED from actual UNKNOWN
    reason = str(_safe_get(mars_result, "reason", default="ABSENT"))
    skipped = "SKIPPED" in reason.upper() or "SKIPPED" in status.upper()

    return {
        "status": "SKIPPED" if skipped else status,
        "reason": reason,
        "cbe_concentration_ratio": _safe_float(
            _safe_get(mars_result, "cbe_concentration_ratio", default=0.0)
        ),
        "is_backdoor_suspect": _safe_bool(
            _safe_get(mars_result, "is_backdoor_suspect", default=False)
        ),
        "cluster_id": _safe_int(_safe_get(mars_result, "cluster_id", default=None)),
        "_signal_present": not skipped,
    }


# ---------------------------------------------------------------------------
# Aggregation Summary Extraction
# ---------------------------------------------------------------------------

def _extract_aggregation_summary(agg_meta: Any, warnings: List[str]) -> Dict[str, Any]:
    """
    Extracts Layer 3 aggregation metadata from a dict.
    Compatible with the actual aggregation_metadata dict returned by Layer3RobustAggregator:
      num_clients, trim_ratio, trim_count, method_used, warnings,
      n_clean_clients, trim_count_applied, applied_to_global
    """
    if agg_meta is None:
        warnings.append("Aggregation metadata absent — using defaults")
        return {
            "method_used": "UNKNOWN",
            "trim_count_applied": 0,
            "n_clean_clients": 0,
            "warnings": [],
            "_signal_present": False,
        }

    if not isinstance(agg_meta, dict):
        warnings.append(f"Aggregation metadata is not a dict ({type(agg_meta).__name__}) — skipping")
        return {
            "method_used": "UNKNOWN",
            "trim_count_applied": 0,
            "n_clean_clients": 0,
            "warnings": [],
            "_signal_present": False,
        }

    return {
        "method_used": str(agg_meta.get("method_used", "UNKNOWN")),
        "trim_count_applied": int(agg_meta.get("trim_count_applied", 0)),
        "n_clean_clients": int(agg_meta.get("n_clean_clients", agg_meta.get("num_clients", 0))),
        "trim_ratio": _safe_float(agg_meta.get("trim_ratio", 0.0)),
        "warnings": _safe_list(agg_meta.get("warnings", [])),
        "_signal_present": True,
    }


# ---------------------------------------------------------------------------
# Attack Summary Extraction
# ---------------------------------------------------------------------------

def _extract_attack_summary(
    client_record: Any,
    warnings: List[str],
    client_id: str,
) -> Dict[str, Any]:
    """
    Extracts attack metadata from a client_security_records[cid] dict or ClientUpdate.
    Compatible with client_security_records[cid] fields:
      attack_type, is_malicious, final_status
    Also compatible with ClientUpdate fields:
      attack_type, is_malicious
    """
    if client_record is None:
        warnings.append(f"[{client_id}] Attack/client record absent — using defaults")
        return {
            "attack_type": "UNKNOWN",
            "is_malicious": False,
            "final_status": "UNKNOWN",
            "_signal_present": False,
        }

    return {
        "attack_type": str(_safe_get(client_record, "attack_type", default="UNKNOWN")),
        "is_malicious": _safe_bool(_safe_get(client_record, "is_malicious", default=False)),
        "final_status": str(_safe_get(client_record, "final_status", default="UNKNOWN")),
        "_signal_present": True,
    }


# ---------------------------------------------------------------------------
# Evaluation Metrics Extraction
# ---------------------------------------------------------------------------

def _extract_evaluation_metrics(
    round_record: Any,
    warnings: List[str],
) -> Dict[str, Any]:
    """
    Extracts round-level evaluation metrics from a round_record dict.
    Compatible with SimulationService.run_round output fields:
      clean_accuracy, backdoor_asr, detection (dict with precision/recall/f1/detection_rate)
    """
    if round_record is None:
        warnings.append("Round record absent — evaluation metrics unavailable")
        return {"_signal_present": False}

    detection = _safe_get(round_record, "detection", default={})
    if not isinstance(detection, dict):
        detection = {}

    metrics: Dict[str, Any] = {
        "clean_accuracy": _safe_float(_safe_get(round_record, "clean_accuracy", default=None), default=-1.0),
        "backdoor_asr": _safe_float(_safe_get(round_record, "backdoor_asr", default=None), default=-1.0),
        "detection_rate": _safe_float(detection.get("detection_rate", -1.0)),
        "f1_score": _safe_float(detection.get("f1_score", -1.0)),
        "precision": _safe_float(detection.get("precision", -1.0)),
        "recall": _safe_float(detection.get("recall", -1.0)),
        "tp": detection.get("tp", 0),
        "fp": detection.get("fp", 0),
        "tn": detection.get("tn", 0),
        "fn": detection.get("fn", 0),
        "_signal_present": True,
    }

    # Flag -1.0 as "not available" (sentinel)
    if metrics["clean_accuracy"] < 0.0:
        warnings.append("clean_accuracy not found in round record")
    if metrics["backdoor_asr"] < 0.0:
        warnings.append("backdoor_asr not found in round record")

    return metrics


# ---------------------------------------------------------------------------
# Main Adapter Class
# ---------------------------------------------------------------------------

class PipelineAdapter:
    """
    Converts FedSanitize pipeline outputs into SecurityContext objects.

    This adapter is the ONLY place where existing pipeline fields are
    accessed by name. All other security_intelligence modules consume
    SecurityContext exclusively.

    Usage
    -----
    # From SecurityPipelineResult (dataclass):
    contexts, warnings = PipelineAdapter.from_pipeline_result(pipeline_result, round_id=3)

    # From round_record dict (SimulationService output):
    contexts, warnings = PipelineAdapter.from_round_record(round_record)

    # From a single raw dict:
    context, warnings = PipelineAdapter.from_dict(some_dict, round_id=1)
    """

    @staticmethod
    def from_pipeline_result(
        result: Any,
        round_id: Optional[int] = None,
    ) -> Tuple[List[SecurityContext], List[str]]:
        """
        Converts a SecurityPipelineResult (or equivalent dict) into per-client
        SecurityContext objects.

        Parameters
        ----------
        result : SecurityPipelineResult | dict
            Output of SecurityPipeline.process_round().
        round_id : int | None
            FL round identifier. Extracted from result if not provided.

        Returns
        -------
        (list[SecurityContext], list[str])
            Normalized contexts and any warnings generated.
        """
        all_warnings: List[str] = []
        contexts: List[SecurityContext] = []

        if result is None:
            all_warnings.append("pipeline_result is None — returning empty contexts")
            return contexts, all_warnings

        # Extract round number
        r_id = round_id
        if r_id is None:
            r_id = _safe_int(_safe_get(result, "round_number", default=None))

        # Extract maps
        l1_results = _safe_get(result, "layer1_results", default={}) or {}
        mars_results = _safe_get(result, "mars_results", default={}) or {}
        client_security_records = _safe_get(result, "client_security_records", default={}) or {}
        agg_meta = _safe_get(result, "aggregation_metadata", default=None)

        agg_summary = _extract_aggregation_summary(agg_meta, all_warnings)

        # Determine client set: union of all available records
        client_ids = set()
        client_ids.update(l1_results.keys() if isinstance(l1_results, dict) else [])
        client_ids.update(mars_results.keys() if isinstance(mars_results, dict) else [])
        client_ids.update(client_security_records.keys() if isinstance(client_security_records, dict) else [])

        if not client_ids:
            all_warnings.append("No client IDs found in pipeline result")
            return contexts, all_warnings

        for cid in sorted(client_ids):
            w: List[str] = []

            l1_res = l1_results.get(cid) if isinstance(l1_results, dict) else None
            mars_res = mars_results.get(cid) if isinstance(mars_results, dict) else None
            sec_rec = client_security_records.get(cid) if isinstance(client_security_records, dict) else None

            l1_summary = _extract_layer1_summary(l1_res, w, cid)
            mars_summary = _extract_mars_summary(mars_res, w, cid)
            attack_summary = _extract_attack_summary(sec_rec, w, cid)

            # Evaluation metrics are round-level, not per-client
            # Pass None here; use from_round_record for full metrics
            eval_metrics = {"_signal_present": False}

            _summary_map = {
                "layer1": l1_summary,
                "mars": mars_summary,
                "attack": attack_summary,
            }
            missing = [
                f for f, s in _summary_map.items()
                if not s.get("_signal_present", False)
            ]

            ctx = SecurityContext(
                round_id=r_id,
                client_id=cid,
                layer1_summary=l1_summary,
                mars_summary=mars_summary,
                aggregation_summary=agg_summary,
                attack_summary=attack_summary,
                evaluation_metrics=eval_metrics,
                metadata={
                    "source": "pipeline_result",
                    "warnings": w,
                    "missing_fields": missing,
                },
            )
            contexts.append(ctx)
            all_warnings.extend(w)

        return contexts, all_warnings

    @staticmethod
    def from_round_record(
        record: Dict[str, Any],
    ) -> Tuple[List[SecurityContext], List[str]]:
        """
        Converts a SimulationService round_record dict into per-client SecurityContext objects.

        Compatible with the actual round_record structure:
          round, attack_type, total_clients, clean_accuracy, backdoor_asr,
          trusted_clients, quarantined_clients, layer1_quarantined,
          mars_quarantined, detection, client_security_records, aggregation,
          distance_matrix, log

        Parameters
        ----------
        record : dict
            Output of SimulationService.run_round().

        Returns
        -------
        (list[SecurityContext], list[str])
            Normalized contexts and any warnings generated.
        """
        all_warnings: List[str] = []
        contexts: List[SecurityContext] = []

        if not isinstance(record, dict):
            all_warnings.append(f"round_record is not a dict ({type(record).__name__}) — returning empty")
            return contexts, all_warnings

        r_id = _safe_int(record.get("round", None))
        client_sec_records = record.get("client_security_records", {}) or {}
        agg_meta = record.get("aggregation", None)

        agg_summary = _extract_aggregation_summary(agg_meta, all_warnings)
        eval_metrics = _extract_evaluation_metrics(record, all_warnings)

        if not isinstance(client_sec_records, dict) or not client_sec_records:
            all_warnings.append("client_security_records absent or empty in round_record")
            return contexts, all_warnings

        for cid in sorted(client_sec_records.keys()):
            w: List[str] = []
            sec_rec = client_sec_records[cid]

            # From client_security_records[cid]:
            # layer1_status, layer1_reason (Layer 1 summary)
            # mars_cluster, mars_status, mars_reason (MARS summary)
            # attack_type, is_malicious, final_status (attack summary)
            # update_norm, cosine_similarity (additional L1 fields)

            l1_summary: Dict[str, Any] = {
                "status": str(sec_rec.get("layer1_status", "UNKNOWN")),
                "reason": str(sec_rec.get("layer1_reason", "UNKNOWN")),
                "anomaly_flag": sec_rec.get("layer1_status", "PASS") == "FLAGGED",
                "norm_score": 0.0,  # Not stored in round_record's client_security_records
                "cosine_similarity": _safe_float(sec_rec.get("cosine_similarity", 0.0)),
                "update_norm": _safe_float(sec_rec.get("update_norm", 0.0)),
                "mad_deviation": 0.0,
                "specific_reasons": [],
                "_signal_present": "layer1_status" in sec_rec,
            }

            mars_status_raw = str(sec_rec.get("mars_status", "UNKNOWN"))
            skipped = "SKIPPED" in mars_status_raw.upper()
            mars_summary: Dict[str, Any] = {
                "status": "SKIPPED" if skipped else mars_status_raw,
                "reason": str(sec_rec.get("mars_reason", "UNKNOWN")),
                "cbe_concentration_ratio": 0.0,  # Not in round_record flat record
                "is_backdoor_suspect": mars_status_raw == "FLAGGED",
                "cluster_id": _safe_int(sec_rec.get("mars_cluster", None)),
                "_signal_present": "mars_status" in sec_rec and not skipped,
            }

            attack_summary: Dict[str, Any] = {
                "attack_type": str(sec_rec.get("attack_type", "UNKNOWN")),
                "is_malicious": _safe_bool(sec_rec.get("is_malicious", False)),
                "final_status": str(sec_rec.get("final_status", "UNKNOWN")),
                "_signal_present": "final_status" in sec_rec,
            }

            missing = []
            if not l1_summary["_signal_present"]:
                missing.append("layer1")
                w.append(f"[{cid}] layer1_status missing in round_record")
            if not mars_summary["_signal_present"]:
                missing.append("mars")

            ctx = SecurityContext(
                round_id=r_id,
                client_id=cid,
                layer1_summary=l1_summary,
                mars_summary=mars_summary,
                aggregation_summary=agg_summary,
                attack_summary=attack_summary,
                evaluation_metrics=eval_metrics,
                metadata={
                    "source": "round_record",
                    "warnings": w,
                    "missing_fields": missing,
                },
            )
            contexts.append(ctx)
            all_warnings.extend(w)

        return contexts, all_warnings

    @staticmethod
    def from_dict(
        d: Dict[str, Any],
        round_id: Optional[int] = None,
        client_id: Optional[str] = None,
    ) -> Tuple[SecurityContext, List[str]]:
        """
        Best-effort conversion of an arbitrary dict into a SecurityContext.
        For use when the exact source format is unknown.

        Parameters
        ----------
        d : dict
            Any dict with security-related fields.
        round_id : int | None
            Explicit round override.
        client_id : str | None
            Explicit client_id override.

        Returns
        -------
        (SecurityContext, list[str])
            Best-effort context and any warnings.
        """
        warnings: List[str] = []

        if not isinstance(d, dict):
            warnings.append(f"Input is not a dict ({type(d).__name__}) — returning empty SecurityContext")
            return SecurityContext(metadata={"source": "unknown", "warnings": warnings, "missing_fields": ["all"]}), warnings

        r_id = round_id or _safe_int(d.get("round", d.get("round_id", None)))
        c_id = client_id or d.get("client_id", None)

        # Try to find layer1 sub-dict or flat fields
        l1_dict = d.get("layer1_summary", d.get("layer1", None))
        if isinstance(l1_dict, dict):
            l1_summary = _extract_layer1_summary(l1_dict, warnings, str(c_id or "?"))
        else:
            l1_summary = _extract_layer1_summary(d if "layer1_status" in d else None, warnings, str(c_id or "?"))

        mars_dict = d.get("mars_summary", d.get("mars", None))
        if isinstance(mars_dict, dict):
            mars_summary = _extract_mars_summary(mars_dict, warnings, str(c_id or "?"))
        else:
            mars_summary = _extract_mars_summary(d if "mars_status" in d else None, warnings, str(c_id or "?"))

        agg_dict = d.get("aggregation_summary", d.get("aggregation", None))
        agg_summary = _extract_aggregation_summary(agg_dict, warnings)

        attack_dict = d.get("attack_summary", d.get("attack", None))
        if isinstance(attack_dict, dict):
            attack_summary = _extract_attack_summary(attack_dict, warnings, str(c_id or "?"))
        else:
            attack_summary = _extract_attack_summary(d if "attack_type" in d else None, warnings, str(c_id or "?"))

        eval_dict = d.get("evaluation_metrics", d.get("metrics", None))
        eval_metrics = _extract_evaluation_metrics(eval_dict or d, warnings)

        missing = [
            k for k, v in {
                "layer1": l1_summary,
                "mars": mars_summary,
                "aggregation": agg_summary,
                "attack": attack_summary,
            }.items()
            if not v.get("_signal_present", False)
        ]

        ctx = SecurityContext(
            round_id=r_id,
            client_id=c_id,
            layer1_summary=l1_summary,
            mars_summary=mars_summary,
            aggregation_summary=agg_summary,
            attack_summary=attack_summary,
            evaluation_metrics=eval_metrics,
            metadata={
                "source": "generic_dict",
                "warnings": warnings,
                "missing_fields": missing,
            },
        )
        return ctx, warnings
