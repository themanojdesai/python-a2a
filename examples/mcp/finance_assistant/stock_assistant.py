#!/usr/bin/env python
"""
A stock assistant agent powered by OpenAI that coordinates between 
a DuckDuckGo agent for ticker lookup and a YFinance agent for price information.
"""

import argparse
import logging
import os
import re
import traceback
from typing import Dict, Any, Optional

from python_a2a import (
    A2AClient, A2AServer, Message, TextContent, FunctionCallContent,
    FunctionResponseContent, FunctionParameter, MessageRole, run_server,
    OpenAIA2AServer
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("stock_assistant")

class StockAssistantAgent(A2AServer):
    """
    A stock assistant agent that coordinates between multiple agents.
    """
    
    def __init__(self, 
                 openai_api_key: str,
                 duckduckgo_endpoint: str,
                 yfinance_endpoint: str):
        """
        Initialize the stock assistant agent.
        
        Args:
            openai_api_key: OpenAI API key
            duckduckgo_endpoint: Endpoint for DuckDuckGo agent
            yfinance_endpoint: Endpoint for YFinance agent
        """
        super().__init__()
        
        # Initialize clients for other agents
        self.duckduckgo_client = A2AClient(duckduckgo_endpoint)
        self.yfinance_client = A2AClient(yfinance_endpoint)
        
        # Initialize OpenAI agent for natural language understanding
        self.openai_agent = OpenAIA2AServer(
            api_key=openai_api_key,
            model="gpt-3.5-turbo",  # Use an appropriate model
            system_prompt=(
                "You are a helpful assistant that helps users get stock information. "
                "You extract company names from user queries and then help coordinate "
                "finding ticker symbols and current stock prices."
            )
        )
        
        self.duckduckgo_endpoint = duckduckgo_endpoint
        self.yfinance_endpoint = yfinance_endpoint
        
        logger.info(f"Stock Assistant Agent initialized, connected to:")
        logger.info(f"  - DuckDuckGo agent at {duckduckgo_endpoint}")
        logger.info(f"  - YFinance agent at {yfinance_endpoint}")
    
    def handle_message(self, message: Message) -> Message:
        """Process incoming A2A messages."""
        try:
            if message.content.type == "text":
                # Use OpenAI to understand the query
                logger.info(f"Received text message: {message.content.text}")
                
                # Extract company name using OpenAI
                company_name = self._extract_company_name(message.content.text)
                
                if company_name:
                    logger.info(f"Extracted company name: {company_name}")
                    
                    # Step 1: Get ticker using DuckDuckGo agent
                    ticker = self._get_ticker_symbol(company_name)
                    
                    if ticker and "Could not find ticker" not in ticker and "Error" not in ticker:
                        # Step 2: Get price using YFinance agent
                        price_info = self._get_stock_price(ticker)
                        
                        # Return combined result
                        if isinstance(price_info, dict) and "price" in price_info:
                            try:
                                price = price_info.get("price")
                                if isinstance(price, (int, float)):
                                    return Message(
                                        content=TextContent(
                                            text=f"{company_name} ({ticker}) is currently trading at "
                                                f"{price:.2f} {price_info.get('currency', 'USD')}."
                                        ),
                                        role=MessageRole.AGENT,
                                        parent_message_id=message.message_id,
                                        conversation_id=message.conversation_id
                                    )
                            except Exception as e:
                                logger.error(f"Error formatting price: {e}")
                        
                        # If we get here, try to extract information directly from the string representation
                        try:
                            if isinstance(price_info, str) and '"price":' in price_info:
                                price_match = re.search(r'"price":\s*(\d+\.?\d*)', price_info)
                                if price_match:
                                    price = float(price_match.group(1))
                                    return Message(
                                        content=TextContent(
                                            text=f"{company_name} ({ticker}) is currently trading at "
                                                f"{price:.2f} USD."
                                        ),
                                        role=MessageRole.AGENT,
                                        parent_message_id=message.message_id,
                                        conversation_id=message.conversation_id
                                    )
                        except Exception as e:
                            logger.error(f"Error extracting price from string: {e}")
                        
                        # If we still can't parse it, return the information we have
                        return Message(
                            content=TextContent(
                                text=f"Found ticker {ticker} for {company_name}, but couldn't parse the price information. "
                                     f"Raw data: {price_info}"
                            ),
                            role=MessageRole.AGENT,
                            parent_message_id=message.message_id,
                            conversation_id=message.conversation_id
                        )
                    else:
                        return Message(
                            content=TextContent(
                                text=f"Couldn't find ticker symbol for {company_name}: {ticker}"
                            ),
                            role=MessageRole.AGENT,
                            parent_message_id=message.message_id,
                            conversation_id=message.conversation_id
                        )
                
                # Default response if no company was identified
                return Message(
                    content=TextContent(
                        text="I'm a Stock Assistant that can provide current stock prices. "
                             "Please ask about a specific company, like 'What's the stock price of Apple?' "
                             "or 'How much is Microsoft stock trading for?'"
                    ),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )
            
            else:
                # Only support text messages
                return Message(
                    content=TextContent(
                        text="I only understand text messages. Please ask your question in natural language."
                    ),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            logger.error(traceback.format_exc())
            
            return Message(
                content=TextContent(
                    text=f"Sorry, I encountered an error: {str(e)}"
                ),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
    
    def _extract_company_name(self, query: str) -> Optional[str]:
        """
        Extract company name from a query using OpenAI.
        
        Args:
            query: User query text
            
        Returns:
            Company name or None if not found
        """
        try:
            # Create a message to ask OpenAI to extract the company name
            message = Message(
                content=TextContent(
                    text=f"Extract the company name from this query: '{query}'. "
                         f"Return ONLY the company name, nothing else."
                ),
                role=MessageRole.USER
            )
            
            # Get response from OpenAI
            response = self.openai_agent.handle_message(message)
            
            if response.content.type == "text":
                # Clean and return the company name
                company_name = response.content.text.strip()
                
                # If it contains explanations or other text, extract just the name
                if ":" in company_name:
                    company_name = company_name.split(":", 1)[1].strip()
                
                # Remove any quotes or periods
                company_name = company_name.strip('"\'.,')
                
                return company_name if company_name else None
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting company name: {e}")
            logger.error(traceback.format_exc())
            
            # Fallback to simple pattern matching
            patterns = [
                r"(?:stock|price|ticker).+?(?:of|for)\s+([A-Za-z\s]+(?:Inc\.?|Corporation|Corp\.?|Company|Co\.?)?)",
                r"([A-Za-z\s]+(?:Inc\.?|Corporation|Corp\.?|Company|Co\.?)?)(?:'s)?\s+(?:stock|price|ticker)",
            ]
            
            for pattern in patterns:
                match = re.search(pattern, query, re.I)
                if match:
                    return match.group(1).strip()
            
            # Try basic company names
            common_companies = ["Apple", "Microsoft", "Google", "Amazon", "Tesla", "Facebook", "Meta"]
            for company in common_companies:
                if company.lower() in query.lower():
                    return company
                    
            return None
    
    def _get_ticker_symbol(self, company_name: str) -> str:
        """
        Get ticker symbol for company using DuckDuckGo agent.
        
        Args:
            company_name: Company name
            
        Returns:
            Ticker symbol or error message
        """
        try:
            # Create function call message for DuckDuckGo agent
            message = Message(
                content=FunctionCallContent(
                    name="get_ticker",
                    parameters=[
                        FunctionParameter(name="company_name", value=company_name)
                    ]
                ),
                role=MessageRole.USER
            )
            
            # Send to DuckDuckGo agent
            response = self.duckduckgo_client.send_message(message)
            
            # Process the response
            if response.content.type == "function_response":
                result = response.content.response.get("ticker")
                error = response.content.response.get("error")
                
                if result:
                    return result
                else:
                    return f"Error from DuckDuckGo agent: {error}"
            else:
                # Handle text responses
                if hasattr(response.content, "text"):
                    text = response.content.text
                    # Try to extract ticker from text
                    ticker_match = re.search(r'ticker\s+(?:symbol\s+)?(?:for\s+[\w\s]+\s+)?is\s+([A-Z]{1,5})', text, re.I)
                    if ticker_match:
                        return ticker_match.group(1)
                    else:
                        # Just return the text
                        return text
                else:
                    return f"Unexpected response from DuckDuckGo agent"
            
        except Exception as e:
            logger.error(f"Error getting ticker symbol: {e}")
            logger.error(traceback.format_exc())
            return f"Error getting ticker symbol: {str(e)}"
    
    def _get_stock_price(self, ticker: str) -> Dict[str, Any]:
        """
        Get stock price using YFinance agent.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Price information dict or error message
        """
        try:
            # Create function call message for YFinance agent
            message = Message(
                content=FunctionCallContent(
                    name="get_price",
                    parameters=[
                        FunctionParameter(name="ticker", value=ticker)
                    ]
                ),
                role=MessageRole.USER
            )
            
            # Send to YFinance agent
            response = self.yfinance_client.send_message(message)
            
            # Process the response
            if response.content.type == "function_response":
                result = response.content.response
                # Log the result and its type for debugging
                logger.info(f"Received result from YFinance: {result} {type(result)}")
                
                # If result is a string representation of a dict, try to parse it
                if isinstance(result, str) and result.startswith("{") and result.endswith("}"):
                    try:
                        import json
                        result = json.loads(result)
                    except json.JSONDecodeError:
                        # Handle the case where it's not valid JSON
                        pass
                
                if isinstance(result, dict) and "error" in result and result["error"]:
                    return {"error": result["error"]}
                elif isinstance(result, dict) and "price" in result:
                    return result
                else:
                    # Try to extract ticker and price from the result if it's a string
                    import re
                    if isinstance(result, str):
                        # Look for price pattern in JSON-like string
                        price_match = re.search(r'"price":\s*(\d+\.?\d*)', result)
                        if price_match:
                            try:
                                price = float(price_match.group(1))
                                return {
                                    "ticker": ticker,
                                    "price": price,
                                    "currency": "USD",
                                    "timestamp": "N/A"
                                }
                            except (ValueError, IndexError):
                                pass
                    
                    return {"error": f"Could not extract price information from: {result}"}
            else:
                # Handle text responses
                if hasattr(response.content, "text"):
                    # Try to extract price info from text
                    text = response.content.text
                    price_match = re.search(r'trading at (\d+\.\d+)', text)
                    if price_match:
                        try:
                            price = float(price_match.group(1))
                            return {
                                "ticker": ticker,
                                "price": price,
                                "currency": "USD",
                                "timestamp": "N/A"
                            }
                        except (ValueError, IndexError):
                            pass
                    return {"error": f"Unexpected text response: {text}"}
                else:
                    return {"error": "Unexpected response from YFinance agent"}
            
        except Exception as e:
            logger.error(f"Error getting stock price: {e}")
            logger.error(traceback.format_exc())
            return {"error": f"Error getting stock price: {str(e)}"}
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about this agent."""
        return {
            "agent_type": "StockAssistantAgent",
            "capabilities": ["text"],
            "uses_openai": True,
            "connected_agents": {
                "duckduckgo": self.duckduckgo_endpoint,
                "yfinance": self.yfinance_endpoint
            }
        }

def main():
    parser = argparse.ArgumentParser(description="Start a Stock Assistant A2A agent")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to listen on")
    parser.add_argument("--openai-api-key", default=None, 
                        help="OpenAI API key (or set OPENAI_API_KEY environment variable)")
    parser.add_argument("--duckduckgo-endpoint", default="http://localhost:5001/a2a",
                        help="DuckDuckGo agent endpoint URL")
    parser.add_argument("--yfinance-endpoint", default="http://localhost:5002/a2a",
                        help="YFinance agent endpoint URL") 
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Get OpenAI API key from args or environment
    openai_api_key = args.openai_api_key or os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        print("Error: OpenAI API key is required. Provide it with --openai-api-key or set the OPENAI_API_KEY environment variable.")
        return 1
    
    # Create the stock assistant agent
    agent = StockAssistantAgent(
        openai_api_key=openai_api_key,
        duckduckgo_endpoint=args.duckduckgo_endpoint,
        yfinance_endpoint=args.yfinance_endpoint
    )
    
    print(f"Starting Stock Assistant A2A Agent on http://{args.host}:{args.port}/a2a")
    print(f"Connected to DuckDuckGo agent at {args.duckduckgo_endpoint}")
    print(f"Connected to YFinance agent at {args.yfinance_endpoint}")
    
    # Run the server
    run_server(agent, host=args.host, port=args.port, debug=args.debug)

if __name__ == "__main__":
    main()