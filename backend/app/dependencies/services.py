"""
Dependency-injection factories for all services.

============================================================================
THIS IS THE FILE OTHER TEAMS EDIT TO PLUG IN THEIR REAL IMPLEMENTATIONS.
============================================================================
To integrate a real AI component, replace the corresponding Mock* class
below with your real class (which must implement the same Protocol) - no
other file needs to change.
"""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.dependencies.database import get_db_session
from app.services.analytics_service import AnalyticsService
from app.services.incident_service import IncidentService
from app.services.integrations.real_duplicate_detector import RealDuplicateDetector
from app.services.integrations.incident_correlator import (
    IncidentCorrelator,
    RuleBasedIncidentCorrelationService,
)

from app.services.media_service import MediaService, get_media_service
from app.services.report_service import ReportService
from app.services.verification_service import VerificationService
from app.services.websocket_service import WebSocketService, get_websocket_service
from app.services.integrations.classifier import EventClassifier
from app.services.integrations.trust_engine import TrustEngine
from app.services.integrations.real_classifier import RealEventClassifier
from app.services.integrations.real_trust_engine import RealTrustEngine


def get_event_classifier() -> EventClassifier:
    return RealEventClassifier()


def get_trust_engine() -> TrustEngine:
    return RealTrustEngine()


def get_duplicate_detector() -> RealDuplicateDetector:
    return RealDuplicateDetector()


def get_incident_correlator() -> IncidentCorrelator:
    return RuleBasedIncidentCorrelationService()


def get_incident_service(
    db: Session = Depends(get_db_session),
    correlator: IncidentCorrelator = Depends(get_incident_correlator),
) -> IncidentService:
    return IncidentService(db, correlator)


def get_report_service(
    db: Session = Depends(get_db_session),
    classifier: EventClassifier = Depends(get_event_classifier),
    trust_engine: TrustEngine = Depends(get_trust_engine),
    duplicate_detector: RealDuplicateDetector = Depends(get_duplicate_detector),
    incident_service: IncidentService = Depends(get_incident_service),
    websocket_service: WebSocketService = Depends(get_websocket_service),
) -> ReportService:
    return ReportService(
        db=db,
        classifier=classifier,
        trust_engine=trust_engine,
        duplicate_detector=duplicate_detector,
        incident_service=incident_service,
        websocket_service=websocket_service,
    )


def get_verification_service(
    db: Session = Depends(get_db_session),
    incident_service: IncidentService = Depends(get_incident_service),
    websocket_service: WebSocketService = Depends(get_websocket_service),
) -> VerificationService:
    return VerificationService(db, incident_service, websocket_service)


def get_analytics_service(db: Session = Depends(get_db_session)) -> AnalyticsService:
    return AnalyticsService(db)


__all__ = [
    "get_event_classifier",
    "get_trust_engine",
    "get_duplicate_detector",
    "get_incident_correlator",
    "get_incident_service",
    "get_report_service",
    "get_verification_service",
    "get_analytics_service",
    "get_media_service",
    "MediaService",
]
