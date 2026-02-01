"""Instructor-based extractors for structured data from research APIs.

These extractors combine API calls with LLM-powered structured extraction
using Instructor and Pydantic models.
"""

from typing import Any, TypeVar

import instructor
from openai import OpenAI
from pydantic import BaseModel

from instructor_builtsimple.api import APIConfig, BuiltSimpleAPI
from instructor_builtsimple.models import (
    ArxivPaper,
    Citation,
    ComparisonAnalysis,
    KeyFinding,
    PubMedArticle,
    ResearchSummary,
    TopicAnalysis,
    WikipediaArticle,
)

T = TypeVar("T", bound=BaseModel)


def _format_pubmed_context(results: list[dict[str, Any]], query: str) -> str:
    """Format PubMed results into context for LLM."""
    if not results:
        return f"No PubMed results found for query: {query}"

    parts = [f"PubMed search results for '{query}':\n"]
    for i, r in enumerate(results, 1):
        parts.append(f"\n--- Article {i} ---")
        parts.append(f"PMID: {r.get('pmid', 'N/A')}")
        parts.append(f"Title: {r.get('title', 'N/A')}")
        parts.append(f"Journal: {r.get('journal', 'N/A')}")
        parts.append(f"Year: {r.get('pub_year', 'N/A')}")
        parts.append(f"URL: {r.get('url', 'N/A')}")
        if r.get("abstract"):
            parts.append(f"Abstract: {r['abstract']}")
    return "\n".join(parts)


def _format_arxiv_context(results: list[dict[str, Any]], query: str) -> str:
    """Format ArXiv results into context for LLM."""
    if not results:
        return f"No ArXiv results found for query: {query}"

    parts = [f"ArXiv search results for '{query}':\n"]
    for i, r in enumerate(results, 1):
        parts.append(f"\n--- Paper {i} ---")
        parts.append(f"ArXiv ID: {r.get('arxiv_id', 'N/A')}")
        parts.append(f"Title: {r.get('title', 'N/A')}")
        parts.append(f"Authors: {r.get('authors', 'N/A')}")
        parts.append(f"Year: {r.get('year', 'N/A')}")
        parts.append(f"URL: https://arxiv.org/abs/{r.get('arxiv_id', '')}")
        if r.get("abstract"):
            parts.append(f"Abstract: {r['abstract']}")
    return "\n".join(parts)


def _format_wikipedia_context(results: list[dict[str, Any]], query: str) -> str:
    """Format Wikipedia results into context for LLM."""
    if not results:
        return f"No Wikipedia results found for query: {query}"

    parts = [f"Wikipedia search results for '{query}':\n"]
    for i, r in enumerate(results, 1):
        parts.append(f"\n--- Article {i} ---")
        parts.append(f"Title: {r.get('title', 'N/A')}")
        parts.append(f"Category: {r.get('category', 'N/A')}")
        if r.get("summary"):
            parts.append(f"Summary: {r['summary']}")
    return "\n".join(parts)


class BaseExtractor:
    """Base class for Instructor-based extractors."""

    def __init__(
        self,
        client: OpenAI | None = None,
        api_config: APIConfig | None = None,
        model: str = "gpt-4o-mini",
    ):
        """Initialize the extractor.

        Args:
            client: OpenAI client. Creates one if not provided.
            api_config: API configuration for Built-Simple endpoints.
            model: Model to use for extraction.
        """
        self.openai_client = client or OpenAI()
        self.instructor_client = instructor.from_openai(self.openai_client)
        self.api = BuiltSimpleAPI(api_config)
        self.model = model

    def extract(
        self,
        context: str,
        response_model: type[T],
        system_prompt: str | None = None,
    ) -> T:
        """Extract structured data from context using Instructor.

        Args:
            context: Text context to extract from.
            response_model: Pydantic model defining the output schema.
            system_prompt: Optional system prompt override.

        Returns:
            Instance of response_model with extracted data.
        """
        default_system = (
            "You are a research assistant that extracts structured information "
            "from academic sources. Be accurate, concise, and cite sources properly."
        )

        return self.instructor_client.chat.completions.create(
            model=self.model,
            response_model=response_model,
            messages=[
                {"role": "system", "content": system_prompt or default_system},
                {"role": "user", "content": context},
            ],
        )


