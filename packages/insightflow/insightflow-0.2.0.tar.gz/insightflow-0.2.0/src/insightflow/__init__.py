"""InsightFlow - AI-powered research automation tool."""

try:
    from importlib.metadata import version

    __version__ = version("insightflow")
except Exception:
    from insightflow._version import __version__
