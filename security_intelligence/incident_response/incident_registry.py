"""
In-memory (optionally persisted) registry of incidents, so the response
engine and threat engine can both answer "how many times has this client
been flagged before". Kept intentionally separate from QuarantineManager,
which only tracks *active isolation state*.
"""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from .response_models import Incident, IncidentStage


class IncidentRegistry:
    def __init__(self):
        self._incidents: Dict[str, Incident] = {}
        self._by_client: Dict[str, List[str]] = {}
        self._lock = threading.Lock()

    def register(self, incident: Incident) -> None:
        with self._lock:
            self._incidents[incident.incident_id] = incident
            if incident.client_id:
                self._by_client.setdefault(incident.client_id, []).append(incident.incident_id)

    def update_stage(self, incident_id: str, stage: IncidentStage) -> None:
        with self._lock:
            inc = self._incidents.get(incident_id)
            if inc is not None:
                inc.stage = stage

    def get(self, incident_id: str) -> Optional[Incident]:
        return self._incidents.get(incident_id)

    def incidents_for_client(self, client_id: str) -> List[Incident]:
        ids = self._by_client.get(client_id, [])
        return [self._incidents[i] for i in ids if i in self._incidents]

    def incident_count_for_client(self, client_id: str) -> int:
        return len(self._by_client.get(client_id, []))

    def all_incidents(self) -> List[Incident]:
        with self._lock:
            return list(self._incidents.values())

    def active_incident_count(self) -> int:
        """Incidents whose latest decision resulted in an active isolation-type action."""
        count = 0
        for inc in self._incidents.values():
            if inc.decision and inc.decision.action.value in ("TEMPORARY_ISOLATE", "QUARANTINE"):
                count += 1
        return count
