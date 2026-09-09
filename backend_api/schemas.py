"""
FedSanitize — Backend API Schemas (Pydantic models)
===================================================
Models for config updates, attack assignments, and simulation control.
"""

from __future__ import annotations
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class FederatedConfigUpdate(BaseModel):
    num_clients: Optional[int] = None
    num_rounds: Optional[int] = None
    local_epochs: Optional[int] = None
    local_batch_size: Optional[int] = None
    local_lr: Optional[float] = None
    local_momentum: Optional[float] = None
    iid: Optional[bool] = None


class DefenseConfigUpdate(BaseModel):
    layer1_norm_threshold: Optional[float] = None
    layer1_mad_multiplier: Optional[float] = None
    layer1_min_cosine: Optional[float] = None
    mars_cbe_top_p: Optional[float] = None
    mars_malignity_threshold: Optional[float] = None
    mars_wasserstein_p: Optional[int] = None
    trimmed_mean_beta: Optional[float] = None


class AttackConfigUpdate(BaseModel):
    num_malicious_clients: Optional[int] = None
    sign_flip_gamma: Optional[float] = None
    random_byzantine_scale: Optional[float] = None
    extreme_update_gamma: Optional[float] = None
    backdoor_trigger_size: Optional[int] = None
    backdoor_target_class: Optional[int] = None
    backdoor_poison_ratio: Optional[float] = None


class ConfigUpdateRequest(BaseModel):
    federated: Optional[FederatedConfigUpdate] = None
    defense: Optional[DefenseConfigUpdate] = None
    attack: Optional[AttackConfigUpdate] = None


class AttackAssignmentRequest(BaseModel):
    attack_type: str = Field(
        ...,
        description="One of: 'NONE', 'EXTREME_UPDATE', 'SIGN_FLIPPING', 'RANDOM_BYZANTINE', 'BACKDOOR', 'LABEL_FLIPPING'"
    )


class ClientSummary(BaseModel):
    client_id: str
    is_malicious: bool
    attack_type: str
    sample_count: int
    latest_record: Optional[Dict[str, Any]] = None
