"""DSPy retriever modules for Built-Simple research APIs.

This module provides retriever classes that integrate with DSPy's
retrieval-augmented generation (RAG) framework.
"""

from typing import Any, List, Optional, Union
from dataclasses import dataclass

import dspy
import httpx


@dataclass
class Passage:
    """A passage returned from a Built-Simple API.
    
    Attributes:
        long_text: The full text content of the passage
        metadata: Additional metadata about the passage
    """
    long_text: str
    metadata: dict
    
    def __str__(self) -> str:
        return self.long_text


class PubMedRM(dspy.Retrieve):
    """DSPy retriever for Built-Simple PubMed API.
    
    Searches 4.5M+ PubMed articles using hybrid semantic + keyword search.
    Returns article abstracts as passages for RAG pipelines.
    
    Features:
        - GPU-accelerated semantic search
        - Hybrid search combining vectors + BM25
        - Rich metadata: PMID, journal, year, DOI
        - Optional full-text retrieval
    
    Example:
        >>> import dspy
        >>> from dspy_builtsimple import PubMedRM
        >>> 
        >>> # Use as configured RM
        >>> rm = PubMedRM(k=5)
        >>> dspy.settings.configure(rm=rm)
        >>> 
        >>> # Or use directly
        >>> results = rm("CRISPR gene editing", k=3)
        >>> for passage in results:
        ...     print(passage.long_text[:100])
    
    Args:
        k: Default number of passages to retrieve (default: 3)
        base_url: API base URL (default: https://pubmed.built-simple.ai)
        timeout: Request timeout in seconds (default: 30.0)
        include_full_text: Fetch full article text instead of abstracts
    """
    
    def __init__(
        self,
        k: int = 3,
        base_url: str = "https://pubmed.built-simple.ai",
        timeout: float = 30.0,
        include_full_text: bool = False,
    ):
        super().__init__(k=k)
        self.base_url = base_url
        self.timeout = timeout
        self.include_full_text = include_full_text
    
    def _fetch_full_text(self, client: httpx.Client, pmid: str) -> Optional[str]:
        """Fetch full article text for a given PMID."""
        try:
            response = client.get(f"{self.base_url}/article/{pmid}/full_text")
            if response.status_code == 200:
                data = response.json()
                return data.get("full_text")
        except Exception:
            pass
        return None
    
    def forward(
        self,
        query_or_queries: Union[str, List[str]],
        k: Optional[int] = None,
        **kwargs,
    ) -> dspy.Prediction:
        """Retrieve passages from PubMed.
        
        Args:
            query_or_queries: Search query string or list of queries
            k: Number of passages to retrieve (overrides default)
            
        Returns:
            dspy.Prediction with 'passages' attribute containing results
        """
        k = k or self.k
        queries = [query_or_queries] if isinstance(query_or_queries, str) else query_or_queries
        
        all_passages = []
        
        with httpx.Client(timeout=self.timeout) as client:
            for query in queries:
                response = client.post(
                    f"{self.base_url}/hybrid-search",
                    json={"query": query, "limit": k},
                )
                response.raise_for_status()
                data = response.json()
                
                for result in data.get("results", []):
                    pmid = result.get("pmid", "")
                    title = result.get("title", "")
                    abstract = result.get("abstract", "")
                    
                    # Optionally fetch full text
                    content = abstract
                    if self.include_full_text and pmid:
                        full_text = self._fetch_full_text(client, pmid)
                        if full_text:
                            content = full_text
                    
                    # Build passage text
                    text_parts = []
                    if title:
                        text_parts.append(f"Title: {title}")
                    if content:
                        text_parts.append(content)
                    
                    passage = Passage(
                        long_text="\n\n".join(text_parts),
                        metadata={
                            "source": "pubmed",
                            "pmid": pmid,
                            "title": title,
                            "journal": result.get("journal"),
                            "pub_year": result.get("pub_year"),
                            "doi": result.get("doi"),
                            "url": result.get("url") or f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                            "similarity_score": result.get("similarity_score"),
                        }
                    )
                    all_passages.append(passage)
        
        return dspy.Prediction(passages=all_passages[:k])


