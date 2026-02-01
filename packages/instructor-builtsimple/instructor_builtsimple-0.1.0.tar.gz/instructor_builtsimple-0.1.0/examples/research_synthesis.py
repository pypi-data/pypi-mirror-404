#!/usr/bin/env python3
"""Research synthesis example: Combine multiple sources.

This example demonstrates how to synthesize research from multiple
sources (PubMed, ArXiv, Wikipedia) into comprehensive summaries,
topic analyses, and comparisons.

Requirements:
    pip install instructor-builtsimple
    export OPENAI_API_KEY=your-api-key
"""

from instructor_builtsimple import ResearchClient


def main():
    client = ResearchClient(model="gpt-4o-mini")

    print("=" * 60)
    print("Example 1: Research Synthesis")
    print("=" * 60)

    # Synthesize research from all sources
    summary = client.synthesize(
        query="mRNA vaccine technology",
        limit=5,
        sources=["pubmed", "arxiv", "wikipedia"],
    )

    print(f"\n🔬 Research Query: {summary.query}")
    print(f"\n📊 Sources Analyzed: {summary.sources_analyzed}")
    print(f"   Breakdown: {summary.source_breakdown}")

    print("\n📝 Executive Summary:")
    print(f"   {summary.executive_summary}")

    print("\n🔑 Key Findings:")
    for finding in summary.key_findings:
        print(f"\n   📌 {finding.finding}")
        print(f"      Confidence: {finding.confidence:.0%}")
        if finding.sources:
            print(f"      Sources: {', '.join(s.identifier for s in finding.sources[:3])}")

    if summary.knowledge_gaps:
        print("\n❓ Knowledge Gaps:")
        for gap in summary.knowledge_gaps:
            print(f"   • {gap}")

    if summary.practical_applications:
        print("\n💡 Practical Applications:")
        for app in summary.practical_applications:
            print(f"   • {app}")

    print("\n" + "=" * 60)
    print("Example 2: Topic Analysis")
    print("=" * 60)

    # Deep analysis of a topic
    analysis = client.analyze(
        topic="neural network interpretability",
        limit=8,
        sources=["arxiv", "wikipedia"],
    )

    print(f"\n📚 Topic: {analysis.topic}")
    print(f"\n📖 Definition:\n   {analysis.definition}")

    if analysis.historical_context:
        print(f"\n📜 Historical Context:\n   {analysis.historical_context}")

    print(f"\n🔬 Current State:\n   {analysis.current_state}")

    print("\n🏆 Major Developments:")
    for dev in analysis.major_developments[:5]:
        print(f"   • {dev}")

    print("\n❓ Open Questions:")
    for q in analysis.open_questions:
        print(f"   • {q}")

    if analysis.future_directions:
        print("\n🔮 Future Directions:")
        for direction in analysis.future_directions:
            print(f"   • {direction}")

    print("\n" + "=" * 60)
    print("Example 3: Comparison Analysis")
    print("=" * 60)

    # Compare technologies/methods
    comparison = client.compare(
        items=["supervised learning", "unsupervised learning", "reinforcement learning"],
        context_query="machine learning paradigms",
        limit=5,
    )

    print(f"\n⚖️ Comparing: {', '.join(comparison.items_compared)}")

    print("\n📋 Comparison Criteria:")
    for criterion in comparison.comparison_criteria:
        print(f"   • {criterion}")

    print("\n🤝 Similarities:")
    for sim in comparison.similarities:
        print(f"   • {sim}")

    print("\n↔️ Differences:")
    for diff in comparison.differences:
        print(f"   • {diff}")

    print("\n💪 Strengths:")
    for item, strengths in comparison.strengths.items():
        print(f"   {item}:")
        for s in strengths[:2]:
            print(f"     ✓ {s}")

    print("\n⚠️ Weaknesses:")
    for item, weaknesses in comparison.weaknesses.items():
        print(f"   {item}:")
        for w in weaknesses[:2]:
            print(f"     ✗ {w}")

    if comparison.recommendation:
        print(f"\n💡 Recommendation:\n   {comparison.recommendation}")

    print("\n✅ Done!")


if __name__ == "__main__":
    main()
