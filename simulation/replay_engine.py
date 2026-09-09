"""
FedSantize Simulation Engine — Replay Engine
============================================
Provides deterministic, step-by-step forensic replay over the recorded
security event timeline without requiring expensive neural network retraining.

Grounded in Phase 7 specifications.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
import copy

from .security_event import SecurityEvent
from .timeline_builder import TimelineStep, TimelineBuilder
from .network_state import NetworkState


class ReplayEngine:
    """
    Deterministic replay controller for federated learning security simulations.
    """

    SUPPORTED_SPEEDS = [0.5, 1.0, 2.0, 4.0]

    def __init__(
        self,
        timeline: Optional[List[TimelineStep]] = None,
        client_records: Optional[Dict[str, Dict[str, Any]]] = None,
        round_id: int = 1,
    ):
        self.timeline: List[TimelineStep] = timeline or []
        self.client_records: Dict[str, Dict[str, Any]] = client_records or {}
        self.round_id = round_id

        self.current_step: int = 0
        self.is_playing: bool = False
        self.playback_speed: float = 1.0
        self.selected_client: Optional[str] = None

        # Network state tracking
        self.network_state = NetworkState(self.client_records, round_id=self.round_id)
        if self.timeline:
            self.seek(0)

    @property
    def total_steps(self) -> int:
        return len(self.timeline)

    @property
    def current_timeline_step(self) -> Optional[TimelineStep]:
        if 0 <= self.current_step < len(self.timeline):
            return self.timeline[self.current_step]
        return None

    @property
    def current_event(self) -> Optional[SecurityEvent]:
        step = self.current_timeline_step
        return step.event if step else None

    @property
    def is_finished(self) -> bool:
        return self.current_step >= len(self.timeline) - 1

    def load_timeline(
        self,
        timeline: List[TimelineStep],
        client_records: Optional[Dict[str, Dict[str, Any]]] = None,
        round_id: int = 1,
    ) -> None:
        """Loads a new timeline and resets playback state."""
        self.timeline = timeline
        self.round_id = round_id
        if client_records is not None:
            self.client_records = client_records
        self.reset()

    def play(self) -> None:
        """Sets playback state to playing."""
        if not self.is_finished:
            self.is_playing = True

    def pause(self) -> None:
        """Pauses playback."""
        self.is_playing = False

    def reset(self) -> None:
        """Resets playback to the initial step."""
        self.current_step = 0
        self.is_playing = False
        self.network_state.initialize(self.client_records, round_id=self.round_id)
        if self.timeline:
            self._apply_steps_up_to(0)

    def step_forward(self) -> bool:
        """Advances replay by one step. Returns True if advanced."""
        if self.current_step < len(self.timeline) - 1:
            self.current_step += 1
            self.network_state.apply_event(self.timeline[self.current_step].event)
            return True
        self.is_playing = False
        return False

    def step_backward(self) -> bool:
        """Reverts replay by one step. Returns True if reverted."""
        if self.current_step > 0:
            self.seek(self.current_step - 1)
            return True
        return False

    def seek(self, step_index: int) -> None:
        """Jumps directly to a target step index, re-synchronizing network state."""
        if not self.timeline:
            self.current_step = 0
            return

        target = max(0, min(step_index, len(self.timeline) - 1))
        self.current_step = target
        self._apply_steps_up_to(target)

    def _apply_steps_up_to(self, step_index: int) -> None:
        """Reconstructs the cumulative network state from step 0 to step_index."""
        self.network_state.initialize(self.client_records, round_id=self.round_id)
        for i in range(step_index + 1):
            if i < len(self.timeline):
                self.network_state.apply_event(self.timeline[i].event)

    def set_speed(self, speed: float) -> None:
        """Sets playback speed multiplier."""
        if speed in self.SUPPORTED_SPEEDS:
            self.playback_speed = float(speed)
        else:
            # Snap to closest supported speed
            closest = min(self.SUPPORTED_SPEEDS, key=lambda s: abs(s - speed))
            self.playback_speed = float(closest)

    def select_client(self, client_id: Optional[str]) -> None:
        """Focuses the forensic inspector on a particular client."""
        self.selected_client = client_id

    def get_progress_ratio(self) -> float:
        """Returns normalized replay progress (0.0 to 1.0)."""
        if len(self.timeline) <= 1:
            return 1.0 if self.timeline else 0.0
        return self.current_step / (len(self.timeline) - 1)

    def get_forensic_summary(self) -> Dict[str, Any]:
        """Provides a quick summary for dashboard header cards."""
        return {
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "progress_pct": round(self.get_progress_ratio() * 100, 1),
            "is_playing": self.is_playing,
            "playback_speed": self.playback_speed,
            "selected_client": self.selected_client,
            "active_layer": self.network_state.current_layer,
            "quarantined_count": len(self.network_state.quarantined_clients),
            "trusted_count": len(self.network_state.trusted_clients),
        }
