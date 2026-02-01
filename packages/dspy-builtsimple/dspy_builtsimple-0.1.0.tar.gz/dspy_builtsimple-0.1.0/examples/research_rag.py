#!/usr/bin/env python3
"""Example: Research RAG with Built-Simple APIs.

This example demonstrates building a research Q&A system using
DSPy with Built-Simple retrievers.

Usage:
    # Set your OpenAI API key
    export OPENAI_API_KEY="your-key"
    
    # Run the example
    python examples/research_rag.py
"""

import os
import dspy
from dspy_builtsimple import PubMedRM, ArxivRM, ResearchRM


def basic_retrieval_example():
    """Basic example: retrieve passages from each source."""
    print("=" * 60)
    print("BASIC RETRIEVAL EXAMPLE")
    print("=" * 60)
    
    # PubMed
    print("\n📚 PubMed Search: 'CRISPR gene therapy'")
    print("-" * 40)
    pubmed = PubMedRM(k=3)
    results = pubmed("CRISPR gene therapy")
    for i, p in enumerate(results.passages, 1):
        print(f"{i}. [{p.metadata['pmid']}] {p.metadata['title'][:60]}...")
    
    # ArXiv
    print("\n📄 ArXiv Search: 'transformer attention'")
    print("-" * 40)
    arxiv = ArxivRM(k=3)
    results = arxiv("transformer attention")
    for i, p in enumerate(results.passages, 1):
        print(f"{i}. [{p.metadata['arxiv_id']}] {p.metadata['title'][:60]}...")
    
    # Wikipedia
    print("\n📖 Wikipedia Search: 'machine learning'")
    print("-" * 40)
    from dspy_builtsimple import WikipediaRM
    wiki = WikipediaRM(k=3)
    results = wiki("machine learning")
    for i, p in enumerate(results.passages, 1):
        print(f"{i}. {p.metadata['title'][:60]}...")


def multi_source_example():
    """Example: search across all sources."""
    print("\n" + "=" * 60)
    print("MULTI-SOURCE SEARCH EXAMPLE")
    print("=" * 60)
    
    rm = ResearchRM(k=6, sources=["pubmed", "arxiv", "wikipedia"])
    results = rm("neural network applications in healthcare")
    
    print("\n🔍 Results from all sources:")
    print("-" * 40)
    for i, p in enumerate(results.passages, 1):
        source = p.metadata["source"].upper()
        title = p.metadata.get("title", "Untitled")[:50]
        print(f"{i}. [{source}] {title}...")


def rag_pipeline_example():
    """Example: Full RAG pipeline with DSPy."""
    print("\n" + "=" * 60)
    print("RAG PIPELINE EXAMPLE")
    print("=" * 60)
    
    # Check for API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("\n⚠️  Set OPENAI_API_KEY to run this example")
        print("   export OPENAI_API_KEY='your-key'")
        return
    
    # Configure DSPy
    lm = dspy.LM("openai/gpt-4o-mini")
    rm = PubMedRM(k=5)
    dspy.settings.configure(lm=lm, rm=rm)
    
    # Define signature
    class ResearchQA(dspy.Signature):
        """Answer research questions using scientific literature."""
        context = dspy.InputField(desc="Retrieved scientific passages")
        question = dspy.InputField(desc="Research question")
        answer = dspy.OutputField(desc="Evidence-based answer")
    
    # Build RAG module
    class ResearchRAG(dspy.Module):
        def __init__(self, num_passages=5):
            super().__init__()
            self.retrieve = dspy.Retrieve(k=num_passages)
            self.generate = dspy.ChainOfThought(ResearchQA)
        
        def forward(self, question):
            context = self.retrieve(question).passages
            response = self.generate(context=context, question=question)
            return dspy.Prediction(context=context, answer=response.answer)
    
    # Run the pipeline
    rag = ResearchRAG(num_passages=5)
    
    question = "What are the main mechanisms of action for mRNA vaccines?"
    print(f"\n❓ Question: {question}")
    print("-" * 40)
    
    result = rag(question)
    
    print(f"\n📊 Retrieved {len(result.context)} passages")
    print(f"\n💡 Answer:\n{result.answer}")


def main():
    """Run all examples."""
    print("\n🧬 DSPy Built-Simple Integration Examples\n")
    
    basic_retrieval_example()
    multi_source_example()
    rag_pipeline_example()
    
    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
