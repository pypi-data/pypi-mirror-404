"""RAG chain example using Built-Simple retrievers with ChatOpenAI."""

import os

from langchain_builtsimple import BuiltSimplePubMedRetriever, BuiltSimpleResearchRetriever
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

# Requires: pip install langchain-openai
# Set OPENAI_API_KEY environment variable


def format_docs(docs):
    """Format documents for context injection."""
    formatted = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "research")
        title = doc.metadata.get("title", "Untitled")
        year = doc.metadata.get("pub_year") or doc.metadata.get("year", "N/A")
        url = doc.metadata.get("url", "")
        
        formatted.append(
            f"[{i}] {title} ({year})\n"
            f"Source: {source} | {url}\n"
            f"{doc.page_content}\n"
        )
    return "\n---\n".join(formatted)


def create_rag_chain(retriever, llm):
    """Create a RAG chain with the given retriever and LLM."""
    
    template = """You are a research assistant specializing in scientific literature.
Answer the question based on the following research papers. Be specific and cite 
the papers by their number [1], [2], etc. If the papers don't contain relevant 
information, say so.

Research Papers:
{context}

Question: {question}

Answer:"""

    prompt = ChatPromptTemplate.from_template(template)
    
    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return chain


def main():
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY not set. Using mock LLM for demo.")
        print("Set OPENAI_API_KEY to use actual ChatOpenAI.\n")
        
        # Mock LLM for demo without API key
        from langchain_core.language_models import FakeListLLM
        llm = FakeListLLM(
            responses=["Based on the research papers provided, I can see several relevant findings about the topic. The papers discuss various aspects of the research question with supporting evidence from recent studies."]
        )
    else:
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # Example 1: PubMed RAG for medical questions
    print("=" * 60)
    print("Example 1: PubMed RAG Chain")
    print("=" * 60)
    
    pubmed_retriever = BuiltSimplePubMedRetriever(limit=5)
    pubmed_chain = create_rag_chain(pubmed_retriever, llm)
    
    question = "What are the latest developments in CAR-T cell therapy for cancer?"
    print(f"\nQuestion: {question}\n")
    
    response = pubmed_chain.invoke(question)
    print(f"Answer:\n{response}")
    
    # Example 2: Combined research RAG
    print("\n" + "=" * 60)
    print("Example 2: Combined Research RAG Chain")
    print("=" * 60)
    
    research_retriever = BuiltSimpleResearchRetriever(limit_per_source=3)
    research_chain = create_rag_chain(research_retriever, llm)
    
    question = "How is machine learning being applied to protein structure prediction?"
    print(f"\nQuestion: {question}\n")
    
    response = research_chain.invoke(question)
    print(f"Answer:\n{response}")


if __name__ == "__main__":
    main()
