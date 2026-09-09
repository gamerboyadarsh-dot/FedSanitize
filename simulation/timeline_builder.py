"""
FedSantize Simulation Engine — Timeline Builder
================================================
Transforms an event stream into a sequence of orchestrated TimelineSteps
organized by cinematic narrative scenes:
  INTRO -> TRAINING -> ATTACK -> UPDATE_FLOW -> LAYER1 -> MARS -> AGGREGATION -> RESULT

Grounded in Phase 4 of the simulation engine specification.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from .event_types import EventType
from .security_event import SecurityEvent


class SceneType:
    INTRO = "INTRO"
    TRAINING = "TRAINING"
    ATTACK = "ATTACK"
    UPDATE_FLOW = "UPDATE_FLOW"
    LAYER1 = "LAYER1"
    MARS = "MARS"
    AGGREGATION = "AGGREGATION"
    RESULT = "RESULT"


@dataclass
class TimelineStep:
    """
    An orchestrated step in the simulation timeline.
    
    Attributes
    ----------
    step_index : int
        Zero-based index of this step in the replay sequence.
    event : SecurityEvent
        The underlying verified security event.
    start_time : float
        Cumulative logical start time (seconds).
    duration : float
        Synthetic display duration allocated for visual comprehension (seconds).
    animation_type : str
        Animation directive for UI renderers (e.g. 'PULSE', 'FLOW', 'ALERT', 'QUARANTINE').
    priority : int
        Visual priority (1 = low, 5 = critical alert).
    scene : str
        One of the SceneType constants.
    description : str
        Concise, human-readable commentary of what is happening.
    """
    step_index: int
    event: SecurityEvent
    start_time: float
    duration: float
    animation_type: str
    priority: int
    scene: str
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_index": self.step_index,
            "event": self.event.to_dict(),
            "start_time": float(self.start_time),
            "duration": float(self.duration),
            "animation_type": self.animation_type,
            "priority": int(self.priority),
            "scene": self.scene,
            "description": self.description,
        }


# Mapping from EventType to (SceneType, animation_type, base_duration, priority)
EVENT_METADATA_MAP: Dict[str, tuple[str, str, float, int]] = {
    EventType.ROUND_STARTED: (SceneType.INTRO, "GLOBAL_PULSE", 1.0, 2),
    EventType.CLIENT_TRAINING_STARTED: (SceneType.TRAINING, "NODE_SPIN", 0.6, 1),
    EventType.CLIENT_TRAINING_FINISHED: (SceneType.TRAINING, "NODE_FLASH", 0.5, 1),
    EventType.ATTACK_ACTIVATED: (SceneType.ATTACK, "THREAT_ALERT", 1.8, 5),
    EventType.CLIENT_UPDATE_CREATED: (SceneType.UPDATE_FLOW, "PACKET_SPAWN", 0.5, 1),
    EventType.CLIENT_UPDATE_SENT: (SceneType.UPDATE_FLOW, "PACKET_FLY", 0.8, 2),
    EventType.LAYER1_STARTED: (SceneType.LAYER1, "RADAR_SWEEP", 1.0, 3),
    EventType.LAYER1_ANALYZING: (SceneType.LAYER1, "SCAN_LINE", 0.5, 2),
    EventType.LAYER1_CLIENT_FLAGGED: (SceneType.LAYER1, "QUARANTINE_WARNING", 1.5, 4),
    EventType.LAYER1_CLIENT_PASSED: (SceneType.LAYER1, "VERIFIED_GLOW", 0.5, 1),
    EventType.MARS_STARTED: (SceneType.MARS, "DEEP_FORENSIC_INIT", 1.2, 3),
    EventType.MARS_LAYER_SELECTED: (SceneType.MARS, "NEURAL_LAYER_HIGHLIGHT", 1.0, 2),
    EventType.MARS_ENERGY_ANALYZED: (SceneType.MARS, "ENERGY_DISTRIBUTION", 1.2, 3),
    EventType.MARS_CBE_CREATED: (SceneType.MARS, "CBE_CONCENTRATION", 1.5, 3),
    EventType.MARS_DISTANCE_COMPUTED: (SceneType.MARS, "WASSERSTEIN_HEATMAP", 1.5, 3),
    EventType.MARS_CLUSTER_CREATED: (SceneType.MARS, "CLUSTER_EMERGENCE", 1.5, 3),
    EventType.MARS_CLIENT_QUARANTINED: (SceneType.MARS, "ISOLATION_SEVER", 2.0, 5),
    EventType.AGGREGATION_STARTED: (SceneType.AGGREGATION, "SERVER_INTAKE", 1.0, 2),
    EventType.AGGREGATION_TRIMMING: (SceneType.AGGREGATION, "TRIM_FILTER", 1.2, 3),
    EventType.AGGREGATION_FINISHED: (SceneType.AGGREGATION, "CONVERGENCE_BEAM", 1.2, 3),
    EventType.GLOBAL_MODEL_UPDATED: (SceneType.RESULT, "GLOBAL_SHIELD", 1.0, 3),
    EventType.ROUND_COMPLETED: (SceneType.RESULT, "METRICS_DASHBOARD", 1.5, 4),
}


class TimelineBuilder:
    """
    Constructs an interactive replay timeline from a list of SecurityEvent items.
    """

    def build_timeline(self, events: List[SecurityEvent]) -> List[TimelineStep]:
        """
        Translates raw security events into ordered, animated timeline steps.
        """
        steps: List[TimelineStep] = []
        cur_time = 0.0

        for idx, event in enumerate(events):
            meta = EVENT_METADATA_MAP.get(
                event.event_type,
                (SceneType.INTRO, "DEFAULT", 0.5, 1),
            )
            scene, anim_type, duration, priority = meta

            # Elevate priority for flagged/quarantined events
            if event.severity in ("HIGH", "CRITICAL"):
                priority = max(priority, 4)

            desc = event.message or f"Event {event.event_type} at step {idx}"

            step = TimelineStep(
                step_index=idx,
                event=event,
                start_time=round(cur_time, 2),
                duration=round(duration, 2),
                animation_type=anim_type,
                priority=priority,
                scene=scene,
                description=desc,
            )
            steps.append(step)
            cur_time += duration

        return steps
