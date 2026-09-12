"""Pydantic schemas for the verification module.

These are the ONLY data contracts the rest of the team should depend on:
    * ``report.py``          — inbound normalized report shape
    * ``classification.py``  — the teammate's event-classifier contract
    * ``verification.py``    — outbound verification/trust-score result
"""
