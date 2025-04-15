#!/usr/bin/env python
"""
A yfinance agent that provides stock price information.
Uses MCP for tool capabilities and exposes A2A interface.
"""

import argparse
import logging
import traceback
import re
from typing import Dict, Any

from python_a2a import (
    A2AServer, Message, TextContent, FunctionCallContent,
    FunctionResponseContent, MessageRole, run_server
)
from python_a2a.mcp import FastMCP, FastMCPAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("yfinance_agent")

# Create MCP server for yfinance
yfinance_mcp = FastMCP(
    name="YFinance MCP",
    version="1.0.0",
    description="Provides yfinance stock price information"
)

@yfinance_mcp.tool()
def get_stock_price(ticker: str) -> Dict[str, Any]:
    """
    Get the current stock price for a given ticker symbol using yfinance.
    
    Args:
        ticker: The stock ticker symbol (e.g., AAPL, MSFT)
    
    Returns:
        Dict with price information or error
    """
    try:
        # Import yfinance here to avoid dependency at module level
        import yfinance as yf
        
        # Get stock info
        stock = yf.Ticker(ticker)
        
        # Get the latest price data
        price_data = stock.history(period="1d")
        
        if price_data.empty:
            return {"error": f"No price data found for ticker {ticker}"}
        
        # Extract the latest price
        latest_price = price_data['Close'].iloc[-1]
        
        # Get additional info if available
        try:
            info = stock.info
            name = info.get('shortName', info.get('longName', ticker))
            currency = info.get('currency', 'USD')
        except:
            name = ticker
            currency = 'USD'
        
        return {
            "ticker": ticker,
            "name": name,
            "price": latest_price,
            "currency": currency,
            "timestamp": price_data.index[-1].strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except ImportError:
        error_msg = "yfinance package is not installed. Install with: pip install yfinance"
        logger.error(error_msg)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Error getting stock price: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return {"error": error_msg}

class YFinanceAgent(A2AServer, FastMCPAgent):
    """
    An A2A agent that uses MCP to provide stock price information.
    """
    
    def __init__(self):
        """Initialize the agent with MCP server."""
        # Initialize A2A server
        A2AServer.__init__(self)
        
        # Initialize FastMCPAgent with the MCP server
        FastMCPAgent.__init__(
            self,
            mcp_servers={"yfinance": yfinance_mcp}
        )
        
        logger.info("YFinance Agent initialized")
    
    async def handle_message_async(self, message: Message) -> Message:
        """Process incoming A2A messages asynchronously."""
        try:
            if message.content.type == "text":
                # Check if the text message contains a ticker inquiry
                logger.info(f"Received text message: {message.content.text}")
                text = message.content.text.lower()
                
                if "price" in text or "stock" in text:
                    # Try to extract ticker
                    ticker = None
                    ticker_match = re.search(r'\b([A-Z]{1,5})\b', message.content.text)
                    if ticker_match:
                        ticker = ticker_match.group(1)
                    
                    if ticker:
                        # Call MCP tool
                        result = await self.call_mcp_tool("yfinance", "get_stock_price", ticker=ticker)
                        
                        if "error" in result:
                            return Message(
                                content=TextContent(
                                    text=f"Error: {result['error']}"
                                ),
                                role=MessageRole.AGENT,
                                parent_message_id=message.message_id,
                                conversation_id=message.conversation_id
                            )
                        
                        return Message(
                            content=TextContent(
                                text=f"{result['name']} ({result['ticker']}) is currently trading at "
                                     f"{result['price']:.2f} {result['currency']}."
                            ),
                            role=MessageRole.AGENT,
                            parent_message_id=message.message_id,
                            conversation_id=message.conversation_id
                        )
                
                # Default response for text messages
                return Message(
                    content=TextContent(
                        text="I'm a YFinance agent that can provide stock price information. "
                             "You can ask about a stock price by mentioning the ticker (e.g., 'What's the price of AAPL?') "
                             "or you can use the get_price function directly."
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
                    if function_name == "get_price":
                        ticker = params.get("ticker", "")
                        result = await self.call_mcp_tool("yfinance", "get_stock_price", ticker=ticker)
                        
                        return Message(
                            content=FunctionResponseContent(
                                name=function_name,
                                response=result
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
            "agent_type": "YFinanceAgent",
            "capabilities": ["text", "function_calling"],
            "functions": ["get_price"]
        })
        return metadata

def main():
    parser = argparse.ArgumentParser(description="Start a YFinance A2A agent for stock price information")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5002, help="Port to listen on")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Create the YFinance agent
    agent = YFinanceAgent()
    
    print(f"Starting YFinance A2A Agent on http://{args.host}:{args.port}/a2a")
    
    # Run the server
    run_server(agent, host=args.host, port=args.port, debug=args.debug)

if __name__ == "__main__":
    main()