class ArxivRM(dspy.Retrieve):
    """DSPy retriever for Built-Simple ArXiv API.
    
    Searches 2.7M+ ArXiv preprints in physics, math, CS, and ML.
    Returns paper abstracts as passages for RAG pipelines.
    
    Features:
        - GPU-accelerated semantic search
        - Direct PDF links in metadata
        - Author information preserved
    
    Example:
        >>> import dspy
        >>> from dspy_builtsimple import ArxivRM
        >>> 
        >>> rm = ArxivRM(k=5)
        >>> results = rm("transformer attention mechanism")
        >>> for passage in results.passages:
        ...     print(passage.metadata["arxiv_id"])
    
    Args:
        k: Default number of passages to retrieve (default: 3)
        base_url: API base URL (default: https://arxiv.built-simple.ai)
        timeout: Request timeout in seconds (default: 30.0)
    """
    
    def __init__(
        self,
        k: int = 3,
        base_url: str = "https://arxiv.built-simple.ai",
        timeout: float = 30.0,
    ):
        super().__init__(k=k)
        self.base_url = base_url
        self.timeout = timeout
    
    def forward(
        self,
        query_or_queries: Union[str, List[str]],
        k: Optional[int] = None,
        **kwargs,
    ) -> dspy.Prediction:
        """Retrieve passages from ArXiv.
        
        Args:
            query_or_queries: Search query string or list of queries
            k: Number of passages to retrieve (overrides default)
            
        Returns:
            dspy.Prediction with 'passages' attribute containing results
        """
        k = k or self.k
        queries = [query_or_queries] if isinstance(query_or_queries, str) else query_or_queries
        
        all_passages = []
        
        with httpx.Client(timeout=self.timeout) as client:
            for query in queries:
                response = client.get(
                    f"{self.base_url}/api/search",
                    params={"q": query, "limit": k},
                )
                response.raise_for_status()
                data = response.json()
                
                for result in data.get("results", []):
                    arxiv_id = result.get("arxiv_id", "")
                    title = result.get("title", "")
                    authors = result.get("authors", "")
                    abstract = result.get("abstract", "")
                    
                    # Build passage text
                    text_parts = []
                    if title:
                        text_parts.append(f"Title: {title}")
                    if authors:
                        text_parts.append(f"Authors: {authors}")
                    if abstract:
                        text_parts.append(abstract)
                    
                    passage = Passage(
                        long_text="\n\n".join(text_parts),
                        metadata={
                            "source": "arxiv",
                            "arxiv_id": arxiv_id,
                            "title": title,
                            "authors": authors,
                            "year": result.get("year"),
                            "url": f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else None,
                            "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}.pdf" if arxiv_id else None,
                            "similarity_score": result.get("similarity"),
                        }
                    )
                    all_passages.append(passage)
        
        return dspy.Prediction(passages=all_passages[:k])


class WikipediaRM(dspy.Retrieve):
    """DSPy retriever for Built-Simple Wikipedia API.
    
    Searches 4.8M+ Wikipedia articles using GPU-accelerated semantic search.
    Returns article summaries as passages for RAG pipelines.
    
    Features:
        - GPU-accelerated semantic search with 384-dim embeddings
        - Hybrid search with Elasticsearch
        - Category metadata for filtering
    
    Example:
        >>> import dspy
        >>> from dspy_builtsimple import WikipediaRM
        >>> 
        >>> rm = WikipediaRM(k=5)
        >>> results = rm("quantum computing applications")
        >>> for passage in results.passages:
        ...     print(passage.metadata["title"])
    
    Args:
        k: Default number of passages to retrieve (default: 3)
        base_url: API base URL (default: https://wikipedia.built-simple.ai)
        timeout: Request timeout in seconds (default: 30.0)
    """
    
    def __init__(
        self,
        k: int = 3,
        base_url: str = "https://wikipedia.built-simple.ai",
        timeout: float = 30.0,
    ):
        super().__init__(k=k)
        self.base_url = base_url
        self.timeout = timeout
    
    def forward(
        self,
        query_or_queries: Union[str, List[str]],
        k: Optional[int] = None,
        **kwargs,
    ) -> dspy.Prediction:
        """Retrieve passages from Wikipedia.
        
        Args:
            query_or_queries: Search query string or list of queries
            k: Number of passages to retrieve (overrides default)
            
        Returns:
            dspy.Prediction with 'passages' attribute containing results
        """
        k = k or self.k
        queries = [query_or_queries] if isinstance(query_or_queries, str) else query_or_queries
        
        all_passages = []
        
        with httpx.Client(timeout=self.timeout) as client:
            for query in queries:
                response = client.post(
                    f"{self.base_url}/api/search",
                    json={"query": query, "limit": k},
                )
                response.raise_for_status()
                data = response.json()
                
                for result in data.get("results", []):
                    title = result.get("title", "")
                    summary = result.get("summary", "")
                    category = result.get("category", "")
                    
                    # Build passage text
                    text_parts = []
                    if title:
                        text_parts.append(f"Title: {title}")
                    if category:
                        text_parts.append(f"Category: {category}")
                    if summary:
                        text_parts.append(summary)
                    
                    passage = Passage(
                        long_text="\n\n".join(text_parts),
                        metadata={
                            "source": "wikipedia",
                            "id": result.get("id"),
                            "title": title,
                            "category": category,
                            "url": f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}" if title else None,
                            "similarity_score": result.get("score"),
                        }
                    )
                    all_passages.append(passage)
        
        return dspy.Prediction(passages=all_passages[:k])


