"""Concrete adapters satisfying ``EventClassifierProtocol``.

Both adapters raise ``ClassifierUnavailableError``/``ClassifierTimeoutError``
on failure instead of fabricating a result.
"""
