"""MODULE 4 & 5 — Semantic text similarity (cross-source agreement + duplicate text).

Provides a single ``SimilarityEngine`` interface with two interchangeable
backends:

    * ``TfidfSimilarityEngine``       — default. Pure scikit-learn,
      no network access or model download required. Reliable for a
      hackathon demo environment that may not have internet access.
    * ``SentenceTransformerSimilarityEngine`` — optional, higher-quality
      semantic similarity. Loaded once and reused; falls back to the
      TF-IDF engine if the ``sentence-transformers`` package or the
      model weights are unavailable, so the rest of the system keeps
      working.

Both implementations:
    * load/fit their vectorizer once, not per request
    * cache computed embeddings by report_id
    * expose the same ``compare_reports`` / ``calculate_cross_source_agreement`` API
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Protocol

import numpy as np

from ..schemas.report import NormalizedWeatherReport, RelatedReport, ReportSource

logger = logging.getLogger("mausamnetra.verification.text_similarity")


@dataclass(frozen=True)
class TextComparisonResult:
    similarity: float  # 0-1
    relation: str  # "duplicate" | "related" | "unrelated"


class SimilarityEngine(Protocol):
    """Interface the rest of the system depends on."""

    def embed(self, text: str) -> np.ndarray: ...

    def compare_reports(self, text_a: str, text_b: str) -> float: ...


class _BaseSimilarityEngine:
    """Shared embedding-cache logic for concrete engines."""

    def __init__(self) -> None:
        self._cache: Dict[str, np.ndarray] = {}

    def _cached_embed(self, key: Optional[str], text: str) -> np.ndarray:
        if key is not None and key in self._cache:
            return self._cache[key]
        vector = self._compute_embedding(text)
        if key is not None:
            self._cache[key] = vector
        return vector

    def _compute_embedding(self, text: str) -> np.ndarray:  # pragma: no cover - overridden
        raise NotImplementedError

    @staticmethod
    def _cosine(a: np.ndarray, b: np.ndarray) -> float:
        denom = float(np.linalg.norm(a) * np.linalg.norm(b))
        if denom == 0.0:
            return 0.0
        value = float(np.dot(a, b) / denom)
        return max(-1.0, min(1.0, value))


class TfidfSimilarityEngine(_BaseSimilarityEngine):
    """Default, dependency-light similarity backend using TF-IDF + cosine similarity.

    A fresh vectorizer is fit lazily over the growing corpus of texts it
    has seen (report + related reports passed to it). This is a
    pragmatic MVP choice: for a hackathon-scale report volume this is
    fast and needs no network access; it can be swapped for
    ``SentenceTransformerSimilarityEngine`` via configuration without
    touching any calling code.
    """

    def __init__(self) -> None:
        super().__init__()
        from sklearn.feature_extraction.text import TfidfVectorizer

        self._vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self._fitted = False

    def _refit(self, corpus: List[str]) -> None:
        if not corpus:
            return
        self._vectorizer.fit(corpus)
        self._fitted = True
        self._cache.clear()  # vocabulary changed; cached vectors are stale

    def _compute_embedding(self, text: str) -> np.ndarray:
        if not self._fitted:
            self._refit([text])
        matrix = self._vectorizer.transform([text])
        return np.asarray(matrix.todense())[0]

    def embed(self, text: str, key: Optional[str] = None) -> np.ndarray:
        return self._cached_embed(key, text)

    def fit_corpus(self, texts: Iterable[str]) -> None:
        """Fit the vectorizer over a batch of texts before comparing them.

        Calling this once per batch (instead of refitting per-pair) keeps
        comparisons O(n) instead of O(n^2) in vectorizer fits.
        """
        self._refit([t for t in texts if t])

    def compare_reports(self, text_a: str, text_b: str, key_a: Optional[str] = None, key_b: Optional[str] = None) -> float:
        if not self._fitted:
            self._refit([text_a, text_b])
        vec_a = self._cached_embed(key_a, text_a)
        vec_b = self._cached_embed(key_b, text_b)
        return self._cosine(vec_a, vec_b)


class SentenceTransformerSimilarityEngine(_BaseSimilarityEngine):
    """Higher-quality semantic similarity via Sentence Transformers.

    The model is loaded exactly once (in ``__init__``) and reused for
    every request. If the package or model weights are not available
    (e.g. no internet access in an offline demo environment), this
    raises ``RuntimeError`` at construction time so callers can fall
    back to ``TfidfSimilarityEngine`` — see
    ``build_default_similarity_engine`` below.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        super().__init__()
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:  # pragma: no cover - depends on optional dep
            raise RuntimeError("sentence-transformers is not installed") from exc

        try:
            self._model = SentenceTransformer(model_name)
        except Exception as exc:  # pragma: no cover - depends on network/model cache
            raise RuntimeError(f"Could not load Sentence Transformer model '{model_name}'") from exc

    def _compute_embedding(self, text: str) -> np.ndarray:
        return np.asarray(self._model.encode(text, normalize_embeddings=True))

    def embed(self, text: str, key: Optional[str] = None) -> np.ndarray:
        return self._cached_embed(key, text)

    def compare_reports(self, text_a: str, text_b: str, key_a: Optional[str] = None, key_b: Optional[str] = None) -> float:
        vec_a = self._cached_embed(key_a, text_a)
        vec_b = self._cached_embed(key_b, text_b)
        return self._cosine(vec_a, vec_b)


