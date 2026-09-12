"""Shared pytest fixtures. No real external services are used — everything
here is either pure-Python or an in-memory fake."""
from __future__ import annotations

import io
from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

from ml.verification.engine.trust_engine import TrustEngine
from ml.verification.schemas.report import NormalizedWeatherReport, RelatedReport, ReportSource


@pytest.fixture
def now() -> datetime:
    return datetime(2026, 9, 12, 10, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def genuine_report(now: datetime) -> NormalizedWeatherReport:
    return NormalizedWeatherReport(
        report_id="WX78231",
        source=ReportSource.CITIZEN,
        text="Heavy rainfall has caused severe waterlogging near Hebbal",
        event_type="flood",
        event_confidence=0.94,
        latitude=13.0358,
        longitude=77.5970,
        city="Hebbal",
        state="Karnataka",
        timestamp=now - timedelta(minutes=5),
    )


@pytest.fixture
def related_corroborating_reports(now: datetime) -> list[RelatedReport]:
    return [
        RelatedReport(
            report_id="WX78232",
            source=ReportSource.WEATHER_API,
            text="Waterlogging reported around Hebbal after heavy rain",
            event_type="flood",
            latitude=13.0355,
            longitude=77.5968,
            timestamp=now - timedelta(minutes=20),
        ),
        RelatedReport(
            report_id="WX78233",
            source=ReportSource.VERIFIED_NEWS,
            text="Flooded roads reported in Hebbal area of Bengaluru",
            event_type="flood",
            latitude=13.0360,
            longitude=77.5972,
            timestamp=now - timedelta(minutes=30),
        ),
    ]


@pytest.fixture
def trust_engine() -> TrustEngine:
    return TrustEngine()


def make_test_image_bytes(seed: int = 0, size: tuple[int, int] = (64, 64)) -> bytes:
    """Generate a deterministic synthetic PNG (no network/model download needed)."""
    import cv2

    rng = np.random.default_rng(seed)
    image = rng.integers(0, 255, size=(size[0], size[1], 3), dtype=np.uint8)
    success, encoded = cv2.imencode(".png", image)
    assert success
    return encoded.tobytes()
