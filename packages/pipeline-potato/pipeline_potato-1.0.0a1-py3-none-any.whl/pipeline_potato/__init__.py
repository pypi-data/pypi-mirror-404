from importlib.metadata import version as _version

from .core.a_potato import APotato
from .pipeline import pipeline, Pipeline

__version__ = _version("pipeline-potato")
__all__ = [
    "APotato",
    "pipeline",
    "Pipeline",
    "__version__"
]
