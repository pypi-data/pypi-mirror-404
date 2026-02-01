#!/usr/bin/env python3
"""Basic example: Extract structured data from research APIs.

This example shows how to use instructor-builtsimple for simple
structured extraction from PubMed, ArXiv, and Wikipedia.

Requirements:
    pip install instructor-builtsimple
    export OPENAI_API_KEY=your-api-key
"""

from instructor_builtsimple import ResearchClient


def main():
    # Initialize the client
    client = ResearchClient(model="gpt-4o-mini")

    print("=" * 60)
    print("Example 1: PubMed Search")
    print("=" * 60)

    # Search PubMed and extract structured articles
    articles = client.pubmed("CRISPR gene therapy", limit=3)

    for article in articles:
        print(f"\n📄 {article.title}")
        print(f"   Journal: {article.journal} ({article.year})")
        print(f"   Summary: {article.abstract_summary}")
        print(f"   Key Findings:")
        for finding in article.key_findings[:2]:
            print(f"     • {finding}")
        print(f"   Relevance: {article.relevance_score:.0%}")
        print(f"   URL: {article.url}")

    print("\n" + "=" * 60)
    print("Example 2: ArXiv Search")
    print("=" * 60)

    # Search ArXiv for preprints
    papers = client.arxiv("large language models", limit=3)

    for paper in papers:
        print(f"\n📑 {paper.title}")
        print(f"   Authors: {', '.join(paper.authors[:3])}")
        if len(paper.authors) > 3:
            print(f"            (+{len(paper.authors) - 3} more)")
        print(f"   Year: {paper.year}")
        print(f"   Main Contribution: {paper.main_contribution}")
        print(f"   Categories: {', '.join(paper.categories)}")
        print(f"   URL: {paper.url}")

    print("\n" + "=" * 60)
    print("Example 3: Wikipedia Search")
    print("=" * 60)

    # Search Wikipedia
    wiki_articles = client.wikipedia("machine learning", limit=3)

    for article in wiki_articles:
        print(f"\n📚 {article.title}")
        print(f"   Category: {article.category}")
        print(f"   Summary: {article.summary}")
        print(f"   Key Facts:")
        for fact in article.key_facts[:3]:
            print(f"     • {fact}")

    print("\n✅ Done!")


if __name__ == "__main__":
    main()