class PubMedExtractor(BaseExtractor):
    """Extract structured data from PubMed search results."""

    def search_and_extract(
        self,
        query: str,
        limit: int = 5,
        response_model: type[T] | None = None,
    ) -> T | list[PubMedArticle]:
        """Search PubMed and extract structured data.

        Args:
            query: Search query for PubMed.
            limit: Maximum number of results to fetch.
            response_model: Optional custom Pydantic model. Defaults to list[PubMedArticle].

        Returns:
            Extracted structured data.
        """
        # Fetch from API
        data = self.api.search_pubmed(query, limit)
        results = data.get("results", [])
        context = _format_pubmed_context(results, query)

        # Use custom model or default
        if response_model:
            return self.extract(context, response_model)

        # Default: extract list of PubMedArticle
        prompt = f"""Extract structured information from these PubMed articles.
For each article, provide:
- A 1-2 sentence summary of the abstract
- Key findings (main conclusions)
- Methodology if mentioned
- Relevance score based on the query '{query}'

{context}"""

        class PubMedArticleList(BaseModel):
            articles: list[PubMedArticle]

        result = self.extract(prompt, PubMedArticleList)
        return result.articles


class ArxivExtractor(BaseExtractor):
    """Extract structured data from ArXiv search results."""

    def search_and_extract(
        self,
        query: str,
        limit: int = 5,
        response_model: type[T] | None = None,
    ) -> T | list[ArxivPaper]:
        """Search ArXiv and extract structured data.

        Args:
            query: Search query for ArXiv.
            limit: Maximum number of results to fetch.
            response_model: Optional custom Pydantic model.

        Returns:
            Extracted structured data.
        """
        data = self.api.search_arxiv(query, limit)
        results = data.get("results", [])
        context = _format_arxiv_context(results, query)

        if response_model:
            return self.extract(context, response_model)

        prompt = f"""Extract structured information from these ArXiv papers.
For each paper, provide:
- A 1-2 sentence summary of the abstract
- Main contribution or novelty
- Research categories
- Relevance score based on the query '{query}'

{context}"""

        class ArxivPaperList(BaseModel):
            papers: list[ArxivPaper]

        result = self.extract(prompt, ArxivPaperList)
        return result.papers


class WikipediaExtractor(BaseExtractor):
    """Extract structured data from Wikipedia search results."""

    def search_and_extract(
        self,
        query: str,
        limit: int = 5,
        category: str | None = None,
        response_model: type[T] | None = None,
    ) -> T | list[WikipediaArticle]:
        """Search Wikipedia and extract structured data.

        Args:
            query: Search query for Wikipedia.
            limit: Maximum number of results to fetch.
            category: Optional category filter.
            response_model: Optional custom Pydantic model.

        Returns:
            Extracted structured data.
        """
        data = self.api.search_wikipedia(query, limit, category)
        results = data.get("results", [])
        context = _format_wikipedia_context(results, query)

        if response_model:
            return self.extract(context, response_model)

        prompt = f"""Extract structured information from these Wikipedia articles.
For each article, provide:
- A 2-3 sentence summary
- Key facts or important points
- Related topics mentioned
- Relevance score based on the query '{query}'

{context}"""

        class WikipediaArticleList(BaseModel):
            articles: list[WikipediaArticle]

        result = self.extract(prompt, WikipediaArticleList)
        return result.articles