class ResearchRM(dspy.Retrieve):
    """Combined DSPy retriever for all Built-Simple research APIs.
    
    Searches across PubMed, ArXiv, and Wikipedia simultaneously,
    returning a diverse set of passages from multiple sources.
    
    Features:
        - Multi-source search in parallel
        - Interleaved results for diversity
        - Configurable per-source limits
    
    Example:
        >>> import dspy
        >>> from dspy_builtsimple import ResearchRM
        >>> 
        >>> # Search all sources
        >>> rm = ResearchRM(k=10, sources=["pubmed", "arxiv", "wikipedia"])
        >>> results = rm("machine learning drug discovery")
        >>> 
        >>> # Group by source
        >>> from collections import Counter
        >>> sources = Counter(p.metadata["source"] for p in results.passages)
        >>> print(sources)  # {'pubmed': 4, 'arxiv': 3, 'wikipedia': 3}
    
    Args:
        k: Total number of passages to retrieve (default: 9)
        sources: List of sources to search (default: all three)
        timeout: Request timeout in seconds (default: 30.0)
    """
    
    def __init__(
        self,
        k: int = 9,
        sources: Optional[List[str]] = None,
        timeout: float = 30.0,
    ):
        super().__init__(k=k)
        self.sources = sources or ["pubmed", "arxiv", "wikipedia"]
        self.timeout = timeout
        
        # Initialize individual retrievers
        self._retrievers = {}
        if "pubmed" in self.sources:
            self._retrievers["pubmed"] = PubMedRM(k=k, timeout=timeout)
        if "arxiv" in self.sources:
            self._retrievers["arxiv"] = ArxivRM(k=k, timeout=timeout)
        if "wikipedia" in self.sources:
            self._retrievers["wikipedia"] = WikipediaRM(k=k, timeout=timeout)
    
    def forward(
        self,
        query_or_queries: Union[str, List[str]],
        k: Optional[int] = None,
        **kwargs,
    ) -> dspy.Prediction:
        """Retrieve passages from all configured sources.
        
        Args:
            query_or_queries: Search query string or list of queries
            k: Total number of passages to retrieve (overrides default)
            
        Returns:
            dspy.Prediction with 'passages' attribute containing interleaved results
        """
        k = k or self.k
        k_per_source = max(1, k // len(self._retrievers))
        
        # Collect results from each source
        source_results = {}
        for source, retriever in self._retrievers.items():
            try:
                result = retriever.forward(query_or_queries, k=k_per_source)
                source_results[source] = result.passages
            except Exception:
                source_results[source] = []
        
        # Interleave results for diversity
        all_passages = []
        max_len = max(len(v) for v in source_results.values()) if source_results else 0
        
        for i in range(max_len):
            for source in self.sources:
                if source in source_results and i < len(source_results[source]):
                    all_passages.append(source_results[source][i])
        
        return dspy.Prediction(passages=all_passages[:k])
