import argparse
import os
import time

from dotenv import load_dotenv

from ..dedup import TTLSeenCache
from ..normalizer import normalize_record
from ..streaming.producer import StreamProducer
from .client import GenericWeatherAPIClient, weather_api_to_raw


def run_polling_worker(
    latitude: float,
    longitude: float,
    city: str | None,
    state: str | None,
    interval_seconds: int,
    topic: str,
    once: bool = False,
) -> None:
    """Continuously poll the weather API and publish normalized observations."""

    load_dotenv()

    client = GenericWeatherAPIClient()
    producer = StreamProducer(topic)
    seen = TTLSeenCache(ttl_seconds=max(interval_seconds * 2, 60))

    print("[WORKER] Member 2 real-time weather worker started")
    print(f"[WORKER] Poll interval: {interval_seconds}s")
    print(f"[WORKER] Output topic: {topic}")

    try:
        while True:
            cycle_started = time.time()

            try:
                provider_payload = client.fetch(latitude, longitude)
                raw = weather_api_to_raw(
                    provider_payload,
                    latitude=latitude,
                    longitude=longitude,
                    city=city,
                    state=state,
                )
                report = normalize_record(raw).model_dump(mode="json")

                if seen.is_duplicate(report):
                    print("[DEDUP] Duplicate observation skipped")
                else:
                    producer.publish(report)
                    print(
                        f"[WORKER] Accepted observation | "
                        f"{report['city']} | {report['timestamp']}"
                    )

            except Exception as exc:
                # One failed API cycle must not kill a continuous streaming worker.
                print(f"[WORKER] Cycle failed: {exc}")

            if once:
                break

            elapsed = time.time() - cycle_started
            sleep_for = max(0, interval_seconds - elapsed)
            time.sleep(sleep_for)

    except KeyboardInterrupt:
        print("\n[WORKER] Stopped by user")
    finally:
        producer.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Continuous MausamRakshak Member 2 weather ingestion worker"
    )
    parser.add_argument("--lat", type=float, default=13.0358)
    parser.add_argument("--lon", type=float, default=77.5970)
    parser.add_argument("--city", default="Bengaluru")
    parser.add_argument("--state", default="Karnataka")
    parser.add_argument("--interval", type=int, default=60)
    parser.add_argument("--topic", default=os.getenv("KAFKA_TOPIC_CLEANED", "weather.cleaned"))
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    run_polling_worker(
        latitude=args.lat,
        longitude=args.lon,
        city=args.city,
        state=args.state,
        interval_seconds=args.interval,
        topic=args.topic,
        once=args.once,
    )


if __name__ == "__main__":
    main()
