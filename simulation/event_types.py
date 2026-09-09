"""
FedSantize Simulation Engine — Event Types
===========================================
Standardized event constants describing the end-to-end lifecycle of
a secure Federated Learning round. Grounded in Phase 1 & 2 specifications.
"""

from __future__ import annotations


class EventType:
    # Round Lifecycle
    ROUND_STARTED = "ROUND_STARTED"
    CLIENT_TRAINING_STARTED = "CLIENT_TRAINING_STARTED"
    CLIENT_TRAINING_FINISHED = "CLIENT_TRAINING_FINISHED"
    ATTACK_ACTIVATED = "ATTACK_ACTIVATED"
    CLIENT_UPDATE_CREATED = "CLIENT_UPDATE_CREATED"
    CLIENT_UPDATE_SENT = "CLIENT_UPDATE_SENT"

    # Layer 1: Statistical Anomaly Detection
    LAYER1_STARTED = "LAYER1_STARTED"
    LAYER1_ANALYZING = "LAYER1_ANALYZING"
    LAYER1_CLIENT_FLAGGED = "LAYER1_CLIENT_FLAGGED"
    LAYER1_CLIENT_PASSED = "LAYER1_CLIENT_PASSED"

    # Layer 2: MARS Backdoor Analysis
    MARS_STARTED = "MARS_STARTED"
    MARS_LAYER_SELECTED = "MARS_LAYER_SELECTED"
    MARS_ENERGY_ANALYZED = "MARS_ENERGY_ANALYZED"
    MARS_CBE_CREATED = "MARS_CBE_CREATED"
    MARS_DISTANCE_COMPUTED = "MARS_DISTANCE_COMPUTED"
    MARS_CLUSTER_CREATED = "MARS_CLUSTER_CREATED"
    MARS_CLIENT_QUARANTINED = "MARS_CLIENT_QUARANTINED"

    # Layer 3: Robust Aggregation
    AGGREGATION_STARTED = "AGGREGATION_STARTED"
    AGGREGATION_TRIMMING = "AGGREGATION_TRIMMING"
    AGGREGATION_FINISHED = "AGGREGATION_FINISHED"

    # Completion & Final Evaluation
    GLOBAL_MODEL_UPDATED = "GLOBAL_MODEL_UPDATED"
    ROUND_COMPLETED = "ROUND_COMPLETED"

    @classmethod
    def all_types(cls) -> list[str]:
        """Returns all recognized event types."""
        return [
            v for k, v in cls.__dict__.items()
            if not k.startswith("__") and isinstance(v, str)
        ]
