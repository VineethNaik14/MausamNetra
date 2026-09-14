"""
Development seed script.

Populates the database with sample users, sources, reports, incidents, and
verification statuses so the frontend/dashboard team has realistic data to
build against immediately.

DOES NOT create a production-usable admin with a hardcoded password - the
seeded admin account uses a clearly-marked development-only password and
should never be used outside local development. Use scripts/create_admin.py
for any real admin account.

Usage:
    python scripts/seed.py
"""
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security import hash_password  # noqa: E402
from app.db.database import SessionLocal  # noqa: E402
from app.models.duplicate import Duplicate  # noqa: E402
from app.models.incident import Incident, IncidentSeverity, IncidentStatus  # noqa: E402
from app.models.report import Report, ReportStatus  # noqa: E402
from app.models.source import Source, SourceType  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.models.verification import Verification, VerificationStatus  # noqa: E402
from app.repositories.report_repository import make_point  # noqa: E402

DEV_ADMIN_EMAIL = "dev-admin@mausamnetra.dev"
DEV_ADMIN_PASSWORD = "DevOnly!ChangeMe123"  # nosec - local development only, never used in production


def seed() -> None:
    db = SessionLocal()
    try:
        # --- Users ---
        if not db.query(User).filter(User.email == DEV_ADMIN_EMAIL).first():
            db.add(
                User(
                    name="Dev Admin",
                    email=DEV_ADMIN_EMAIL,
                    password_hash=hash_password(DEV_ADMIN_PASSWORD),
                    role=UserRole.ADMIN,
                    is_active=True,
                )
            )
            print(f"Seeded DEV admin: {DEV_ADMIN_EMAIL} / {DEV_ADMIN_PASSWORD} (development only!)")

        sample_user_email = "citizen1@example.com"
        if not db.query(User).filter(User.email == sample_user_email).first():
            db.add(
                User(
                    name="Sample Citizen",
                    email=sample_user_email,
                    password_hash=hash_password("Passw0rd!123"),
                    role=UserRole.USER,
                    is_active=True,
                )
            )
        db.commit()

        # --- Sources ---
        source_defs = [
            ("Citizen App", SourceType.CITIZEN, 55.0),
            ("IMD Weather API", SourceType.WEATHER_API, 90.0),
            ("Govt Disaster Cell", SourceType.GOVERNMENT, 95.0),
            ("Regional News Feed", SourceType.NEWS, 70.0),
            ("Public Social Feed", SourceType.PUBLIC_FEED, 40.0),
            ("Simulated Social Stream", SourceType.SIMULATED_SOCIAL, 35.0),
        ]
        sources = {}
        for name, stype, reliability in source_defs:
            existing = db.query(Source).filter(Source.name == name).first()
            if existing:
                sources[name] = existing
                continue
            src = Source(name=name, type=stype, reliability_score=reliability, is_active=True)
            db.add(src)
            db.flush()
            sources[name] = src
        db.commit()

        if db.query(Report).count() > 0:
            print("Reports already exist - skipping report/incident seeding.")
            return

        # --- Sample incident (Bengaluru flood) ---
        now = datetime.now(timezone.utc)
        incident = Incident(
            event_type="FLOOD",
            severity=IncidentSeverity.MODERATE,
            latitude=12.9716,
            longitude=77.5946,
            location=make_point(77.5946, 12.9716),
            state="Karnataka",
            district="Bengaluru Urban",
            city="Bengaluru",
            start_time=now - timedelta(hours=3),
            confidence=0.82,
            status=IncidentStatus.ACTIVE,
            report_count=3,
            verified_count=1,
            suspicious_count=0,
            duplicate_count=1,
        )
        db.add(incident)
        db.flush()

        sample_reports = [
            {
                "text": "Heavy rainfall has flooded roads near Silk Board junction.",
                "event_type": "FLOOD",
                "event_confidence": 0.91,
                "lat": 12.9172,
                "lon": 77.6228,
                "city": "Bengaluru",
                "district": "Bengaluru Urban",
                "state": "Karnataka",
                "source": "Citizen App",
                "status": ReportStatus.PROCESSED,
                "trust_score": 88,
                "verification_status": VerificationStatus.VERIFIED,
            },
            {
                "text": "Waterlogging reported on Outer Ring Road due to continuous rain.",
                "event_type": "FLOOD",
                "event_confidence": 0.85,
                "lat": 12.9352,
                "lon": 77.6146,
                "city": "Bengaluru",
                "district": "Bengaluru Urban",
                "state": "Karnataka",
                "source": "Public Social Feed",
                "status": ReportStatus.PROCESSED,
                "trust_score": 65,
                "verification_status": VerificationStatus.NEEDS_REVIEW,
            },
            {
                "text": "Heavy rainfall flooded roads near Silk Board junction badly.",
                "event_type": "FLOOD",
                "event_confidence": 0.90,
                "lat": 12.9175,
                "lon": 77.6230,
                "city": "Bengaluru",
                "district": "Bengaluru Urban",
                "state": "Karnataka",
                "source": "Simulated Social Stream",
                "status": ReportStatus.PROCESSED,
                "trust_score": 30,
                "verification_status": VerificationStatus.SUSPICIOUS,
                "is_duplicate_of_first": True,
            },
        ]

        first_report_id = None
        for i, r in enumerate(sample_reports):
            report = Report(
                source_id=sources[r["source"]].id,
                text=r["text"],
                event_type=r["event_type"],
                event_confidence=r["event_confidence"],
                timestamp=now - timedelta(hours=3 - i * 0.5),
                latitude=r["lat"],
                longitude=r["lon"],
                location=make_point(r["lon"], r["lat"]),
                city=r["city"],
                district=r["district"],
                state=r["state"],
                status=r["status"],
                incident_id=incident.id,
            )
            db.add(report)
            db.flush()

            if i == 0:
                first_report_id = report.id

            db.add(
                Verification(
                    report_id=report.id,
                    trust_score=r["trust_score"],
                    status=r["verification_status"],
                    reason="Seeded sample verification result",
                )
            )

            if r.get("is_duplicate_of_first") and first_report_id:
                db.add(Duplicate(report_id=report.id, master_report_id=first_report_id, similarity_score=0.93))

        # --- A second, unrelated, lower-severity incident (heatwave) ---
        heatwave = Incident(
            event_type="HEATWAVE",
            severity=IncidentSeverity.LOW,
            latitude=17.3850,
            longitude=78.4867,
            location=make_point(78.4867, 17.3850),
            state="Telangana",
            district="Hyderabad",
            city="Hyderabad",
            start_time=now - timedelta(days=1),
            confidence=0.7,
            status=IncidentStatus.MONITORING,
            report_count=1,
            verified_count=0,
            suspicious_count=0,
            duplicate_count=0,
        )
        db.add(heatwave)
        db.flush()

        heatwave_report = Report(
            source_id=sources["IMD Weather API"].id,
            text="Extreme heat wave conditions recorded across Hyderabad region.",
            event_type="HEATWAVE",
            event_confidence=0.88,
            timestamp=now - timedelta(days=1),
            latitude=17.3850,
            longitude=78.4867,
            location=make_point(78.4867, 17.3850),
            city="Hyderabad",
            district="Hyderabad",
            state="Telangana",
            status=ReportStatus.PROCESSED,
            incident_id=heatwave.id,
        )
        db.add(heatwave_report)
        db.flush()
        db.add(
            Verification(
                report_id=heatwave_report.id,
                trust_score=90,
                status=VerificationStatus.VERIFIED,
                reason="Official IMD Weather API source - seeded",
            )
        )

        db.commit()
        print("Seed data created: 2 incidents, 4 reports, verifications, and 1 duplicate relationship.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
