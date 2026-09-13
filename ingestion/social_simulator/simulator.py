import argparse
import random
import time
from datetime import datetime, timezone
from typing import Iterator

from ..dedup import TTLSeenCache
from ..normalizer import normalize_record
from ..streaming.producer import StreamProducer


CITY_DATA = [
    ("Bengaluru", "Karnataka", 13.0358, 77.5970),
    ("Mumbai", "Maharashtra", 19.0760, 72.8777),
    ("Chennai", "Tamil Nadu", 13.0827, 80.2707),
    ("Hyderabad", "Telangana", 17.3850, 78.4867),
    ("Kolkata", "West Bengal", 22.5726, 88.3639),
    ("Delhi", "Delhi", 28.6139, 77.2090),
]

POSTS = [
    "Heavy rain is causing waterlogging on the road.",
    "Strong winds reported in the area.",
    "Thunderstorm activity happening nearby.",
    "Lightning observed during the storm.",
    "Very high temperatures reported today.",
    "Dense fog is reducing visibility.",
    "Hailstorm reported by residents.",
    "Flooding reported after intense rainfall.",
]


def generate_reports(count: int | None = None) -> Iterator[dict]:
    generated = 0

    while count is None or generated < count:
        city, state, lat, lon = random.choice(CITY_DATA)

        raw = {
            "source": "simulated_social",
            "source_type": "simulated_social",
            "text": random.choice(POSTS),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "latitude": lat + random.uniform(-0.01, 0.01),
            "longitude": lon + random.uniform(-0.01, 0.01),
            "city": city,
            "state": state,
            "metadata": {"simulated": True},
        }

        yield normalize_record(raw).model_dump(mode="json")
        generated += 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate a live public-weather feed.")
    parser.add_argument("--count", type=int, default=0,
                        help="0 means continuous mode")
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--topic", default="weather.cleaned")
    args = parser.parse_args()

    producer = StreamProducer(args.topic)
    seen = TTLSeenCache(ttl_seconds=30)

    try:
        count = None if args.count == 0 else args.count

        for report in generate_reports(count):
            if seen.is_duplicate(report):
                print("[SIMULATOR] Duplicate skipped")
            else:
                producer.publish(report)
                print(
                    f"[SIMULATOR] Generated -> {report['city']} | "
                    f"{report['text']}"
                )

            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\n[SIMULATOR] Stopped by user")
    finally:
        producer.close()


if __name__ == "__main__":
    main()
