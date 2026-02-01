"""Pydantic models for structured extraction from research sources.

These models define the schema for extracting structured data from
PubMed, ArXiv, and Wikipedia using Instructor.
"""

from typing import Optional

from pydantic import BaseModel, Field


# =============================================================================
# Source-Specific Models
# =============================================================================


class PubMedArticle(BaseModel):
    """Structured representation of a PubMed article."""

    pmid: str = Field(description="PubMed ID of the article")
    title: str = Field(description="Title of the article")
    journal: Optional[str] = Field(default=None, description="Journal name")
    year: Optional[int] = Field(default=None, description="Publication year")
    abstract_summary: str = Field(
        description="Concise summary of the abstract in 1-2 sentences"
    )
    key_findings: list[str] = Field(
        default_factory=list,
        description="List of key findings or conclusions from the abstract",
    )
    methodology: Optional[str] = Field(
        default=None, description="Brief description of methodology if mentioned"
    )
    relevance_score: float = Field(
        ge=0, le=1, description="Relevance score from 0-1 based on search query"
    )
    url: str = Field(description="URL to the full article on PubMed")


class ArxivPaper(BaseModel):
    """Structured representation of an ArXiv preprint."""

    arxiv_id: str = Field(description="ArXiv ID (e.g., '2301.12345')")
    title: str = Field(description="Title of the paper")
    authors: list[str] = Field(description="List of author names")
    year: int = Field(description="Publication year")
    abstract_summary: str = Field(
        description="Concise summary of the abstract in 1-2 sentences"
    )
    main_contribution: str = Field(
        description="Primary contribution or novelty of the paper"
    )
    categories: list[str] = Field(
        default_factory=list,
        description="Inferred research categories (e.g., 'machine learning', 'NLP')",
    )
    relevance_score: float = Field(
        ge=0, le=1, description="Relevance score from 0-1 based on search query"
    )
    url: str = Field(description="URL to the paper on ArXiv")


class WikipediaArticle(BaseModel):
    """Structured representation of a Wikipedia article."""

    title: str = Field(description="Title of the Wikipedia article")
    category: Optional[str] = Field(default=None, description="Main category")
    summary: str = Field(
        description="Concise summary of the article content in 2-3 sentences"
    )
    key_facts: list[str] = Field(
        default_factory=list,
        description="List of key facts or important points from the article",
    )
    related_topics: list[str] = Field(
        default_factory=list, description="Related topics or concepts mentioned"
    )
    relevance_score: float = Field(
        ge=0, le=1, description="Relevance score from 0-1 based on search query"
    )


# =============================================================================
# Composite Models for Research Synthesis
# =============================================================================


class Citation(BaseModel):
    """A citation reference extracted from research."""

    source: str = Field(description="Source type: 'pubmed', 'arxiv', or 'wikipedia'")
    identifier: str = Field(description="Source-specific ID (PMID, ArXiv ID, or title)")
    title: str = Field(description="Title of the cited work")
    year: Optional[int] = Field(default=None, description="Publication year if available")
    url: Optional[str] = Field(default=None, description="URL to the source")


class KeyFinding(BaseModel):
    """A key finding synthesized from research sources."""

    finding: str = Field(description="The key finding or insight")
    confidence: float = Field(
        ge=0, le=1, description="Confidence level from 0-1 based on source agreement"
    )
    sources: list[Citation] = Field(
        description="Citations supporting this finding"
    )
    category: Optional[str] = Field(
        default=None,
        description="Category of finding (e.g., 'methodology', 'result', 'application')",
    )


class ResearchSummary(BaseModel):
    """Comprehensive research summary synthesized from multiple sources."""

    query: str = Field(description="Original search query")
    executive_summary: str = Field(
        description="High-level executive summary of the research topic (3-5 sentences)"
    )
    key_findings: list[KeyFinding] = Field(
        description="List of key findings with citations"
    )
    knowledge_gaps: list[str] = Field(
        default_factory=list,
        description="Identified gaps or areas needing more research",
    )
    practical_applications: list[str] = Field(
        default_factory=list, description="Practical applications or implications"
    )
    sources_analyzed: int = Field(description="Number of sources analyzed")
    source_breakdown: dict[str, int] = Field(
        description="Count of sources by type (pubmed, arxiv, wikipedia)"
    )


# =============================================================================
# Extraction Request/Response Models
# =============================================================================


class ExtractionResult(BaseModel):
    """Result from a structured extraction."""

    query: str = Field(description="Original search query")
    sources_used: list[str] = Field(description="Sources that were searched")
    raw_results_count: int = Field(description="Number of raw results from APIs")
    extracted_data: BaseModel = Field(description="The extracted structured data")


class TopicAnalysis(BaseModel):
    """Deep analysis of a research topic."""

    topic: str = Field(description="The research topic being analyzed")
    definition: str = Field(description="Clear definition of the topic")
    historical_context: Optional[str] = Field(
        default=None, description="Brief historical context if available"
    )
    current_state: str = Field(
        description="Current state of research/knowledge on this topic"
    )
    key_researchers: list[str] = Field(
        default_factory=list,
        description="Notable researchers or institutions in this field",
    )
    major_developments: list[str] = Field(
        description="Major developments or breakthroughs in chronological order"
    )
    open_questions: list[str] = Field(
        description="Open research questions or debates"
    )
    future_directions: list[str] = Field(
        default_factory=list, description="Predicted future directions"
    )
    citations: list[Citation] = Field(
        description="Key citations supporting the analysis"
    )


class ComparisonAnalysis(BaseModel):
    """Comparison between two or more concepts/methods."""

    items_compared: list[str] = Field(description="Items being compared")
    comparison_criteria: list[str] = Field(
        description="Criteria used for comparison"
    )
    similarities: list[str] = Field(description="Key similarities between items")
    differences: list[str] = Field(description="Key differences between items")
    strengths: dict[str, list[str]] = Field(
        description="Strengths of each item (item -> list of strengths)"
    )
    weaknesses: dict[str, list[str]] = Field(
        description="Weaknesses of each item (item -> list of weaknesses)"
    )
    recommendation: Optional[str] = Field(
        default=None, description="Recommendation or conclusion if applicable"
    )
    citations: list[Citation] = Field(
        description="Citations supporting the comparison"
    )
