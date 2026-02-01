"""Instructor integration for Built-Simple research APIs.

This package provides structured data extraction from PubMed, ArXiv, and Wikipedia
using Instructor and Pydantic models.

Example:
    >>> from instructor_builtsimple import ResearchClient
    >>> from instructor_builtsimple.models import ResearchSummary
    >>> 
    >>> client = ResearchClient()
    >>> summary = client.extract(
    ...     query="CRISPR gene editing",
    ...     response_model=ResearchSummary,
    ...     sources=["pubmed", "arxiv"]
    ... )
"""

from instructor_builtsimple.client import ResearchClient
from instructor_builtsimple.extractors import (
    ArxivExtractor,
    PubMedExtractor,
    ResearchExtractor,
    WikipediaExtractor,
)
from instructor_builtsimple.models import (
    ArxivPaper,
    Citation,
    KeyFinding,
    PubMedArticle,
    ResearchSummary,
    WikipediaArticle,
)

__version__ = "0.1.0"

__all__ = [
    # Client
    "ResearchClient",
    # Extractors
    "PubMedExtractor",
    "ArxivExtractor",
    "WikipediaExtractor",
    "ResearchExtractor",
    # Models
    "PubMedArticle",
    "ArxivPaper",
    "WikipediaArticle",
    "ResearchSummary",
    "KeyFinding",
    "Citation",
]
