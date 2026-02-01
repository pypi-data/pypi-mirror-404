"""Agent example using Built-Simple research tools."""

import os

from langchain_builtsimple import BuiltSimpleArxivTool, BuiltSimplePubMedTool, BuiltSimpleResearchTool

# Requires: pip install langchain langchain-openai
# Set OPENAI_API_KEY environment variable


def demo_tools_directly():
    """Demonstrate using tools directly without an agent."""
    print("=" * 60)
    print("Direct Tool Usage (No Agent)")
    print("=" * 60)
    
    # PubMed tool
    pubmed_tool = BuiltSimplePubMedTool()
    print(f"\nTool: {pubmed_tool.name}")
    print(f"Description: {pubmed_tool.description}\n")
    
    result = pubmed_tool.invoke({"query": "mRNA vaccines", "limit": 2})
    print(result)
    
    # ArXiv tool
    print("\n" + "-" * 40)
    arxiv_tool = BuiltSimpleArxivTool()
    print(f"\nTool: {arxiv_tool.name}")
    print(f"Description: {arxiv_tool.description}\n")
    
    result = arxiv_tool.invoke({"query": "large language models reasoning", "limit": 2})
    print(result)


def demo_agent():
    """Demonstrate using tools with a LangChain agent."""
    if not os.getenv("OPENAI_API_KEY"):
        print("\n" + "=" * 60)
        print("Agent Demo (Skipped - OPENAI_API_KEY not set)")
        print("=" * 60)
        print("Set OPENAI_API_KEY to run the agent demo.")
        return
    
    from langchain.agents import AgentExecutor, create_tool_calling_agent
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI
    
    print("\n" + "=" * 60)
    print("Agent with Research Tools")
    print("=" * 60)
    
    # Initialize LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # Create tools
    tools = [
        BuiltSimplePubMedTool(),
        BuiltSimpleArxivTool(),
    ]
    
    # Create agent prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a research assistant with access to scientific literature databases.

You have two search tools:
- pubmed_search: For biomedical and life sciences (peer-reviewed papers)
- arxiv_search: For physics, math, CS, ML/AI (preprints)

Choose the appropriate tool based on the research topic. For medical/biological 
topics, use PubMed. For AI/ML/physics/math topics, use ArXiv. For interdisciplinary 
topics, you may need to search both.

Always cite your sources with titles and URLs when answering questions."""),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])
    
    # Create and run agent
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    # Example queries
    queries = [
        "What are the latest papers on using transformers for medical image analysis?",
        "Find recent research on CRISPR delivery mechanisms",
    ]
    
    for query in queries:
        print(f"\n{'=' * 40}")
        print(f"Query: {query}")
        print("=" * 40)
        
        response = agent_executor.invoke({"input": query})
        print(f"\nFinal Answer:\n{response['output']}")


def demo_research_agent():
    """Demo with the combined research tool."""
    if not os.getenv("OPENAI_API_KEY"):
        return
    
    from langchain.agents import AgentExecutor, create_tool_calling_agent
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI
    
    print("\n" + "=" * 60)
    print("Agent with Combined Research Tool")
    print("=" * 60)
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # Use the combined tool for comprehensive searches
    tools = [BuiltSimpleResearchTool()]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a research assistant. You have access to a research_search 
tool that searches both PubMed (biomedical) and ArXiv (physics/CS/ML) simultaneously.

Use this tool to find relevant papers and synthesize the information to answer 
research questions. Always cite your sources."""),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])
    
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    query = "What's the state of AI-driven drug discovery? Cover both the ML methods and clinical applications."
    print(f"\nQuery: {query}\n")
    
    response = agent_executor.invoke({"input": query})
    print(f"\nFinal Answer:\n{response['output']}")


def main():
    # Demo 1: Direct tool usage (always works)
    demo_tools_directly()
    
    # Demo 2: Agent with tools (requires OpenAI API key)
    demo_agent()
    
    # Demo 3: Combined research agent
    demo_research_agent()


if __name__ == "__main__":
    main()
