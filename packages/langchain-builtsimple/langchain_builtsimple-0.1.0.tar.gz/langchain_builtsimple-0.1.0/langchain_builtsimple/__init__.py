"""LangChain integration for Built-Simple research APIs.

This package provides LangChain-compatible retrievers and tools for searching
scientific literature via Built-Simple's PubMed and ArXiv APIs.

Example:
    >>> from langchain_builtsimple import BuiltSimplePubMedRetriever
    >>> retriever = BuiltSimplePubMedRetriever(limit=5)
    >>> docs = retriever.invoke("CRISPR gene editing")
"""

from langchain_builtsimple.retrievers import (
    BuiltSimpleArxivRetriever,
    BuiltSimplePubMedRetriever,
    BuiltSimpleResearchRetriever,
)
from langchain_builtsimple.tools import (
    BuiltSimpleArxivTool,
    BuiltSimplePubMedTool,
    BuiltSimpleResearchTool,
)

__version__ = "0.1.0"

__all__ = [
    # Retrievers
    "BuiltSimplePubMedRetriever",
    "BuiltSimpleArxivRetriever",
    "BuiltSimpleResearchRetriever",
    # Tools
    "BuiltSimplePubMedTool",
    "BuiltSimpleArxivTool",
    "BuiltSimpleResearchTool",
]
