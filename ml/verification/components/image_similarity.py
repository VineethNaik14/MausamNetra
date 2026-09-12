"""MODULE 6 — Lightweight image duplicate detection.

Pipeline: image bytes -> decode -> grayscale + resize -> perceptual hash
(difference hash) -> Hamming distance -> similarity score.

This is intentionally simple (no deepfake detection, no deep learning):
it is robust to resizing, recompression and minor colour/brightness
changes, which covers the common "someone reused an old photo" case for
an MVP.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np

from ..exceptions import ImageProcessingError, UnsupportedMediaError
from ..schemas.verification import ImageDuplicateResult

try:
    import cv2  # opencv-python-headless
except ImportError as exc:  # pragma: no cover - hard dependency per project stack
    raise ImportError(
        "opencv-python-headless is required for image_similarity.py (see requirements.txt)"
    ) from exc

_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
_HASH_SIZE = 16  # 16x16 -> 256-bit dHash; good balance of accuracy vs. speed for an MVP


@dataclass(frozen=True)
class PerceptualHash:
    bits: np.ndarray  # boolean array

    def hamming_distance(self, other: "PerceptualHash") -> int:
        if self.bits.shape != other.bits.shape:
            raise ValueError("Cannot compare hashes of different sizes")
        return int(np.count_nonzero(self.bits != other.bits))

    def similarity(self, other: "PerceptualHash") -> float:
        total_bits = self.bits.size
        distance = self.hamming_distance(other)
        return 1.0 - (distance / total_bits)


def validate_image_bytes(data: bytes, content_type: Optional[str], max_size_mb: float) -> None:
    """Basic security/sanity validation before touching image bytes.

    Guards against: oversized uploads, disallowed/mismatched content
    types, and empty/garbage payloads. Does not attempt to sniff for
    malicious payloads beyond what OpenCV's decoder itself rejects.
    """
    if not data:
        raise UnsupportedMediaError("Empty image payload")

    size_mb = len(data) / (1024 * 1024)
    if size_mb > max_size_mb:
        raise UnsupportedMediaError(f"Image size {size_mb:.2f} MB exceeds limit of {max_size_mb} MB")

    if content_type is not None and content_type not in _ALLOWED_CONTENT_TYPES:
        raise UnsupportedMediaError(f"Unsupported content type: {content_type}")


def compute_perceptual_hash(image_bytes: bytes, content_type: Optional[str] = None, max_size_mb: float = 10.0) -> PerceptualHash:
    """Decode image bytes and compute a difference hash (dHash)."""
    validate_image_bytes(image_bytes, content_type, max_size_mb)

    buffer = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(buffer, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ImageProcessingError("Could not decode image; file may be corrupt or not an image")

    resized = cv2.resize(image, (_HASH_SIZE + 1, _HASH_SIZE), interpolation=cv2.INTER_AREA)
    diff = resized[:, 1:] > resized[:, :-1]
    return PerceptualHash(bits=diff)


class ImageDuplicateDetector:
    """Compares an incoming image against a small in-memory hash cache.

    In production the cache would be backed by a database table of
    ``(report_id, phash)``; for the MVP an in-memory dict keeps the
    module independently testable without a database dependency.
    """

    def __init__(self, similarity_threshold: float = 0.90, max_image_size_mb: float = 10.0) -> None:
        self._threshold = similarity_threshold
        self._max_size_mb = max_image_size_mb
        self._known_hashes: Dict[str, PerceptualHash] = {}

    def register(self, report_id: str, image_bytes: bytes, content_type: Optional[str] = None) -> PerceptualHash:
        """Hash and remember an image for future duplicate comparisons."""
        phash = compute_perceptual_hash(image_bytes, content_type, self._max_size_mb)
        self._known_hashes[report_id] = phash
        return phash

    def check_duplicate(
        self, report_id: str, image_bytes: bytes, content_type: Optional[str] = None
    ) -> ImageDuplicateResult:
        candidate_hash = compute_perceptual_hash(image_bytes, content_type, self._max_size_mb)

        best_match_id: Optional[str] = None
        best_similarity = 0.0
        for known_id, known_hash in self._known_hashes.items():
            if known_id == report_id:
                continue
            similarity = candidate_hash.similarity(known_hash)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match_id = known_id

        self._known_hashes[report_id] = candidate_hash

        if best_match_id is not None and best_similarity >= self._threshold:
            return ImageDuplicateResult(
                possible_duplicate=True,
                similarity=round(best_similarity, 4),
                reason=(
                    f"Image perceptual similarity ({best_similarity:.2f}) with report "
                    f"'{best_match_id}' exceeds the configured threshold ({self._threshold:.2f})"
                ),
            )
        return ImageDuplicateResult(
            possible_duplicate=False,
            similarity=round(best_similarity, 4),
            reason="No previously seen image matched closely enough to be considered a duplicate",
        )


def sha256_of(image_bytes: bytes) -> str:
    """Exact-duplicate fingerprint, useful as a cheap pre-filter before hashing."""
    return hashlib.sha256(image_bytes).hexdigest()