class ResearchExtractor(BaseExtractor):
    """Extract and synthesize structured data from multiple research sources."""

    def search_and_synthesize(
        self,
        query: str,
        limit: int = 5,
        sources: list[str] | None = None,
    ) -> ResearchSummary:
        """Search multiple sources and synthesize into a research summary.

        Args:
            query: Search query.
            limit: Maximum results per source.
            sources: List of sources ('pubmed', 'arxiv', 'wikipedia').

        Returns:
            Synthesized ResearchSummary.
        """
        sources = sources or ["pubmed", "arxiv", "wikipedia"]
        all_results = self.api.search_all(query, limit, sources)

        # Build combined context
        context_parts = [f"Research query: {query}\n"]
        source_counts: dict[str, int] = {}

        if "pubmed" in all_results:
            results = all_results["pubmed"].get("results", [])
            source_counts["pubmed"] = len(results)
            context_parts.append(_format_pubmed_context(results, query))

        if "arxiv" in all_results:
            results = all_results["arxiv"].get("results", [])
            source_counts["arxiv"] = len(results)
            context_parts.append(_format_arxiv_context(results, query))

        if "wikipedia" in all_results:
            results = all_results["wikipedia"].get("results", [])
            source_counts["wikipedia"] = len(results)
            context_parts.append(_format_wikipedia_context(results, query))

        context = "\n\n".join(context_parts)
        total_sources = sum(source_counts.values())

        prompt = f"""Synthesize a comprehensive research summary from these sources.

Provide:
1. Executive summary (3-5 sentences covering the key aspects)
2. Key findings with citations to specific sources (use PMID, ArXiv ID, or Wikipedia title)
3. Knowledge gaps or areas needing more research
4. Practical applications or implications

The summary should integrate information across all sources, not just list them.

{context}

Total sources analyzed: {total_sources}
Source breakdown: {source_counts}"""

        result = self.extract(prompt, ResearchSummary)
        result.sources_analyzed = total_sources
        result.source_breakdown = source_counts
        return result

    def analyze_topic(
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
        """
        sources = sources or ["pubmed", "arxiv", "wikipedia"]
        all_results = self.api.search_all(topic, limit, sources)

        context_parts = [f"Topic: {topic}\n"]

        for source, data in all_results.items():
            results = data.get("results", [])
            if source == "pubmed":
                context_parts.append(_format_pubmed_context(results, topic))
            elif source == "arxiv":
                context_parts.append(_format_arxiv_context(results, topic))
            elif source == "wikipedia":
                context_parts.append(_format_wikipedia_context(results, topic))

        context = "\n\n".join(context_parts)

        prompt = f"""Perform a comprehensive analysis of this research topic.

Provide:
1. Clear definition of the topic
2. Historical context and evolution
3. Current state of research/knowledge
4. Key researchers or institutions
5. Major developments (chronological)
6. Open research questions or debates
7. Predicted future directions
8. Key citations supporting your analysis

{context}"""

        return self.extract(prompt, TopicAnalysis)

    def compare(
        self,
        items: list[str],
        context_query: str | None = None,
        limit: int = 5,
    ) -> ComparisonAnalysis:
        """Compare multiple concepts, methods, or technologies.

        Args:
            items: List of items to compare (2-5 items).
            context_query: Optional query for additional context.
            limit: Results per source for context query.

        Returns:
            ComparisonAnalysis with structured comparison.
        """
        # Build comparison query
        query = " vs ".join(items)
        if context_query:
            query = f"{query} {context_query}"

        all_results = self.api.search_all(query, limit)

        context_parts = [f"Comparing: {', '.join(items)}\n"]

        for source, data in all_results.items():
            results = data.get("results", [])
            if source == "pubmed":
                context_parts.append(_format_pubmed_context(results, query))
            elif source == "arxiv":
                context_parts.append(_format_arxiv_context(results, query))
            elif source == "wikipedia":
                context_parts.append(_format_wikipedia_context(results, query))

        context = "\n\n".join(context_parts)

        prompt = f"""Compare these items: {', '.join(items)}

Provide:
1. Criteria used for comparison
2. Key similarities between items
3. Key differences between items
4. Strengths of each item
5. Weaknesses of each item
6. Recommendation or conclusion (if applicable)
7. Citations supporting the comparison

{context}"""

        return self.extract(prompt, ComparisonAnalysis)
