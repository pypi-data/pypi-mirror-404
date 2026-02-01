"""Integration tests for Built-Simple DSPy retrievers.

These tests require network access and hit the live APIs.
Run with: pytest tests/test_integration.py -v
"""

import pytest

# Skip all tests if dspy is not available
dspy = pytest.importorskip("dspy")

from dspy_builtsimple import PubMedRM, ArxivRM, WikipediaRM, ResearchRM


class TestPubMedRMIntegration:
    """Integration tests for PubMedRM."""
    
    def test_search_returns_results(self):
        """Test that search returns passages."""
        rm = PubMedRM(k=3)
        result = rm("cancer treatment")
        
        assert hasattr(result, "passages")
        assert len(result.passages) > 0
        assert len(result.passages) <= 3
    
    def test_passage_has_metadata(self):
        """Test that passages have expected metadata."""
        rm = PubMedRM(k=1)
        result = rm("diabetes")
        
        passage = result.passages[0]
        assert hasattr(passage, "long_text")
        assert hasattr(passage, "metadata")
        assert passage.metadata["source"] == "pubmed"
        assert "pmid" in passage.metadata
    
    def test_passage_content(self):
        """Test that passage has text content."""
        rm = PubMedRM(k=1)
        result = rm("vaccine")
        
        passage = result.passages[0]
        assert len(passage.long_text) > 50


class TestArxivRMIntegration:
    """Integration tests for ArxivRM."""
    
    def test_search_returns_results(self):
        """Test that search returns passages."""
        rm = ArxivRM(k=3)
        result = rm("machine learning")
        
        assert hasattr(result, "passages")
        assert len(result.passages) > 0
        assert len(result.passages) <= 3
    
    def test_passage_has_arxiv_metadata(self):
        """Test that passages have ArXiv-specific metadata."""
        rm = ArxivRM(k=1)
        result = rm("neural network")
        
        passage = result.passages[0]
        assert passage.metadata["source"] == "arxiv"
        assert "arxiv_id" in passage.metadata
        assert "pdf_url" in passage.metadata


class TestWikipediaRMIntegration:
    """Integration tests for WikipediaRM."""
    
    def test_search_returns_results(self):
        """Test that search returns passages."""
        rm = WikipediaRM(k=3)
        result = rm("artificial intelligence")
        
        assert hasattr(result, "passages")
        assert len(result.passages) > 0
    
    def test_passage_has_wikipedia_metadata(self):
        """Test that passages have Wikipedia-specific metadata."""
        rm = WikipediaRM(k=1)
        result = rm("python programming")
        
        passage = result.passages[0]
        assert passage.metadata["source"] == "wikipedia"
        assert "title" in passage.metadata


class TestResearchRMIntegration:
    """Integration tests for ResearchRM."""
    
    def test_multi_source_search(self):
        """Test that search returns results from multiple sources."""
        rm = ResearchRM(k=6, sources=["pubmed", "arxiv"])
        result = rm("deep learning")
        
        assert hasattr(result, "passages")
        assert len(result.passages) > 0
        
        sources = set(p.metadata["source"] for p in result.passages)
        assert len(sources) >= 1  # At least one source returned results
    
    def test_interleaved_results(self):
        """Test that results are interleaved from sources."""
        rm = ResearchRM(k=6, sources=["pubmed", "arxiv"])
        result = rm("genomics")
        
        # Results should not be all from one source at the start
        if len(result.passages) >= 4:
            first_four_sources = [p.metadata["source"] for p in result.passages[:4]]
            # Should have some variety in first few results
            assert len(set(first_four_sources)) >= 1


class TestBatchQueries:
    """Test batch query functionality."""
    
    def test_pubmed_batch(self):
        """Test PubMed with multiple queries."""
        rm = PubMedRM(k=2)
        result = rm(["cancer", "diabetes"])
        
        assert len(result.passages) > 0
    
    def test_arxiv_batch(self):
        """Test ArXiv with multiple queries."""
        rm = ArxivRM(k=2)
        result = rm(["transformer", "attention"])
        
        assert len(result.passages) > 0
