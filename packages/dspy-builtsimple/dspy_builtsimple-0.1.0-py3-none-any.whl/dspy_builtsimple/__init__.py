"""DSPy retriever modules for Built-Simple research APIs.

This package provides DSPy-compatible retriever modules for searching
scientific literature via Built-Simple's PubMed, ArXiv, and Wikipedia APIs.

Example:
    >>> import dspy
    >>> from dspy_builtsimple import PubMedRM, ArxivRM, WikipediaRM
    >>> 
    >>> # Configure DSPy with a retriever
    >>> rm = PubMedRM(k=5)
    >>> dspy.settings.configure(rm=rm)
    >>> 
    >>> # Use in a RAG pipeline
    >>> retrieve = dspy.Retrieve(k=5)
    >>> results = retrieve("CRISPR gene editing").passages
"""

from dspy_builtsimple.retrievers import (
    ArxivRM,
    PubMedRM,
    WikipediaRM,
    ResearchRM,
)

__version__ = "0.1.0"

__all__ = [
    "PubMedRM",
    "ArxivRM", 
    "WikipediaRM",
    "ResearchRM",
]
