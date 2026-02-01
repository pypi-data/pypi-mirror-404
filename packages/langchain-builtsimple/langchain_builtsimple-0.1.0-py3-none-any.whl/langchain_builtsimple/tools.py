"""LangChain tools for Built-Simple research APIs.

These tools can be used with LangChain agents to search scientific literature.
"""

from typing import Optional, Type

import httpx
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class PubMedSearchInput(BaseModel):
    """Input schema for PubMed search tool."""
    
    query: str = Field(description="Search query for PubMed database")
    limit: int = Field(default=5, description="Maximum number of results (1-20)")


class ArxivSearchInput(BaseModel):
    """Input schema for ArXiv search tool."""
    
    query: str = Field(description="Search query for ArXiv preprints")
    limit: int = Field(default=5, description="Maximum number of results (1-20)")


class BuiltSimplePubMedTool(BaseTool):
    """Tool for searching PubMed via Built-Simple API.
    
    Use this tool to search for peer-reviewed biomedical and life sciences
    literature from PubMed. Returns titles, abstracts, and publication details.
    
    Example:
        >>> tool = BuiltSimplePubMedTool()
        >>> result = tool.invoke({"query": "COVID-19 vaccines", "limit": 3})
    """
    
    name: str = "pubmed_search"
    description: str = (
        "Search PubMed for peer-reviewed biomedical and life sciences literature. "
        "Use for medical, biological, pharmaceutical, and healthcare research. "
        "Returns paper titles, abstracts, journals, and publication years. "
        "Input should be a search query describing the topic of interest."
    )
    args_schema: Type[BaseModel] = PubMedSearchInput
    
    base_url: str = "https://pubmed.built-simple.ai"
    timeout: float = 30.0
    
    def _run(
        self,
        query: str,
        limit: int = 5,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute PubMed search and return formatted results."""
        limit = max(1, min(limit, 20))  # Clamp between 1-20
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/hybrid-search",
                    json={"query": query, "limit": limit},
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as e:
            return f"Error searching PubMed: {str(e)}"
        
        results = data.get("results", [])
        if not results:
            return f"No PubMed results found for: {query}"
        
        # Format results for agent consumption
        output_parts = [f"Found {len(results)} PubMed results for '{query}':\n"]
        
        for i, result in enumerate(results, 1):
            parts = [f"\n--- Result {i} ---"]
            if result.get("title"):
                parts.append(f"Title: {result['title']}")
            if result.get("journal"):
                parts.append(f"Journal: {result['journal']}")
            if result.get("pub_year"):
                parts.append(f"Year: {result['pub_year']}")
            if result.get("pmid"):
                parts.append(f"PMID: {result['pmid']}")
                parts.append(f"URL: https://pubmed.ncbi.nlm.nih.gov/{result['pmid']}/")
            if result.get("abstract"):
                abstract = result["abstract"]
                if len(abstract) > 500:
                    abstract = abstract[:500] + "..."
                parts.append(f"Abstract: {abstract}")
            
            output_parts.append("\n".join(parts))
        
        return "\n".join(output_parts)


class BuiltSimpleArxivTool(BaseTool):
    """Tool for searching ArXiv via Built-Simple API.
    
    Use this tool to search for preprints in physics, mathematics, computer
    science, and related fields from ArXiv.
    
    Example:
        >>> tool = BuiltSimpleArxivTool()
        >>> result = tool.invoke({"query": "large language models", "limit": 3})
    """
    
    name: str = "arxiv_search"
    description: str = (
        "Search ArXiv for preprints in physics, mathematics, computer science, "
        "statistics, electrical engineering, and quantitative biology. "
        "Use for cutting-edge research, AI/ML papers, and theoretical work. "
        "Returns paper titles, authors, abstracts, and ArXiv IDs. "
        "Input should be a search query describing the topic of interest."
    )
    args_schema: Type[BaseModel] = ArxivSearchInput
    
    base_url: str = "https://arxiv.built-simple.ai"
    timeout: float = 30.0
    
    def _run(
        self,
        query: str,
        limit: int = 5,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Execute ArXiv search and return formatted results."""
        limit = max(1, min(limit, 20))  # Clamp between 1-20
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    f"{self.base_url}/api/search",
                    params={"q": query, "limit": limit},
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as e:
            return f"Error searching ArXiv: {str(e)}"
        
        results = data.get("results", [])
        if not results:
            return f"No ArXiv results found for: {query}"
        
        # Format results for agent consumption
        output_parts = [f"Found {len(results)} ArXiv results for '{query}':\n"]
        
        for i, result in enumerate(results, 1):
            parts = [f"\n--- Result {i} ---"]
            if result.get("title"):
                parts.append(f"Title: {result['title']}")
            if result.get("authors"):
                authors = result["authors"]
                if isinstance(authors, list):
                    authors = ", ".join(authors[:5])
                    if len(result["authors"]) > 5:
                        authors += f" (+{len(result['authors']) - 5} more)"
                parts.append(f"Authors: {authors}")
            if result.get("year"):
                parts.append(f"Year: {result['year']}")
            if result.get("arxiv_id"):
                parts.append(f"ArXiv ID: {result['arxiv_id']}")
                parts.append(f"URL: https://arxiv.org/abs/{result['arxiv_id']}")
            if result.get("abstract"):
                abstract = result["abstract"]
                if len(abstract) > 500:
                    abstract = abstract[:500] + "..."
                parts.append(f"Abstract: {abstract}")
            
            output_parts.append("\n".join(parts))
        
        return "\n".join(output_parts)


class BuiltSimpleResearchTool(BaseTool):
    """Combined tool that searches both PubMed and ArXiv.
    
    Use this for comprehensive research queries that should cover both
    peer-reviewed publications and preprints.
    """
    
    name: str = "research_search"
    description: str = (
        "Search both PubMed and ArXiv simultaneously for comprehensive research coverage. "
        "Use when you need both peer-reviewed papers (PubMed) and preprints (ArXiv). "
        "Good for interdisciplinary topics like AI in healthcare, computational biology, etc."
    )
    args_schema: Type[BaseModel] = PubMedSearchInput  # Same schema works
    
    pubmed_url: str = "https://pubmed.built-simple.ai"
    arxiv_url: str = "https://arxiv.built-simple.ai"
    timeout: float = 30.0
    
    def _run(
        self,
        query: str,
        limit: int = 5,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Search both PubMed and ArXiv."""
        pubmed_tool = BuiltSimplePubMedTool(
            base_url=self.pubmed_url,
            timeout=self.timeout,
        )
        arxiv_tool = BuiltSimpleArxivTool(
            base_url=self.arxiv_url,
            timeout=self.timeout,
        )
        
        pubmed_results = pubmed_tool._run(query, limit=limit)
        arxiv_results = arxiv_tool._run(query, limit=limit)
        
        return f"=== PubMed Results ===\n{pubmed_results}\n\n=== ArXiv Results ===\n{arxiv_results}"
