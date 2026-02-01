"""Basic retrieval example using Built-Simple research APIs."""

from langchain_builtsimple import (
    BuiltSimpleArxivRetriever,
    BuiltSimplePubMedRetriever,
    BuiltSimpleResearchRetriever,
)


def main():
    # Example 1: Search PubMed for medical research
    print("=" * 60)
    print("Example 1: PubMed Search")
    print("=" * 60)
    
    pubmed_retriever = BuiltSimplePubMedRetriever(limit=3)
    docs = pubmed_retriever.invoke("CRISPR gene therapy cancer")
    
    for i, doc in enumerate(docs, 1):
        print(f"\n--- Document {i} ---")
        print(f"Title: {doc.metadata.get('title', 'N/A')}")
        print(f"Journal: {doc.metadata.get('journal', 'N/A')}")
        print(f"Year: {doc.metadata.get('pub_year', 'N/A')}")
        print(f"URL: {doc.metadata.get('url', 'N/A')}")
        print(f"Content preview: {doc.page_content[:200]}...")
    
    # Example 2: Search ArXiv for ML papers
    print("\n" + "=" * 60)
    print("Example 2: ArXiv Search")
    print("=" * 60)
    
    arxiv_retriever = BuiltSimpleArxivRetriever(limit=3)
    docs = arxiv_retriever.invoke("transformer attention mechanism")
    
    for i, doc in enumerate(docs, 1):
        print(f"\n--- Document {i} ---")
        print(f"Title: {doc.metadata.get('title', 'N/A')}")
        print(f"Authors: {doc.metadata.get('authors', 'N/A')}")
        print(f"Year: {doc.metadata.get('year', 'N/A')}")
        print(f"ArXiv ID: {doc.metadata.get('arxiv_id', 'N/A')}")
    
    # Example 3: Combined search across both sources
    print("\n" + "=" * 60)
    print("Example 3: Combined Research Search")
    print("=" * 60)
    
    combined_retriever = BuiltSimpleResearchRetriever(limit_per_source=2)
    docs = combined_retriever.invoke("machine learning drug discovery")
    
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "unknown")
        title = doc.metadata.get("title", "N/A")
        print(f"\n[{source.upper()}] {title}")


if __name__ == "__main__":
    main()
