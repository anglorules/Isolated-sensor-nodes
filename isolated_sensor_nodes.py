from dataclasses import dataclass
from datetime import datetime, timezone
import random
from typing import List, Dict


@dataclass
class TelemetryEvent:
    timestamp: str
    node_id: str
    cpu_percent: float
    db_queries_per_sec: int
    auth_failures: int


class IsolatedSensorNode:
    def __init__(self, node_id: str, seed: int | None = None):
        self.node_id = node_id
        self.rng = random.Random(seed)

    def generate_event(self, inject_anomaly: bool = False) -> TelemetryEvent:
        cpu = round(self.rng.uniform(12.0, 45.0), 2)
        db_qps = self.rng.randint(5, 35)
        auth_fails = 0 if self.rng.random() > 0.1 else 1

        if inject_anomaly:
            # Simulates an abnormal spike or unauthorized probe burst locally
            cpu = round(self.rng.uniform(85.0, 99.5), 2)
            db_qps = self.rng.randint(180, 400)
            auth_fails = self.rng.randint(6, 20)

        return TelemetryEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            node_id=self.node_id,
            cpu_percent=cpu,
            db_queries_per_sec=db_qps,
            auth_failures=auth_fails,
        )


def evaluate_locally(event: TelemetryEvent) -> List[str]:
    alerts = []
    if event.cpu_percent > 85.0:
        alerts.append("HIGH_CPU_SPIKE")
    if event.db_queries_per_sec > 150:
        alerts.append("ABNORMAL_DB_PROBE_RATE")
    if event.auth_failures >= 5:
        alerts.append("AUTH_FAILURE_BURST")
    return alerts


def run_simulation(steps: int = 10) -> List[Dict]:
    nodes = [
        IsolatedSensorNode("node-payments-01", seed=101),
        IsolatedSensorNode("node-db-edge-02", seed=202),
    ]
    local_audit_log = []

    for step in range(steps):
        for node in nodes:
            anomaly = step in (4, 8) and node.node_id == "node-db-edge-02"
            event = node.generate_event(inject_anomaly=anomaly)
            alerts = evaluate_locally(event)

            record = {
                "event": event,
                "local_alerts": alerts,
                "pii_or_raw_payload_exported": False,
            }
            local_audit_log.append(record)

            if alerts:
                print(
                    f"[{event.timestamp}] {event.node_id} -> "
                    f"Alerts: {', '.join(alerts)} "
                    f"(CPU={event.cpu_percent}%, DB_QPS={event.db_queries_per_sec}, "
                    f"AuthFails={event.auth_failures})"
                )

    return local_audit_log


if __name__ == "__main__":
    run_simulation()