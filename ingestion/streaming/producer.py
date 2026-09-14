import json
import os
import time
from typing import Any, Optional


class StreamProducer:
    """Kafka producer with a safe console fallback for local/SIH demos."""

    def __init__(self, topic: str = "weather.cleaned"):
        self.topic = topic
        self.bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "")
        self._producer = None

        if self.bootstrap:
            try:
                from kafka import KafkaProducer
                self._producer = KafkaProducer(
                    bootstrap_servers=self.bootstrap,
                    value_serializer=lambda value: json.dumps(
                        value, ensure_ascii=False
                    ).encode("utf-8"),
                    # Pinned explicitly: kafka-python's auto-version-detection
                    # handshake silently fails against modern KRaft-mode
                    # brokers (e.g. apache/kafka:3.9.0), so autodetection is
                    # never allowed to run here.
                    api_version=(2, 5, 0),
                )
                print(f"[KAFKA] Connected to {self.bootstrap}")
            except Exception as exc:
                print(f"[KAFKA] Connection unavailable; using console fallback: {exc}")

    @property
    def kafka_enabled(self) -> bool:
        return self._producer is not None

    def publish(self, report: dict[str, Any]) -> None:
        if self._producer is not None:
            self._producer.send(self.topic, report)
            self._producer.flush()
            print(f"[KAFKA] Published -> {self.topic}")
        else:
            print(
                f"[STREAM-FALLBACK] {self.topic} -> "
                f"{json.dumps(report, ensure_ascii=False)}"
            )

    def close(self) -> None:
        if self._producer is not None:
            self._producer.flush()
            self._producer.close()
