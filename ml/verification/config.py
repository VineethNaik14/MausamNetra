"""Centralized, environment-based configuration for the verification engine.

All trust-score weights, decision thresholds and operational limits live
here. Nothing else in the codebase should hard-code these values.

Configuration is read from environment variables (with sane defaults for
local/hackathon development) and validated at import/startup time via
``get_settings()``.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name}='{raw}' is not a valid float") from exc


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name}='{raw}' is not a valid int") from exc


def _str_env(name: str, default: str) -> str:
    raw = os.getenv(name)
    return default if raw is None or raw.strip() == "" else raw


@dataclass(frozen=True)
class TrustWeights:
    """Weights for each trust-score factor. Must sum to ~1.0."""

    source_reliability: float = field(default_factory=lambda: _float_env("TRUST_SOURCE_WEIGHT", 0.20))
    location_consistency: float = field(default_factory=lambda: _float_env("TRUST_LOCATION_WEIGHT", 0.20))
    temporal_consistency: float = field(default_factory=lambda: _float_env("TRUST_TEMPORAL_WEIGHT", 0.15))
    cross_source_agreement: float = field(default_factory=lambda: _float_env("TRUST_CROSS_SOURCE_WEIGHT", 0.20))
    media_text_consistency: float = field(default_factory=lambda: _float_env("TRUST_MEDIA_WEIGHT", 0.15))
    metadata_completeness: float = field(default_factory=lambda: _float_env("TRUST_METADATA_WEIGHT", 0.10))

    def total(self) -> float:
        return (
            self.source_reliability
            + self.location_consistency
            + self.temporal_consistency
            + self.cross_source_agreement
            + self.media_text_consistency
            + self.metadata_completeness
        )

    def validate(self) -> None:
        total = self.total()
        if not (0.98 <= total <= 1.02):
            raise ValueError(
                f"Trust weights must sum to ~1.0, got {total:.4f}. "
                "Check TRUST_*_WEIGHT environment variables."
            )
        for name, value in self.__dict__.items():
            if value < 0:
                raise ValueError(f"Trust weight '{name}' must be non-negative, got {value}")


@dataclass(frozen=True)
class Settings:
    """Application-wide settings for the verification engine."""

    weights: TrustWeights = field(default_factory=TrustWeights)

    verified_threshold: float = field(default_factory=lambda: _float_env("VERIFIED_THRESHOLD", 80.0))
    review_threshold: float = field(default_factory=lambda: _float_env("REVIEW_THRESHOLD", 60.0))

    text_similarity_threshold: float = field(
        default_factory=lambda: _float_env("TEXT_SIMILARITY_THRESHOLD", 0.85)
    )
    text_related_threshold: float = field(
        default_factory=lambda: _float_env("TEXT_RELATED_THRESHOLD", 0.60)
    )
    image_similarity_threshold: float = field(
        default_factory=lambda: _float_env("IMAGE_SIMILARITY_THRESHOLD", 0.90)
    )

    max_image_size_mb: float = field(default_factory=lambda: _float_env("MAX_IMAGE_SIZE_MB", 10.0))
    max_request_body_mb: float = field(default_factory=lambda: _float_env("MAX_REQUEST_BODY_MB", 15.0))

    location_consistency_radius_km: float = field(
        default_factory=lambda: _float_env("LOCATION_CONSISTENCY_RADIUS_KM", 25.0)
    )
    corroboration_radius_km: float = field(
        default_factory=lambda: _float_env("CORROBORATION_RADIUS_KM", 5.0)
    )
    corroboration_window_hours: float = field(
        default_factory=lambda: _float_env("CORROBORATION_WINDOW_HOURS", 12.0)
    )
    max_future_skew_minutes: float = field(
        default_factory=lambda: _float_env("MAX_FUTURE_SKEW_MINUTES", 10.0)
    )
    stale_report_hours: float = field(
        default_factory=lambda: _float_env("STALE_REPORT_HOURS", 72.0)
    )

    similarity_backend: str = field(
        default_factory=lambda: _str_env("SIMILARITY_BACKEND", "tfidf")
    )
    sentence_transformer_model: str = field(
        default_factory=lambda: _str_env("SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2")
    )

    classifier_mode: str = field(default_factory=lambda: _str_env("CLASSIFIER_MODE", "local"))
    classifier_http_url: str = field(default_factory=lambda: _str_env("CLASSIFIER_HTTP_URL", ""))
    classifier_http_timeout_seconds: float = field(
        default_factory=lambda: _float_env("CLASSIFIER_HTTP_TIMEOUT_SECONDS", 3.0)
    )

    log_level: str = field(default_factory=lambda: _str_env("LOG_LEVEL", "INFO"))

    def validate(self) -> None:
        self.weights.validate()
        if self.verified_threshold <= self.review_threshold:
            raise ValueError("VERIFIED_THRESHOLD must be greater than REVIEW_THRESHOLD")
        if not (0 <= self.review_threshold <= 100):
            raise ValueError("REVIEW_THRESHOLD must be within [0, 100]")
        if not (0 <= self.verified_threshold <= 100):
            raise ValueError("VERIFIED_THRESHOLD must be within [0, 100]")
        if not (0 < self.text_similarity_threshold <= 1):
            raise ValueError("TEXT_SIMILARITY_THRESHOLD must be within (0, 1]")
        if not (0 < self.image_similarity_threshold <= 1):
            raise ValueError("IMAGE_SIMILARITY_THRESHOLD must be within (0, 1]")
        if self.max_image_size_mb <= 0:
            raise ValueError("MAX_IMAGE_SIZE_MB must be positive")
        if self.classifier_mode not in {"local", "http"}:
            raise ValueError("CLASSIFIER_MODE must be 'local' or 'http'")
        if self.classifier_mode == "http" and not self.classifier_http_url:
            raise ValueError("CLASSIFIER_HTTP_URL must be set when CLASSIFIER_MODE='http'")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return process-wide settings, validated once and cached.

    Using ``lru_cache`` gives us a cheap singleton without global mutable
    state scattered across modules. Tests can call
    ``get_settings.cache_clear()`` after monkeypatching environment
    variables to force re-read.
    """
    settings = Settings()
    settings.validate()
    return settings
