"""Independently-testable trust-score factor components.

Each module here computes exactly one factor (0-100) plus, where
relevant, a human-readable explanation. ``engine/trust_engine.py``
composes them; nothing else should reach into these modules directly.
"""
