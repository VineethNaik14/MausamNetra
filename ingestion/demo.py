from datetime import datetime, timezone

from .citizen_reports.ingestion import ingest_citizen_report
from .dedup import TTLSeenCache
from .streaming.producer import StreamProducer


def main():
    """Run an end-to-end local demonstration without requiring a live API."""
    print("=" * 72)
    print("MAUSAMRAKSHAK — MEMBER 2 REAL-TIME PIPELINE DEMO")
    print("=" * 72)

    raw = {
        "source": "Citizen Report",
        "source_type": "citizen_report",
        "text": "   Heavy rainfall has caused severe waterlogging near Hebbal.   ",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "latitude": 13.0358,
        "longitude": 77.5970,
        "city": "Bengaluru",
        "district": "Bengaluru Urban",
        "state": "Karnataka",
        "media_url": "image01.jpg",
    }

    report = ingest_citizen_report(raw)

    print("[1/6] INGESTION      -> citizen report received")
    print("[2/6] CLEANING       -> text/source normalized")
    print("[3/6] VALIDATION     -> coordinates/timestamp/schema validated")
    print("[4/6] NORMALIZATION  -> canonical report created")

    seen = TTLSeenCache()
    producer = StreamProducer("weather.cleaned")

    if seen.is_duplicate(report):
        print("[5/6] DEDUPLICATION  -> duplicate skipped")
    else:
        producer.publish(report)
        print("[5/6] STREAMING      -> report published")

    print("[6/6] HANDOFF        -> ready for Member 3 classifier / Member 5 backend")
    producer.close()

    print("\nCanonical report:")
    for key, value in report.items():
        print(f"  {key}: {value}")

    print("\nSUCCESS: Member 2 local real-time pipeline is operational.")


if __name__ == "__main__":
    main()
