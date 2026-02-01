"""Tests for instructor-builtsimple API client."""

from instructor_builtsimple.api import BuiltSimpleAPI


def test_pubmed_search():
    """Test PubMed search returns results."""
    api = BuiltSimpleAPI()
    results = api.search_pubmed("CRISPR", limit=2)
    
    assert isinstance(results, dict), "Should return a dict"
    assert "results" in results, "Should have results key"
    assert len(results["results"]) > 0, "Should return at least one result"
    
    article = results["results"][0]
    assert "pmid" in article, "Article should have pmid"
    assert "title" in article, "Article should have title"


def test_arxiv_search():
    """Test ArXiv search returns results."""
    api = BuiltSimpleAPI()
    results = api.search_arxiv("transformers", limit=2)
    
    assert isinstance(results, dict), "Should return a dict"
    assert "results" in results, "Should have results key"
    assert len(results["results"]) > 0, "Should return at least one result"


def test_wikipedia_search():
    """Test Wikipedia search returns results."""
    api = BuiltSimpleAPI()
    results = api.search_wikipedia("machine learning", limit=2)
    
    assert isinstance(results, dict), "Should return a dict"
    assert "results" in results, "Should have results key"


if __name__ == "__main__":
    print("Testing PubMed...")
    test_pubmed_search()
    print("✓ PubMed works")
    
    print("Testing ArXiv...")
    test_arxiv_search()
    print("✓ ArXiv works")
    
    print("Testing Wikipedia...")
    test_wikipedia_search()
    print("✓ Wikipedia works")
    
    print("\nAll tests passed! ✓")
