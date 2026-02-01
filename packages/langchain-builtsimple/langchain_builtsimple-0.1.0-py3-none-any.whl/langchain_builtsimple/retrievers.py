"""LangChain retrievers for Built-Simple research APIs."""

from typing import Any, List, Optional

import httpx
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import Field


class BuiltSimplePubMedRetriever(BaseRetriever):
    """Retriever for Built-Simple PubMed API.
    
    Searches the PubMed database via Built-Simple's hybrid search API,
    returning scientific papers as LangChain Documents.
    
    Features:
        - 4.5M+ articles with semantic + keyword hybrid search
        - Optional FULL TEXT retrieval (not just abstracts)
        - Rich metadata: PMID, DOI, journal, year
    
    Example:
        >>> # Abstract only (default)
        >>> retriever = BuiltSimplePubMedRetriever(limit=5)
        >>> docs = retriever.invoke("CRISPR gene editing")
        >>> 
        >>> # With full text
        >>> retriever = BuiltSimplePubMedRetriever(limit=5, include_full_text=True)
        >>> docs = retriever.invoke("CRISPR gene editing")
        >>> print(docs[0].page_content)  # Full article text!
    """
    
    base_url: str = Field(default="https://pubmed.built-simple.ai")
    limit: int = Field(default=10, description="Maximum number of results to return")
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    include_full_text: bool = Field(
        default=False, 
        description="Fetch full article text instead of just abstracts. Makes additional API calls."
    )
    
    def _fetch_full_text(self, client: httpx.Client, pmid: str) -> Optional[dict]:
        """Fetch full article text for a given PMID."""
        try:
            response = client.get(f"{self.base_url}/article/{pmid}/full_text")
            if response.status_code == 200:
                data = response.json()
                if data.get("full_text"):
                    return data
        except Exception:
            pass
        return None
    
    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: Optional[CallbackManagerForRetrieverRun] = None,
    ) -> List[Document]:
        """Search PubMed and return documents.
        
        Args:
            query: Search query string
            run_manager: Callback manager (optional)
            
        Returns:
            List of Document objects with paper content and metadata
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/hybrid-search",
                json={"query": query, "limit": self.limit},
            )
            response.raise_for_status()
            data = response.json()
            
            documents = []
            for result in data.get("results", []):
                pmid = result.get("pmid")
                title = result.get("title", "")
                abstract = result.get("abstract", "")
                
                # Optionally fetch full text
                full_text_data = None
                has_full_text = False
                if self.include_full_text and pmid:
                    full_text_data = self._fetch_full_text(client, pmid)
                    has_full_text = full_text_data is not None
                
                # Build page content
                content_parts = []
                if title:
                    content_parts.append(f"Title: {title}")
                
                if has_full_text and full_text_data.get("full_text"):
                    # Use full text
                    content_parts.append(f"\nFull Text:\n{full_text_data['full_text']}")
                elif abstract:
                    # Fall back to abstract
                    content_parts.append(f"\nAbstract: {abstract}")
                
                page_content = "\n".join(content_parts) if content_parts else ""
                
                # Build metadata
                metadata = {
                    "source": "pubmed",
                    "pmid": pmid,
                    "title": title,
                    "journal": result.get("journal"),
                    "pub_year": result.get("pub_year"),
                    "doi": result.get("doi"),
                    "url": result.get("url") or f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    "has_full_text": has_full_text,
                }
                
                if has_full_text:
                    metadata["full_text_length"] = len(full_text_data.get("full_text", ""))
                
                # Remove None values
                metadata = {k: v for k, v in metadata.items() if v is not None}
                
                documents.append(Document(page_content=page_content, metadata=metadata))
        
        return documents


class BuiltSimpleArxivRetriever(BaseRetriever):
    """Retriever for Built-Simple ArXiv API.
    
    Searches the ArXiv preprint database via Built-Simple's search API,
    returning scientific papers as LangChain Documents.
    
    Features:
        - 2.7M+ papers in physics, math, CS, and ML
        - Semantic search with similarity scores
        - Direct PDF links included in metadata
    
    Example:
        >>> retriever = BuiltSimpleArxivRetriever(limit=5)
        >>> docs = retriever.invoke("transformer neural networks")
        >>> print(docs[0].page_content)
    """
    
    base_url: str = Field(default="https://arxiv.built-simple.ai")
    limit: int = Field(default=10, description="Maximum number of results to return")
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    
    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: Optional[CallbackManagerForRetrieverRun] = None,
    ) -> List[Document]:
        """Search ArXiv and return documents.
        
        Args:
            query: Search query string
            run_manager: Callback manager (optional)
            
        Returns:
            List of Document objects with paper content and metadata
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/api/search",
                params={"q": query, "limit": self.limit},
            )
            response.raise_for_status()
            data = response.json()
        
        documents = []
        for result in data.get("results", []):
            # Build page content from title, authors, and abstract
            content_parts = []
            if result.get("title"):
                content_parts.append(f"Title: {result['title']}")
            if result.get("authors"):
                authors = result["authors"]
                if isinstance(authors, list):
                    authors = ", ".join(authors)
                content_parts.append(f"Authors: {authors}")
            if result.get("abstract"):
                content_parts.append(f"\nAbstract: {result['abstract']}")
            
            page_content = "\n".join(content_parts) if content_parts else ""
            
            # Build metadata
            arxiv_id = result.get("arxiv_id")
            metadata = {
                "source": "arxiv",
                "arxiv_id": arxiv_id,
                "title": result.get("title"),
                "authors": result.get("authors"),
                "year": result.get("year"),
                "url": f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else None,
                "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}.pdf" if arxiv_id else None,
                "similarity_score": result.get("similarity"),
            }
            # Remove None values
            metadata = {k: v for k, v in metadata.items() if v is not None}
            
            documents.append(Document(page_content=page_content, metadata=metadata))
        
        return documents


class BuiltSimpleResearchRetriever(BaseRetriever):
    """Combined retriever that searches both PubMed and ArXiv.
    
    Useful for comprehensive research queries that should span both
    peer-reviewed publications (PubMed) and preprints (ArXiv).
    
    Example:
        >>> retriever = BuiltSimpleResearchRetriever(limit_per_source=3)
        >>> docs = retriever.invoke("machine learning drug discovery")
    """
    
    pubmed_url: str = Field(default="https://pubmed.built-simple.ai")
    arxiv_url: str = Field(default="https://arxiv.built-simple.ai")
    limit_per_source: int = Field(default=5, description="Results per source")
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    include_full_text: bool = Field(default=False, description="Fetch full text for PubMed results")
    
    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: Optional[CallbackManagerForRetrieverRun] = None,
    ) -> List[Document]:
        """Search both PubMed and ArXiv, returning combined results."""
        pubmed_retriever = BuiltSimplePubMedRetriever(
            base_url=self.pubmed_url,
            limit=self.limit_per_source,
            timeout=self.timeout,
            include_full_text=self.include_full_text,
        )
        arxiv_retriever = BuiltSimpleArxivRetriever(
            base_url=self.arxiv_url,
            limit=self.limit_per_source,
            timeout=self.timeout,
        )
        
        # Fetch from both sources
        pubmed_docs = pubmed_retriever.invoke(query)
        arxiv_docs = arxiv_retriever.invoke(query)
        
        # Interleave results for variety
        combined = []
        max_len = max(len(pubmed_docs), len(arxiv_docs))
        for i in range(max_len):
            if i < len(pubmed_docs):
                combined.append(pubmed_docs[i])
            if i < len(arxiv_docs):
                combined.append(arxiv_docs[i])
        
        return combined
