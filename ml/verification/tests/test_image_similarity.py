from __future__ import annotations

import pytest

from ml.verification.components.image_similarity import ImageDuplicateDetector
from ml.verification.exceptions import ImageProcessingError, UnsupportedMediaError
from .conftest import make_test_image_bytes


def test_identical_image_is_duplicate():
    detector = ImageDuplicateDetector(similarity_threshold=0.90)
    image_bytes = make_test_image_bytes(seed=1)
    detector.register("R1", image_bytes)

    result = detector.check_duplicate("R2", image_bytes)
    assert result.possible_duplicate is True
    assert result.similarity >= 0.90


def test_different_image_is_not_duplicate():
    detector = ImageDuplicateDetector(similarity_threshold=0.90)
    detector.register("R1", make_test_image_bytes(seed=1))

    result = detector.check_duplicate("R2", make_test_image_bytes(seed=42))
    assert result.possible_duplicate is False


def test_oversized_image_rejected():
    detector = ImageDuplicateDetector(max_image_size_mb=0.001)  # ~1 KB limit
    with pytest.raises(UnsupportedMediaError):
        detector.check_duplicate("R1", make_test_image_bytes(seed=1, size=(256, 256)))


def test_invalid_image_bytes_rejected():
    detector = ImageDuplicateDetector()
    with pytest.raises((ImageProcessingError, UnsupportedMediaError)):
        detector.check_duplicate("R1", b"not an image")


def test_empty_image_rejected():
    detector = ImageDuplicateDetector()
    with pytest.raises(UnsupportedMediaError):
        detector.check_duplicate("R1", b"")