def build_default_similarity_engine(backend: str = "tfidf", model_name: str = "all-MiniLM-L6-v2") -> SimilarityEngine:
    """Factory that honours configuration but never crashes app startup.

    If ``backend == "sentence_transformer"`` but the dependency/model is
    unavailable, this logs a warning and falls back to TF-IDF rather than
    taking down the whole service.
    """
    if backend == "sentence_transformer":
        try:
            return SentenceTransformerSimilarityEngine(model_name=model_name)
        except RuntimeError as exc:
            logger.warning("Falling back to TF-IDF similarity engine: %s", exc)
            return TfidfSimilarityEngine()
    return TfidfSimilarityEngine()


class DuplicateTextDetector:
    """MODULE 5 — classifies a pair/set of reports as duplicate/related/unrelated."""

    def __init__(
        self,
        engine: SimilarityEngine,
        duplicate_threshold: float = 0.85,
        related_threshold: float = 0.60,
    ) -> None:
        self._engine = engine
        self._duplicate_threshold = duplicate_threshold
        self._related_threshold = related_threshold

    def classify_pair(self, report: NormalizedWeatherReport, other: RelatedReport) -> TextComparisonResult:
        text_a = report.text or ""
        text_b = other.text or ""
        if not text_a or not text_b:
            return TextComparisonResult(similarity=0.0, relation="unrelated")

        similarity = self._engine.compare_reports(
            text_a, text_b, key_a=report.report_id, key_b=other.report_id
        )
        if similarity >= self._duplicate_threshold:
            relation = "duplicate"
        elif similarity >= self._related_threshold:
            relation = "related"
        else:
            relation = "unrelated"
        return TextComparisonResult(similarity=round(similarity, 4), relation=relation)

    def find_best_match(
        self, report: NormalizedWeatherReport, candidates: Iterable[RelatedReport]
    ) -> Optional[tuple[RelatedReport, TextComparisonResult]]:
        best: Optional[tuple[RelatedReport, TextComparisonResult]] = None
        for candidate in candidates:
            result = self.classify_pair(report, candidate)
            if best is None or result.similarity > best[1].similarity:
                best = (candidate, result)
        return best


class CrossSourceAgreementScorer:
    """MODULE 4 — do independent sources corroborate this report?

    Reports from the exact same ``source`` are treated as one voice, not
    independent corroboration (per the project brief) — they still count
    toward "related" grouping but are excluded from the independence
    bonus.
    """

    def __init__(self, engine: SimilarityEngine, related_threshold: float = 0.55) -> None:
        self._engine = engine
        self._related_threshold = related_threshold

    def calculate_cross_source_agreement(
        self, report: NormalizedWeatherReport, related_reports: Iterable[RelatedReport]
    ) -> tuple[float, str]:
        related_reports = list(related_reports)
        if not related_reports:
            return 50.0, "No related reports available to corroborate or contradict this report"

        text_a = report.text or ""
        if not text_a:
            return 40.0, "Report has no text to compare against related reports"

        independent_agreements = 0
        same_source_agreements = 0
        total_considered = 0

        for candidate in related_reports:
            candidate_text = candidate.text or ""
            if not candidate_text:
                continue
            total_considered += 1
            similarity = self._engine.compare_reports(
                text_a, candidate_text, key_a=report.report_id, key_b=candidate.report_id
            )
            if similarity >= self._related_threshold:
                if candidate.source == report.source:
                    same_source_agreements += 1
                else:
                    independent_agreements += 1

        if total_considered == 0:
            return 50.0, "Related reports had no comparable text"

        if independent_agreements >= 2:
            return 95.0, f"{independent_agreements} independent sources corroborate this report"
        if independent_agreements == 1:
            return 78.0, "One independent source corroborates this report"
        if same_source_agreements > 0:
            return 45.0, (
                "Only same-source repetition found; independent corroboration is required "
                "for a strong score"
            )
        return 30.0, "No independent or same-source corroboration found among related reports"
