#!/usr/bin/env python3
"""Custom extraction example: Define your own Pydantic models.

This example shows how to extract custom structured data by defining
your own Pydantic models that match your specific use case.

Requirements:
    pip install instructor-builtsimple
    export OPENAI_API_KEY=your-api-key
"""

from pydantic import BaseModel, Field

from instructor_builtsimple import ResearchClient


# Define custom extraction models
class DrugInformation(BaseModel):
    """Extracted information about pharmaceutical drugs."""

    drug_names: list[str] = Field(
        description="Names of drugs mentioned in the research"
    )
    mechanisms_of_action: list[str] = Field(
        description="How the drugs work at a molecular/biological level"
    )
    target_conditions: list[str] = Field(
        description="Medical conditions the drugs are used to treat"
    )
    side_effects: list[str] = Field(
        default_factory=list,
        description="Known side effects or adverse reactions"
    )
    clinical_trial_info: list[str] = Field(
        default_factory=list,
        description="Information about clinical trials if mentioned"
    )


class TechnologyComparison(BaseModel):
    """Comparison of AI/ML technologies."""

    technologies: list[str] = Field(description="Technologies being compared")
    use_cases: dict[str, list[str]] = Field(
        description="Use cases for each technology"
    )
    performance_notes: list[str] = Field(
        description="Performance comparisons or benchmarks mentioned"
    )
    trade_offs: list[str] = Field(
        description="Trade-offs between the technologies"
    )
    recommendation: str | None = Field(
        default=None,
        description="Recommendation based on the research"
    )


class ResearchTrends(BaseModel):
    """Trends extracted from research literature."""

    field: str = Field(description="Research field being analyzed")
    emerging_topics: list[str] = Field(
        description="Emerging research topics or trends"
    )
    declining_interest: list[str] = Field(
        default_factory=list,
        description="Topics with declining research interest"
    )
    key_institutions: list[str] = Field(
        default_factory=list,
        description="Leading institutions in this field"
    )
    future_predictions: list[str] = Field(
        description="Predictions about future research directions"
    )


def main():
    client = ResearchClient(model="gpt-4o-mini")

    print("=" * 60)
    print("Example 1: Drug Information Extraction")
    print("=" * 60)

    drug_info = client.extract(
        query="Alzheimer's disease treatments",
        response_model=DrugInformation,
        sources=["pubmed"],
        limit=5,
    )

    print(f"\n💊 Drugs Found: {', '.join(drug_info.drug_names)}")
    print("\n🔬 Mechanisms of Action:")
    for mech in drug_info.mechanisms_of_action:
        print(f"   • {mech}")
    print("\n🎯 Target Conditions:")
    for condition in drug_info.target_conditions:
        print(f"   • {condition}")
    if drug_info.side_effects:
        print("\n⚠️ Side Effects:")
        for effect in drug_info.side_effects[:5]:
            print(f"   • {effect}")

    print("\n" + "=" * 60)
    print("Example 2: Technology Comparison")
    print("=" * 60)

    tech_comparison = client.extract(
        query="BERT vs GPT vs T5 language models comparison",
        response_model=TechnologyComparison,
        sources=["arxiv", "wikipedia"],
        limit=5,
    )

    print(f"\n🔧 Technologies: {', '.join(tech_comparison.technologies)}")
    print("\n📋 Use Cases:")
    for tech, cases in tech_comparison.use_cases.items():
        print(f"   {tech}:")
        for case in cases[:2]:
            print(f"     • {case}")
    print("\n⚖️ Trade-offs:")
    for trade_off in tech_comparison.trade_offs:
        print(f"   • {trade_off}")
    if tech_comparison.recommendation:
        print(f"\n💡 Recommendation: {tech_comparison.recommendation}")

    print("\n" + "=" * 60)
    print("Example 3: Research Trends")
    print("=" * 60)

    trends = client.extract(
        query="quantum computing applications 2024",
        response_model=ResearchTrends,
        sources=["arxiv", "wikipedia"],
        limit=10,
    )

    print(f"\n📊 Field: {trends.field}")
    print("\n🚀 Emerging Topics:")
    for topic in trends.emerging_topics:
        print(f"   • {topic}")
    if trends.key_institutions:
        print("\n🏛️ Key Institutions:")
        for inst in trends.key_institutions[:5]:
            print(f"   • {inst}")
    print("\n🔮 Future Predictions:")
    for pred in trends.future_predictions:
        print(f"   • {pred}")

    print("\n✅ Done!")


if __name__ == "__main__":
    main()
