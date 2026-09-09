"""
FedSantize Simulation Engine — Scenario Engine
==============================================
Provides tailored visual narratives and technical storytelling
for each adversarial attack scenario:
  - NORMAL / BENIGN
  - EXTREME_UPDATE (Large magnitude poisoning)
  - SIGN_FLIP (Directional reversal)
  - RANDOM_BYZANTINE (Chaotic noise injection)
  - LABEL_FLIPPING (Data poisoning)
  - BACKDOOR (Targeted trigger injection & MARS forensics)

Grounded in Phase 8 of the simulation engine specification.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class ScenarioNarrative:
    attack_type: str
    title: str
    headline: str
    story_steps: List[str]
    mitigating_layer: str
    forensic_focus: str
    technical_explanation: str
    threat_severity: str


SCENARIO_DATABASE: Dict[str, ScenarioNarrative] = {
    "NORMAL": ScenarioNarrative(
        attack_type="NORMAL",
        title="Clean Federated Learning Consensus",
        headline="All clients contribute compliant gradient deltas.",
        story_steps=[
            "Federated server distributes global model weights.",
            "Clients train locally on private data partitions.",
            "Clients submit parameter updates with moderate L2 norms and high directional alignment.",
            "Layer 1 confirms updates conform to statistical distribution (MAD filter pass).",
            "MARS representation analysis confirms absence of concentrated backdoor clusters.",
            "Coordinate-wise Trimmed Mean aggregates client updates into updated global model.",
        ],
        mitigating_layer="None Needed (Clean FL)",
        forensic_focus="Update Norm & Directional Alignment",
        technical_explanation="Normal distributed training produces consistent directional convergence. Updates maintain expected gradient distributions.",
        threat_severity="LOW",
    ),
    "EXTREME_UPDATE": ScenarioNarrative(
        attack_type="EXTREME_UPDATE",
        title="Extreme Magnitude Model Poisoning",
        headline="Malicious client attempts to overpower global weights with massive gradient scaling.",
        story_steps=[
            "Malicious client scales local parameter delta by gamma multiplier (e.g. 10x - 50x).",
            "Compromised update transmitted toward the central server.",
            "Layer 1 Statistical Filter evaluates update L2 norm against the peer median.",
            "Update exceeds Median Absolute Deviation (MAD) safety threshold.",
            "Layer 1 flags and isolates the malicious client before MARS or aggregation.",
            "Trimmed Mean securely combines remaining honest client updates.",
        ],
        mitigating_layer="Layer 1 (Statistical Anomaly Detection)",
        forensic_focus="L2 Update Norm & MAD Multiplier",
        technical_explanation="Adversary attempts to dominate the coordinate average by injecting updates orders of magnitude larger than normal convergence steps. Detected via robust non-parametric MAD filtering.",
        threat_severity="HIGH",
    ),
    "SIGN_FLIPPING": ScenarioNarrative(
        attack_type="SIGN_FLIPPING",
        title="Sign Flipping Directional Reversal",
        headline="Malicious client inverts gradient direction to actively undo global learning.",
        story_steps=[
            "Malicious client inverts delta direction (delta = -gamma * delta).",
            "Inverted update creates sharp directional conflict with benign consensus.",
            "Layer 1 computes pairwise and consensus cosine similarity.",
            "Client exhibits negative or severely depressed cosine similarity against peer consensus.",
            "Layer 1 quarantines the inverted client; Layer 3 coordinate trimming neutralizes any residual drift.",
            "Global model parameter integrity is preserved.",
        ],
        mitigating_layer="Layer 1 (Cosine Similarity) & Layer 3 (Trimmed Mean)",
        forensic_focus="Directional Cosine Similarity",
        technical_explanation="By multiplying gradients by -1, the attacker attempts to push the model away from the loss minimum. Cosine distance against robust consensus flags this directional conflict.",
        threat_severity="HIGH",
    ),
    "RANDOM_BYZANTINE": ScenarioNarrative(
        attack_type="RANDOM_BYZANTINE",
        title="Random Byzantine Noise Injection",
        headline="Arbitrary stochastic noise injected to destroy model parameter convergence.",
        story_steps=[
            "Byzantine client generates high-variance Gaussian noise deltas.",
            "Chaotic parameter updates injected into the aggregation pool.",
            "Layer 1 detects both abnormal norm dispersion and weak directional correlation.",
            "If noise magnitude is calibrated to bypass Layer 1, Layer 3 Coordinate-wise Trimmed Mean clips extreme coordinates.",
            "Global model converges smoothly despite malicious noise injection.",
        ],
        mitigating_layer="Layer 1 (Norm & Direction) + Layer 3 (Coordinate Trimmed Mean)",
        forensic_focus="Norm Variance & Trimmed Coordinates",
        technical_explanation="Byzantine adversaries introduce unstructured stochastic disruptions. Coordinate-wise trimming eliminates tail values across each dimension, nullifying variance explosions.",
        threat_severity="HIGH",
    ),
    "LABEL_FLIPPING": ScenarioNarrative(
        attack_type="LABEL_FLIPPING",
        title="Targeted Data Poisoning (Label Flipping)",
        headline="Adversary manipulates local training dataset labels (e.g., class 7 -> 1).",
        story_steps=[
            "Adversary systematically reassigns target labels in their local private dataset.",
            "Local SGD trains model parameters on corrupted data.",
            "Update deltas may appear statistically moderate in overall norm.",
            "Consensus directional analysis and Layer 3 coordinate trimming mitigate targeted degradation.",
            "Clean test accuracy is preserved across unaffected classes.",
        ],
        mitigating_layer="Layer 1 (Consensus Alignment) & Layer 3 (Robust Aggregation)",
        forensic_focus="Class-wise Loss & Gradient Consensus",
        technical_explanation="Data poisoning alters local empirical loss surfaces. If update norms remain subtle, coordinate trimming prevents the poisoned client from dictating directional shifts for the victim class.",
        threat_severity="MEDIUM",
    ),
    "BACKDOOR": ScenarioNarrative(
        attack_type="BACKDOOR",
        title="Stealthy Neural Backdoor Injection (Flagship Threat)",
        headline="Attacker injects watermark trigger to create hidden backdoor while maintaining normal utility.",
        story_steps=[
            "Attacker embeds visual trigger pattern (e.g. 4-pixel watermark) into a subset of training samples.",
            "Poisoned client trains local CNN to associate trigger with attacker's target class.",
            "Model update is stealthy: norm and overall cosine similarity mimic benign clients.",
            "Layer 1 inspects update in parameter space: NO obvious statistical anomaly detected.",
            "Update escalates to Layer 2: MARS Deep Representation Forensics.",
            "MARS inspects intermediate convolutional representations (conv1, conv2).",
            "Backdoor Energy and Concentrated Backdoor Energy (CBE) reveal sharp sparse activation spikes.",
            "Wasserstein distance matrix separates backdoor clients into a distinct outlier cluster.",
            "MARS quarantines the backdoor client; sanitized updates proceed to Layer 3 aggregation.",
            "Result: 97%+ Clean Accuracy with Backdoor ASR eliminated.",
        ],
        mitigating_layer="Layer 2 (MARS Deep Backdoor Analysis)",
        forensic_focus="CBE Concentration Ratio, Wasserstein Heatmap & Cluster Separation",
        technical_explanation="Backdoor attacks evade simple weight norm defenses by concentrating malicious capacity into specialized representation sub-spaces. MARS extracts this concentrated backdoor energy and clusters via Wasserstein distances, isolating the stealthy adversary with mathematical precision.",
        threat_severity="CRITICAL",
    ),
}


class ScenarioEngine:
    """Manages attack scenario narratives and visual explainability."""

    @staticmethod
    def get_narrative(attack_type: str) -> ScenarioNarrative:
        # Standardize query
        key = str(attack_type).upper().strip()
        for candidate in ("BACKDOOR", "EXTREME_UPDATE", "SIGN_FLIP", "SIGN_FLIPPING", "RANDOM_BYZANTINE", "BYZANTINE", "LABEL_FLIPPING", "LABEL_FLIP"):
            if candidate in key:
                if "BACKDOOR" in candidate:
                    return SCENARIO_DATABASE["BACKDOOR"]
                if "EXTREME" in candidate:
                    return SCENARIO_DATABASE["EXTREME_UPDATE"]
                if "SIGN" in candidate:
                    return SCENARIO_DATABASE["SIGN_FLIPPING"]
                if "BYZANTINE" in candidate:
                    return SCENARIO_DATABASE["RANDOM_BYZANTINE"]
                if "LABEL" in candidate:
                    return SCENARIO_DATABASE["LABEL_FLIPPING"]
        return SCENARIO_DATABASE.get(key, SCENARIO_DATABASE["NORMAL"])
