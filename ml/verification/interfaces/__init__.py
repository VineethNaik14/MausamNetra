"""Abstract interfaces (Protocols) the TrustEngine depends on.

Depending on interfaces rather than concrete implementations is what lets
the teammate's classifier — or the database layer — be swapped without
touching the TrustEngine.
"""
