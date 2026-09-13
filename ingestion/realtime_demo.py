import argparse
import time
from datetime import datetime, timezone

from .dedup import TTLSeenCache
from .normalizer import normalize_record
from .streaming.producer import StreamProducer
from .social_simulator.simulator import CITY_DATA, POSTS


def run(interval: float, topic: str, count: int) -> None:
    """Generate a continuous local stream so the architecture can be tested without an API key."""
    producer = StreamProducer(topic)
    seen = TTLSeenCache(ttl_seconds=60)
    produced = 0

    print("[REALTIME-DEMO] Local live-feed simulation started.")
    print("[REALTIME-DEMO] Press Ctrl+C to stop.")

    try:
        while count == 0 or produced < count:
            city, state, lat, lon = CITY_DATA[produced % len(CITY_DATA)]
            raw = {
                "source": "simulated_social",
                "source_type": "simulated_public_feed",
                "text": POSTS[produced % len(POSTS)],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "latitude": lat,
                "longitude": lon,
                "city": city,
                "state": state,
                "metadata": {"simulated": True, "sequence": produced + 1},
            }

            report = normalize_record(raw).model_dump(mode="json")

            if seen.is_duplicate(report):
                print("[REALTIME-DEMO] duplicate skipped")
            else:
                producer.publish(report)
                print(
                    f"[REALTIME-DEMO] #{produced + 1} -> "
                    f"{report['city']} | {report['text']}"
                )
                produced += 1

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n[REALTIME-DEMO] Stopped.")
    finally:
        producer.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=float, default=2)
    parser.add_argument("--count", type=int, default=0,
                        help="0 = continuous")
    parser.add_argument("--topic", default="weather.cleaned")
    args = parser.parse_args()
    run(args.interval, args.topic, args.count)


if __name__ == "__main__":
    main()
