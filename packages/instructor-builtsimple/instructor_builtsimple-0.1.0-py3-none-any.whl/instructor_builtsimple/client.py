"""High-level client for structured research extraction.

This module provides a unified interface for searching and extracting
structured data from Built-Simple research APIs using Instructor.
"""

from typing import TypeVar

from openai import OpenAI
from pydantic import BaseModel

from instructor_builtsimple.api import APIConfig, BuiltSimpleAPI
from instructor_builtsimple.extractors import (
    ArxivExtractor,
    PubMedExtractor,
    ResearchExtractor,
    WikipediaExtractor,
)
from instructor_builtsimple.models import (
    ArxivPaper,
    ComparisonAnalysis,
    PubMedArticle,
    ResearchSummary,
    TopicAnalysis,
    WikipediaArticle,
)

T = TypeVar("T", bound=BaseModel)


class ResearchClient:
    """Unified client for structured research extraction.

    This client provides a high-level interface for searching research
    databases and extracting structured information using LLMs.

    Example:
        >>> client = ResearchClient()
        >>> 
        >>> # Simple extraction with default models
        >>> articles = client.pubmed("COVID-19 vaccines", limit=5)
        >>> 
        >>> # Custom extraction schema
        >>> from pydantic import BaseModel
        >>> class VaccineSummary(BaseModel):
        ...     vaccine_name: str
        ...     efficacy: str
        ...     side_effects: list[str]
        >>> 
        >>> summary = client.extract(
        ...     query="mRNA vaccine efficacy",
        ...     response_model=VaccineSummary,
        ...     sources=["pubmed"]
        ... )
        >>> 
        >>> # Research synthesis
        >>> synthesis = client.synthesize("CRISPR gene editing")
    """

    def __init__(
        self,
        openai_client: OpenAI | None = None,
        api_config: APIConfig | None = None,
        model: str = "gpt-4o-mini",
    ):
        """Initialize the research client.

        Args:
            openai_client: OpenAI client. Creates one if not provided.
            api_config: Configuration for Built-Simple API endpoints.
            model: Model to use for extraction (default: gpt-4o-mini).
        """
        self.openai_client = openai_client or OpenAI()
        self.api_config = api_config or APIConfig()
        self.model = model

        # Initialize extractors
        self._pubmed = PubMedExtractor(
            client=self.openai_client,
            api_config=self.api_config,
            model=self.model,
        )
        self._arxiv = ArxivExtractor(
            client=self.openai_client,
            api_config=self.api_config,
            model=self.model,
        )
        self._wikipedia = WikipediaExtractor(
            client=self.openai_client,
            api_config=self.api_config,
            model=self.model,
        )
        self._research = ResearchExtractor(
            client=self.openai_client,
            api_config=self.api_config,
            model=self.model,
        )

    @property
    def api(self) -> BuiltSimpleAPI:
        """Access the underlying API client for raw requests."""
        return self._pubmed.api

    def pubmed(
        self,
        query: str,
        limit: int = 5,
        response_model: type[T] | None = None,
    ) -> T | list[PubMedArticle]:
        """Search PubMed and extract structured data.

        Args:
            query: Search query for biomedical literature.
            limit: Maximum number of results (1-20).
            response_model: Optional custom Pydantic model for extraction.

        Returns:
            List of PubMedArticle or custom model instance.

        Example:
            >>> articles = client.pubmed("diabetes treatment", limit=3)
            >>> for article in articles:
            ...     print(f"{article.title}: {article.abstract_summary}")
        """
        return self._pubmed.search_and_extract(query, limit, response_model)

    def arxiv(
        self,
        query: str,
        limit: int = 5,
        response_model: type[T] | None = None,
    ) -> T | list[ArxivPaper]:
        """Search ArXiv and extract structured data.

        Args:
            query: Search query for preprints.
            limit: Maximum number of results (1-25).
            response_model: Optional custom Pydantic model for extraction.

        Returns:
            List of ArxivPaper or custom model instance.

        Example:
            >>> papers = client.arxiv("transformer architecture", limit=5)
            >>> for paper in papers:
            ...     print(f"{paper.title} by {', '.join(paper.authors[:3])}")
        """
        return self._arxiv.search_and_extract(query, limit, response_model)

    def wikipedia(
        self,
        query: str,
        limit: int = 5,
        category: str | None = None,
        response_model: type[T] | None = None,
    ) -> T | list[WikipediaArticle]:
        """Search Wikipedia and extract structured data.

        Args:
            query: Search query.
            limit: Maximum number of results (1-20).
            category: Optional category filter.
            response_model: Optional custom Pydantic model for extraction.

        Returns:
            List of WikipediaArticle or custom model instance.

        Example:
            >>> articles = client.wikipedia("machine learning")
            >>> for article in articles:
            ...     print(f"{article.title}: {article.summary}")
        """
        return self._wikipedia.search_and_extract(query, limit, category, response_model)

    def synthesize(
        self,
        query: str,
        limit: int = 5,
        sources: list[str] | None = None,
    ) -> ResearchSummary:
        """Search and synthesize research from multiple sources.

        This method searches all specified sources and uses an LLM to
        synthesize the results into a comprehensive research summary.

        Args:
            query: Research query.
            limit: Maximum results per source.
            sources: Sources to search ('pubmed', 'arxiv', 'wikipedia').
                    Defaults to all sources.

        Returns:
            ResearchSummary with synthesized findings and citations.

        Example:
            >>> summary = client.synthesize("CRISPR applications")
            >>> print(summary.executive_summary)
            >>> for finding in summary.key_findings:
            ...     print(f"- {finding.finding}")
        """
        return self._research.search_and_synthesize(query, limit, sources)

    def analyze(
        self,
        topic: str,
        limit: int = 10,
        sources: list[str] | None = None,
    ) -> TopicAnalysis:
        """Perform deep analysis of a research topic.

        Args:
            topic: Topic to analyze.
            limit: Maximum results per source.
            sources: Sources to search.

        Returns:
            TopicAnalysis with comprehensive topic breakdown.

        Example:
            >>> analysis = client.analyze("quantum computing")
            >>> print(f"Definition: {analysis.definition}")
            >>> print("Open questions:")
            >>> for q in analysis.open_questions:
            ...     print(f"  - {q}")
        """
        return self._research.analyze_topic(topic, limit, sources)

    def compare(
        self,
        items: list[str],
        context_query: str | None = None,
        limit: int = 5,
    ) -> ComparisonAnalysis:
        """Compare multiple concepts, methods, or technologies.

        Args:
            items: List of items to compare (2-5 items recommended).
            context_query: Optional query for additional context.
            limit: Results per source for context.

        Returns:
            ComparisonAnalysis with structured comparison.

        Example:
            >>> comparison = client.compare(
            ...     ["BERT", "GPT", "T5"],
            ...     context_query="NLP performance"
            ... )
            >>> print("Similarities:", comparison.similarities)
            >>> print("Differences:", comparison.differences)
        """
        return self._research.compare(items, context_query, limit)

    def extract(
        self,
        query: str,
        response_model: type[T],
        sources: list[str] | None = None,
        limit: int = 5,
    ) -> T:
        """Extract custom structured data from research sources.

        This method allows you to define any Pydantic model and extract
        that specific structure from the research results.

        Args:
            query: Search query.
            response_model: Pydantic model defining the extraction schema.
            sources: Sources to search.
            limit: Maximum results per source.

        Returns:
            Instance of response_model with extracted data.

        Example:
            >>> from pydantic import BaseModel, Field
            >>> 
            >>> class DrugInfo(BaseModel):
            ...     drug_names: list[str] = Field(description="Names of drugs mentioned")
            ...     mechanisms: list[str] = Field(description="Mechanisms of action")
            ...     clinical_trials: list[str] = Field(description="Clinical trial info")
            >>> 
            >>> info = client.extract(
            ...     query="Alzheimer's disease treatments",
            ...     response_model=DrugInfo,
            ...     sources=["pubmed"]
            ... )
        """
        # Fetch from all specified sources
        sources = sources or ["pubmed", "arxiv", "wikipedia"]
        all_results = self.api.search_all(query, limit, sources)

        # Build combined context
        context_parts = [f"Research query: {query}\n"]

        for source, data in all_results.items():
            results = data.get("results", [])
            if source == "pubmed":
                context_parts.append(self._format_pubmed(results, query))
            elif source == "arxiv":
                context_parts.append(self._format_arxiv(results, query))
            elif source == "wikipedia":
                context_parts.append(self._format_wikipedia(results, query))

        context = "\n\n".join(context_parts)

        # Extract using Instructor
        return self._research.extract(
            context,
            response_model,
            system_prompt=(
                "You are a research assistant extracting specific structured "
                "information from academic sources. Extract only the requested "
                "fields based on the evidence in the sources. Be accurate."
            ),
        )

    def _format_pubmed(self, results: list[dict], query: str) -> str:
        """Format PubMed results."""
        if not results:
            return ""
        parts = ["PubMed Results:"]
        for r in results:
            parts.append(f"- {r.get('title', 'N/A')} (PMID: {r.get('pmid', 'N/A')})")
            if r.get("abstract"):
                parts.append(f"  Abstract: {r['abstract'][:500]}...")
        return "\n".join(parts)

    def _format_arxiv(self, results: list[dict], query: str) -> str:
        """Format ArXiv results."""
        if not results:
            return ""
        parts = ["ArXiv Results:"]
        for r in results:
            parts.append(f"- {r.get('title', 'N/A')} ({r.get('arxiv_id', 'N/A')})")
            if r.get("abstract"):
                parts.append(f"  Abstract: {r['abstract'][:500]}...")
        return "\n".join(parts)

    def _format_wikipedia(self, results: list[dict], query: str) -> str:
        """Format Wikipedia results."""
        if not results:
            return ""
        parts = ["Wikipedia Results:"]
        for r in results:
            parts.append(f"- {r.get('title', 'N/A')}")
            if r.get("summary"):
                parts.append(f"  Summary: {r['summary']}")
        return "\n".join(parts)
