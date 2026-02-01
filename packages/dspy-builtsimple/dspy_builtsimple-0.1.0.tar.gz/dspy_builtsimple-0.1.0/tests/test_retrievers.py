"""Tests for dspy-builtsimple retrievers."""

from dspy_builtsimple import PubMedRM, ArxivRM, WikipediaRM


def test_pubmed_retriever():
    """Test PubMed retriever returns results."""
    rm = PubMedRM(k=2)
    results = rm("CRISPR gene editing")
    
    assert hasattr(results, 'passages'), "Should return Prediction with passages"
    assert len(results.passages) > 0, "Should return at least one passage"
    
    passage = results.passages[0]
    assert hasattr(passage, 'long_text'), "Passage should have long_text"
    assert hasattr(passage, 'metadata'), "Passage should have metadata"
    assert 'pmid' in passage.metadata, "Metadata should include pmid"


def test_arxiv_retriever():
    """Test ArXiv retriever returns results."""
    rm = ArxivRM(k=2)
    results = rm("transformer attention mechanism")
    
    assert hasattr(results, 'passages'), "Should return Prediction with passages"
    assert len(results.passages) > 0, "Should return at least one passage"
    
    passage = results.passages[0]
    assert 'arxiv_id' in passage.metadata, "Metadata should include arxiv_id"


def test_wikipedia_retriever():
    """Test Wikipedia retriever returns results."""
    rm = WikipediaRM(k=2)
    results = rm("machine learning")
    
    assert hasattr(results, 'passages'), "Should return Prediction with passages"
    assert len(results.passages) > 0, "Should return at least one passage"


if __name__ == "__main__":
    print("Testing PubMed...")
    test_pubmed_retriever()
    print("✓ PubMed works")
    
    print("Testing ArXiv...")
    test_arxiv_retriever()
    print("✓ ArXiv works")
    
    print("Testing Wikipedia...")
    test_wikipedia_retriever()
    print("✓ Wikipedia works")
    
    print("\nAll tests passed! ✓")
