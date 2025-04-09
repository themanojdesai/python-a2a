# examples/applications/research_assistant/main.py
"""
A research assistant application using A2A to coordinate multiple specialized agents.

This example demonstrates how A2A can be used to build complex applications
where multiple agents with different capabilities work together.
"""

import argparse
import json
from python_a2a import (
    A2AClient, Message, TextContent, MessageRole, Conversation,
    create_text_message, pretty_print_conversation
)

def research_workflow(query, llm_endpoint, search_endpoint, summarize_endpoint):
    """
    Coordinate multiple agents to answer a research query.
    
    Steps:
    1. LLM agent generates search queries based on the research question
    2. Search agent retrieves relevant information
    3. Summarization agent synthesizes the information into a coherent answer
    
    Args:
        query: The research question
        llm_endpoint: Endpoint for the general LLM agent
        search_endpoint: Endpoint for the search agent
        summarize_endpoint: Endpoint for the summarization agent
        
    Returns:
        Final conversation with the complete research answer
    """
    # Create clients for each agent
    llm_client = A2AClient(llm_endpoint)
    search_client = A2AClient(search_endpoint)
    summarize_client = A2AClient(summarize_endpoint)
    
    # Create a conversation to track the entire workflow
    conversation = Conversation()
    
    # Step 1: Add the initial query
    conversation.create_text_message(
        text=f"Research question: {query}",
        role=MessageRole.USER
    )
    
    # Step 2: Generate search queries using LLM agent
    print("Step 1: Generating search queries...")
    search_request = Message(
        content=TextContent(
            text=f"Based on this research question: '{query}', "
                 f"generate 3 specific search queries that would help find relevant information. "
                 f"Format as a numbered list."
        ),
        role=MessageRole.USER
    )
    
    search_queries_response = llm_client.send_message(search_request)
    conversation.add_message(search_queries_response)
    
    print(f"LLM generated search queries: {search_queries_response.content.text}")
    
    # Step 3: Get information using the search agent
    print("\nStep 2: Retrieving information...")
    search_message = Message(
        content=TextContent(
            text=f"Please search for information that would help answer this question: {query}\n\n"
                 f"Using these search queries:\n{search_queries_response.content.text}"
        ),
        role=MessageRole.USER
    )
    
    search_results = search_client.send_message(search_message)
    conversation.add_message(search_results)
    
    print(f"Search results retrieved with {len(search_results.content.text)} characters")
    
    # Step 4: Summarize the findings using the summarization agent
    print("\nStep 3: Synthesizing information...")
    summarize_message = Message(
        content=TextContent(
            text=f"Synthesize the following information into a comprehensive answer to the "
                 f"research question: '{query}'\n\n"
                 f"Information:\n{search_results.content.text}"
        ),
        role=MessageRole.USER
    )
    
    summary_response = summarize_client.send_message(summarize_message)
    conversation.add_message(summary_response)
    
    print(f"Synthesized answer created with {len(summary_response.content.text)} characters")
    
    # Step 5: Add final answer to the conversation
    conversation.create_text_message(
        text=f"Here is the answer to your research question:\n\n{summary_response.content.text}",
        role=MessageRole.AGENT
    )
    
    return conversation

def main():
    parser = argparse.ArgumentParser(description="A2A Research Assistant")
    parser.add_argument("query", help="Research question to answer")
    parser.add_argument("--llm-endpoint", required=True, help="Endpoint for LLM agent")
    parser.add_argument("--search-endpoint", required=True, help="Endpoint for search agent")
    parser.add_argument("--summarize-endpoint", required=True, help="Endpoint for summarization agent")
    
    args = parser.parse_args()
    
    print(f"A2A Research Assistant")
    print(f"=====================")
    print(f"Research Question: {args.query}")
    print(f"LLM Agent: {args.llm_endpoint}")
    print(f"Search Agent: {args.search_endpoint}")
    print(f"Summarize Agent: {args.summarize_endpoint}")
    print("-" * 50)
    
    # Run the research workflow
    result = research_workflow(
        args.query, 
        args.llm_endpoint, 
        args.search_endpoint, 
        args.summarize_endpoint
    )
    
    # Print the final result
    print("\nResearch Complete!")
    print("=" * 50)
    print(result.messages[-1].content.text)
    print("=" * 50)
    
    print("\nThis example demonstrates how A2A enables modular AI systems where specialized agents")
    print("collaborate to solve complex tasks. Each agent can be independently improved or")
    print("replaced without affecting the overall system architecture.")

if __name__ == "__main__":
    main()