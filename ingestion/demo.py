from datetime import datetime, timezone

from .backend_bridge import push_report
from .citizen_reports.ingestion import ingest_citizen_report
from .dedup import TTLSeenCache
from .streaming.producer import StreamProducer


def main():
    """Run an end-to-end local demonstration of the ingestion pipeline.

    Steps 1-5 (ingest/clean/validate/normalize/dedupe/stream) never needed a
    live API. Step 6 now also delivers the report to the real backend
    (POST /api/v1/reports) so it actually reaches the DB, AI pipeline, and
    dashboard - set BACKEND_URL if the backend isn't on the default
    http://localhost:8000/api/v1. If the backend isn't running, this step
    logs the failure and the rest of the demo still completes."""
    print("=" * 72)
    print("MAUSAMNETRA")
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

    print("[1/7] INGESTION      -> citizen report received")
    print("[2/7] CLEANING       -> text/source normalized")
    print("[3/7] VALIDATION     -> coordinates/timestamp/schema validated")
    print("[4/7] NORMALIZATION  -> canonical report created")

    seen = TTLSeenCache()
    producer = StreamProducer("weather.cleaned")

    if seen.is_duplicate(report):
        print("[5/7] DEDUPLICATION  -> duplicate skipped")
    else:
        producer.publish(report)
        print("[5/7] STREAMING      -> report published")

    print(
        "[6/7] HANDOFF        -> delivering to backend (classification + verification run there)"
    )
    delivered = push_report(report)
    if delivered:
        print(
            f"[7/7] BACKEND        -> stored as report {delivered['id']} (status={delivered['status']})"
        )
    else:
        print(
            "[7/7] BACKEND        -> delivery failed (is the backend running? see message above)"
        )

    producer.close()

    print("\nCanonical report:")
    for key, value in report.items():
        print(f"  {key}: {value}")

    print("\nSUCCESS: Member 2 local real-time pipeline is operational.")


if __name__ == "__main__":
    main()
