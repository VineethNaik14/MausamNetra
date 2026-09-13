import argparse
import json
import os


def consume(topic: str, timeout_ms: int = 5000) -> None:
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
    )

    print(f"[CONSUMER] Listening on {topic}")

    try:
        for message in consumer:
            print(
                f"[CONSUMER] {topic} | partition={message.partition} | "
                f"offset={message.offset}"
            )
            print(json.dumps(message.value, indent=2, ensure_ascii=False))
    except KeyboardInterrupt:
        print("\n[CONSUMER] Stopped by user")
    finally:
        consumer.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", default="weather.cleaned")
    args = parser.parse_args()
    consume(args.topic)


if __name__ == "__main__":
    main()
