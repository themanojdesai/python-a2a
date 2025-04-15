#!/usr/bin/env python
"""
A DuckDuckGo search agent that provides ticker symbols for companies.
Uses MCP for tool capabilities and exposes A2A interface.
"""

import argparse
import logging
import traceback
import re
import requests
from typing import Dict, Any

from python_a2a import (
    A2AServer, Message, TextContent, FunctionCallContent,
    FunctionResponseContent, MessageRole, run_server
)
from python_a2a.mcp import FastMCP, FastMCPAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("duckduckgo_agent")

# Create MCP server for DuckDuckGo search
duckduckgo_mcp = FastMCP(
    name="DuckDuckGo MCP",
    version="1.0.0",
    description="Provides DuckDuckGo search capabilities for finding stock ticker symbols"
)

@duckduckgo_mcp.tool()
def search_ticker(company_name: str) -> str:
    """
    Search for the stock ticker symbol of a company using DuckDuckGo.
    
    Args:
        company_name: The name of the company to find the ticker for
    
    Returns:
        The ticker symbol or error message
    """
    try:
        # Format search query
        query = f"{company_name} stock ticker symbol"
        
        # Make request to DuckDuckGo API
        url = f"https://api.duckduckgo.com/?q={query}&format=json&pretty=1"
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        data = response.json()
        
        # Extract ticker from results
        abstract_text = data.get("Abstract", "")
        
        # Look for common ticker patterns (e.g., NYSE: AAPL, NASDAQ: MSFT)
        ticker_match = re.search(r'(?:NYSE|NASDAQ):\s*([A-Z]+)', abstract_text)
        if ticker_match:
            return ticker_match.group(1)
        
        # Look for simple ticker pattern (just uppercase letters)
        ticker_match = re.search(r'\(([A-Z]{1,5})\)', abstract_text)
        if ticker_match:
            return ticker_match.group(1)
        
        # If we found relevant content but couldn't extract ticker, try a simpler approach
        if abstract_text:
            # Just return first all-caps word of reasonable length
            words = abstract_text.split()
            for word in words:
                if word.isupper() and 1 < len(word) < 6 and word.isalpha():
                    return word
        
        # If no exact match, use a fallback approach
        if company_name.lower() == "apple":
            return "AAPL"
        elif company_name.lower() == "microsoft":
            return "MSFT" 
        elif company_name.lower() == "google" or company_name.lower() == "alphabet":
            return "GOOGL"
        elif company_name.lower() == "amazon":
            return "AMZN"
        elif company_name.lower() == "tesla":
            return "TSLA"
        
        return f"Could not find ticker for {company_name}"
    
    except Exception as e:
        logger.error(f"Error searching for ticker: {e}")
        logger.error(traceback.format_exc())
        return f"Error searching for ticker: {str(e)}"

class DuckDuckGoAgent(A2AServer, FastMCPAgent):
    """
    An A2A agent that uses MCP to provide stock ticker lookup capabilities.
    """
    
    def __init__(self):
        """Initialize the agent with MCP server."""
        # Initialize A2A server
        A2AServer.__init__(self)
        
        # Initialize FastMCPAgent with the MCP server
        FastMCPAgent.__init__(
            self,
            mcp_servers={"duckduckgo": duckduckgo_mcp}
        )
        
        logger.info("DuckDuckGo Agent initialized")
    
    async def handle_message_async(self, message: Message) -> Message:
        """Process incoming A2A messages asynchronously."""
        try:
            if message.content.type == "text":
                # Check if the text message contains a company name query
                logger.info(f"Received text message: {message.content.text}")
                text = message.content.text.lower()
                
                if "ticker" in text or "symbol" in text:
                    # Try to extract company name
                    company_name = None
                    for pattern in [
                        r"(?:ticker|symbol)\s+(?:for|of)\s+(.+?)(?:\?|$|\.|,)",
                        r"(.+?)(?:'s|s')\s+(?:ticker|symbol)"
                    ]:
                        match = re.search(pattern, text, re.I)
                        if match:
                            company_name = match.group(1).strip()
                            break
                    
                    if company_name:
                        # Call MCP tool
                        ticker = await self.call_mcp_tool("duckduckgo", "search_ticker", company_name=company_name)
                        return Message(
                            content=TextContent(
                                text=f"The ticker symbol for {company_name} is {ticker}."
                            ),
                            role=MessageRole.AGENT,
                            parent_message_id=message.message_id,
                            conversation_id=message.conversation_id
                        )
                
                # Default response for text messages
                return Message(
                    content=TextContent(
                        text="I'm a DuckDuckGo agent that can find stock ticker symbols for companies. "
                             "You can ask me questions like 'What's the ticker for Apple?' or "
                             "you can use the get_ticker function directly."
                    ),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )
            
            elif message.content.type == "function_call":
                function_name = message.content.name
                logger.info(f"Received function call: {function_name}")
                
                # Extract parameters
                params = {p.name: p.value for p in message.content.parameters}
                
                try:
                    # Handle function calls
                    if function_name == "get_ticker":
                        company_name = params.get("company_name", "")
                        ticker = await self.call_mcp_tool("duckduckgo", "search_ticker", company_name=company_name)
                        
                        return Message(
                            content=FunctionResponseContent(
                                name=function_name,
                                response={"ticker": ticker}
                            ),
                            role=MessageRole.AGENT,
                            parent_message_id=message.message_id,
                            conversation_id=message.conversation_id
                        )
                    else:
                        raise ValueError(f"Unknown function: {function_name}")
                    
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Error in function {function_name}: {error_msg}")
                    logger.error(traceback.format_exc())
                    
                    return Message(
                        content=FunctionResponseContent(
                            name=function_name,
                            response={"error": error_msg}
                        ),
                        role=MessageRole.AGENT,
                        parent_message_id=message.message_id,
                        conversation_id=message.conversation_id
                    )
            
            else:
                # Unsupported content type
                return Message(
                    content=TextContent(
                        text=f"I cannot process messages of type {message.content.type}."
                    ),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            logger.error(traceback.format_exc())
            
            return Message(
                content=TextContent(
                    text=f"Error processing message: {str(e)}"
                ),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
    
    def handle_message(self, message: Message) -> Message:
        """Process incoming A2A messages by delegating to the async handler."""
        import asyncio
        
        try:
            # Create a new event loop if necessary
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            return loop.run_until_complete(self.handle_message_async(message))
        except Exception as e:
            logger.error(f"Error in handle_message: {e}")
            logger.error(traceback.format_exc())
            
            return Message(
                content=TextContent(
                    text=f"Error processing your request: {str(e)}"
                ),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about this agent."""
        metadata = super().get_metadata()
        metadata.update({
            "agent_type": "DuckDuckGoAgent",
            "capabilities": ["text", "function_calling"],
            "functions": ["get_ticker"]
        })
        return metadata

def main():
    parser = argparse.ArgumentParser(description="Start a DuckDuckGo A2A agent for stock ticker lookup")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5001, help="Port to listen on")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Create the DuckDuckGo agent
    agent = DuckDuckGoAgent()
    
    print(f"Starting DuckDuckGo A2A Agent on http://{args.host}:{args.port}/a2a")
    
    # Run the server
    run_server(agent, host=args.host, port=args.port, debug=args.debug)

if __name__ == "__main__":
    main()