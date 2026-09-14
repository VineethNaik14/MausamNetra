import argparse
import json
import os

from ..backend_bridge import push_report


def consume(
    topic: str, timeout_ms: int = 5000, deliver_to_backend: bool = True
) -> None:
    """Continuously consume standardized weather reports from Kafka."""
    bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "")

    if not bootstrap:
        print("[CONSUMER] KAFKA_BOOTSTRAP_SERVERS is not set.")
        print("[CONSUMER] Start a Kafka broker or use producer fallback mode.")
        return

    from kafka import KafkaConsumer

    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=bootstrap,
        auto_offset_reset="latest",
        enable_auto_commit=True,
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
        consumer_timeout_ms=timeout_ms,
        # Pinned explicitly: kafka-python's auto-version-detection handshake
        # silently fails against modern KRaft-mode brokers (e.g.
        # apache/kafka:3.9.0), so autodetection is never allowed to run here.
        api_version=(2, 5, 0),
    )

    print(f"[CONSUMER] Listening on {topic}")

    try:
        for message in consumer:
            print(
                f"[CONSUMER] {topic} | partition={message.partition} | "
                f"offset={message.offset}"
            )
            print(json.dumps(message.value, indent=2, ensure_ascii=False))
            if deliver_to_backend:
                # This is the hop that was previously missing entirely -
                # without it, consumed reports were never persisted,
                # classified, verified, or shown on the dashboard.
                push_report(message.value)
    except KeyboardInterrupt:
        print("\n[CONSUMER] Stopped by user")
    finally:
        consumer.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", default="weather.cleaned")
    parser.add_argument(
        "--no-backend",
        action="store_true",
        help="Consume and print only, without POSTing to the backend.",
    )
    args = parser.parse_args()
    consume(args.topic, deliver_to_backend=not args.no_backend)


if __name__ == "__main__":
    main()
