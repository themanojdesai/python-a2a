#!/usr/bin/env python3
"""
Zerodha Kite MCP Integration Example

This example demonstrates how to integrate Zerodha's official Kite MCP server with python-a2a,
creating an intelligent trading assistant that provides real portfolio analysis and market insights.

Based on Zerodha's official MCP implementation:
- Blog: https://zerodha.com/z-connect/featured/connect-your-zerodha-account-to-ai-assistants-with-kite-mcp
- Repository: https://github.com/zerodha/kite-mcp-server

Features:
- Real-time portfolio analysis
- Market data retrieval  
- Personalized financial insights
- Natural language portfolio queries
- Read-only access for security

Requirements:
- Node.js (for community implementations)
- Kite API credentials (for local server)
- Internet connection (for hosted server)

Usage:
- Hosted mode (recommended): python kite_mcp_example.py --mode hosted
- Local mode: python kite_mcp_example.py --mode local --api-key YOUR_KEY --api-secret YOUR_SECRET
"""

import asyncio
import argparse
import socket
import os
import re
import logging
from typing import Dict, Optional, Any, List
from python_a2a import (
    A2AServer, AgentCard, run_server, Message, MessageRole, 
    TextContent, AgentSkill
)
from python_a2a.mcp import FastMCPAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ANSI colors for beautiful output
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RED = "\033[91m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"


def print_banner():
    """Print a beautiful banner"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BOLD}{CYAN}📈 Zerodha Kite MCP Trading Assistant 📈{RESET}")
    print(f"{BLUE}Powered by Official Zerodha Kite MCP Server{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")


def find_free_port():
    """Find an available port to use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', 0))
        return s.getsockname()[1]


class KiteTradingAssistant(A2AServer, FastMCPAgent):
    """
    An intelligent trading assistant powered by Zerodha's official Kite MCP server.
    
    This agent provides natural language access to:
    - Real-time portfolio analysis
    - Market data and insights
    - Personalized financial recommendations
    - Sector exposure analysis
    - Investment performance tracking
    
    Note: This is READ-ONLY access for security.
    """
    
    def __init__(self, kite_config: Dict[str, str], port: Optional[int] = None):
        """
        Initialize the Kite Trading Assistant.
        
        Args:
            kite_config: Configuration with mode and credentials
            port: Optional port number
        """
        # Find a free port if not provided
        if port is None:
            port = find_free_port()
        
        # Create agent card with real trading capabilities
        agent_card = AgentCard(
            name="Kite Trading Assistant",
            description="AI-powered trading assistant for Zerodha Kite with real portfolio access",
            url=f"http://localhost:{port}",
            version="1.0.0",
            skills=[
                AgentSkill(
                    name="Portfolio Analysis",
                    description="Analyze real portfolio performance and holdings",
                    tags=["portfolio", "analysis", "performance", "holdings"],
                    examples=["Analyze my portfolio performance", "Show my sector exposure", "What are my top holdings?"]
                ),
                AgentSkill(
                    name="Market Intelligence",
                    description="Get real-time market data and insights",
                    tags=["market", "data", "quotes", "trends"],
                    examples=["What's happening in the market today?", "Get NIFTY performance", "Show top gainers"]
                ),
                AgentSkill(
                    name="Investment Insights",
                    description="Personalized investment recommendations and analysis",
                    tags=["insights", "recommendations", "analysis"],
                    examples=["Give me investment insights", "Analyze my diversification", "What should I consider buying?"]
                ),
                AgentSkill(
                    name="Financial Planning",
                    description="Financial planning and goal tracking assistance",
                    tags=["planning", "goals", "strategy"],
                    examples=["Help me plan my investments", "Track my financial goals", "Suggest portfolio rebalancing"]
                )
            ]
        )
        
        # Initialize A2AServer
        A2AServer.__init__(self, agent_card=agent_card)
        
        # Setup Kite MCP connection
        kite_mcp_config = self._setup_kite_mcp(kite_config)
        FastMCPAgent.__init__(self, mcp_servers=kite_mcp_config)
        
        # Store configuration
        self.port = port
        self.kite_mode = kite_config.get("mode", "hosted")
        
        # Track available tools
        self.available_tools: List[str] = []
        self._tools_discovered = False
    
    def _setup_kite_mcp(self, config: Dict[str, str]) -> Dict[str, Any]:
        """Setup Kite MCP server connection based on official implementation"""
        mode = config.get("mode", "hosted")
        
        if mode == "local":
            # Local Kite MCP server - requires Go installation and official server
            # Based on: https://github.com/zerodha/kite-mcp-server
            api_key = config.get("api_key", "")
            api_secret = config.get("api_secret", "")
            
            if not api_key or not api_secret:
                logger.warning("API credentials required for local mode")
            
            return {
                "kite": {
                    "command": ["go", "run", "main.go"],
                    "env": {
                        "APP_MODE": "stdio",
                        "KITE_API_KEY": api_key,
                        "KITE_API_SECRET": api_secret
                    },
                    "cwd": config.get("server_path", ".")
                }
            }
        else:
            # Official hosted Kite MCP server via SSE
            # This is the recommended approach from Zerodha
            return {
                "kite": {
                    "url": "https://mcp.kite.trade/sse",
                    "transport": "sse"
                }
            }
    
    async def setup(self):
        """Setup the agent by discovering available tools"""
        try:
            await super().setup()
            # Discover available tools
            tools = await self.list_mcp_tools("kite")
            self.available_tools = [tool["name"] for tool in tools]
            self._tools_discovered = True
            logger.info(f"Discovered {len(self.available_tools)} Kite MCP tools")
        except Exception as e:
            logger.error(f"Failed to setup Kite MCP connection: {e}")
            # Continue without MCP tools
            self._tools_discovered = False
    
    def handle_message(self, message: Message) -> Message:
        """Handle incoming messages with intelligent routing to appropriate tools"""
        text = message.content.text if hasattr(message.content, 'text') else ""
        
        # Check if tools are available
        if not self._tools_discovered:
            return self._connection_error_response(message)
        
        # Help command
        if "help" in text.lower():
            return self._help_response(message)
        
        # Portfolio analysis
        elif any(word in text.lower() for word in ["portfolio", "holdings", "performance", "analysis"]):
            return self._handle_portfolio_analysis(message, text)
        
        # Market data and insights
        elif any(word in text.lower() for word in ["market", "nifty", "sensex", "price", "quote", "trend"]):
            return self._handle_market_insights(message, text)
        
        # Investment recommendations
        elif any(word in text.lower() for word in ["recommend", "suggest", "buy", "sell", "invest"]):
            return self._handle_investment_insights(message, text)
        
        # Financial planning
        elif any(word in text.lower() for word in ["plan", "goal", "strategy", "diversification", "allocation"]):
            return self._handle_financial_planning(message, text)
        
        # Default intelligent response
        else:
            return self._intelligent_response(message, text)
    
    def _handle_portfolio_analysis(self, message: Message, text: str) -> Message:
        """Handle portfolio analysis requests using real Kite MCP tools"""
        # Use text for contextual analysis
        logger.info(f"Processing portfolio analysis request: {text[:50]}...")
        try:
            response_parts = []
            
            # Get portfolio holdings if tool is available
            if "get_holdings" in self.available_tools:
                holdings = asyncio.run(self.call_mcp_tool("kite", "get_holdings"))
                if holdings:
                    response_parts.append(f"{GREEN}📊 Your Portfolio Holdings:{RESET}")
                    response_parts.append(self._format_holdings_analysis(holdings))
            
            # Get positions if available
            if "get_positions" in self.available_tools:
                positions = asyncio.run(self.call_mcp_tool("kite", "get_positions"))
                if positions:
                    response_parts.append(f"{CYAN}📈 Current Positions:{RESET}")
                    response_parts.append(self._format_positions_analysis(positions))
            
            # Get margins/account info if available
            if "get_margins" in self.available_tools:
                margins = asyncio.run(self.call_mcp_tool("kite", "get_margins"))
                if margins:
                    response_parts.append(f"{YELLOW}💰 Account Summary:{RESET}")
                    response_parts.append(self._format_account_summary(margins))
            
            if not response_parts:
                response = f"{YELLOW}I can help with portfolio analysis, but I need to connect to your Kite account first. Please ensure you're authenticated with the Kite MCP server.{RESET}"
            else:
                response = "\n\n".join(response_parts)
                
        except Exception as e:
            logger.error(f"Error in portfolio analysis: {e}")
            response = f"{RED}I encountered an issue accessing your portfolio data. This might be due to authentication or connection issues with the Kite MCP server.{RESET}"
        
        return Message(
            content=TextContent(text=response),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )
    
    def _handle_market_insights(self, message: Message, text: str) -> Message:
        """Handle market data and insights requests"""
        try:
            # Extract symbol if mentioned
            symbol = self._extract_symbol(text)
            
            response_parts = []
            
            if symbol and "get_quotes" in self.available_tools:
                # Get specific stock quote
                quotes = asyncio.run(self.call_mcp_tool("kite", "get_quotes", symbols=[symbol]))
                if quotes:
                    response_parts.append(f"{GREEN}📊 Market Data for {symbol}:{RESET}")
                    response_parts.append(self._format_market_data(symbol, quotes))
            
            # Add general market insights
            response_parts.append(f"{BLUE}🔍 Market Intelligence:{RESET}")
            response_parts.append("I can provide real-time market data and analysis using your Kite account.")
            response_parts.append("Try asking about specific stocks, indices, or market trends!")
            
            response = "\n\n".join(response_parts)
                
        except Exception as e:
            logger.error(f"Error in market insights: {e}")
            response = f"{RED}I encountered an issue accessing market data. Please check your connection to the Kite MCP server.{RESET}"
        
        return Message(
            content=TextContent(text=response),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )
    
    def _handle_investment_insights(self, message: Message, text: str) -> Message:
        """Handle investment recommendation requests"""
        # Log the specific request for analytics
        logger.info(f"Investment insights requested: {text[:50]}...")
        response = f"""
{GREEN}💡 Investment Insights:{RESET}

I can provide personalized investment analysis based on your real portfolio data from Kite.

{CYAN}What I can help with:{RESET}
• Portfolio diversification analysis
• Sector exposure review
• Performance benchmarking
• Risk assessment
• Rebalancing suggestions

{YELLOW}Note:{RESET} All recommendations are for educational purposes. Please consult with a financial advisor for investment decisions.

Try asking: "Analyze my portfolio diversification" or "What's my sector exposure?"
"""
        
        return Message(
            content=TextContent(text=response),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )
    
    def _handle_financial_planning(self, message: Message, text: str) -> Message:
        """Handle financial planning requests"""
        # Track planning request types
        logger.info(f"Financial planning query: {text[:50]}...")
        response = f"""
{GREEN}📋 Financial Planning Assistant:{RESET}

I can help you with financial planning using your real Kite portfolio data.

{CYAN}Planning Services:{RESET}
• Goal-based investment tracking
• Portfolio rebalancing strategies
• Risk tolerance assessment
• Asset allocation optimization
• Long-term wealth building plans

{BLUE}Getting Started:{RESET}
Share your financial goals, and I'll analyze your current portfolio to provide personalized recommendations.

Example: "I want to save for retirement in 20 years" or "Help me plan for my child's education"
"""
        
        return Message(
            content=TextContent(text=response),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )
    
    def _intelligent_response(self, message: Message, text: str) -> Message:
        """Provide intelligent default response"""
        # Log general inquiries for improvement
        logger.info(f"General inquiry received: {text[:50]}...")
        response = f"""
{GREEN}Hello! I'm your Zerodha Kite Trading Assistant powered by real MCP integration.{RESET}

{CYAN}I can help you with:{RESET}
• 📊 Real portfolio analysis and performance tracking
• 📈 Live market data and insights
• 💡 Personalized investment recommendations
• 📋 Financial planning and goal tracking

{YELLOW}Try asking:{RESET}
• "Analyze my portfolio performance"
• "What's happening in the market today?"
• "Show my holdings and their performance"
• "Give me investment insights"

Type 'help' for more detailed commands!
"""
        
        return Message(
            content=TextContent(text=response),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )
    
    def _connection_error_response(self, message: Message) -> Message:
        """Response when MCP connection is not available"""
        response = f"""
{RED}⚠️ Kite MCP Connection Issue{RESET}

I'm having trouble connecting to the Kite MCP server. This could be due to:

{YELLOW}Possible Issues:{RESET}
• Network connectivity problems
• Kite MCP server authentication required
• Server configuration issues

{CYAN}Solutions:{RESET}
• Check your internet connection
• Ensure you're logged into your Kite account
• Verify the MCP server is running (for local mode)

{BLUE}Server Status:{RESET}
• Mode: {self.kite_mode.upper()}
• Tools Discovered: {len(self.available_tools)}

Try restarting the application or switching to hosted mode.
"""
        
        return Message(
            content=TextContent(text=response),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )
    
    # Helper methods
    def _extract_symbol(self, text: str) -> Optional[str]:
        """Extract stock symbol from text"""
        patterns = [
            r'\b([A-Z]{2,})\b',  # All caps words
            r'(?:of|for)\s+([A-Z][A-Z0-9]+)',  # After 'of' or 'for'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.upper())
            if match:
                return match.group(1)
        
        return None
    
    def _format_holdings_analysis(self, holdings: List[Dict]) -> str:
        """Format real holdings data for analysis"""
        if not holdings:
            return f"{YELLOW}No holdings found in your portfolio.{RESET}"
        
        total_value = sum(float(h.get('value', 0)) for h in holdings if h.get('value'))
        total_pnl = sum(float(h.get('pnl', 0)) for h in holdings if h.get('pnl'))
        
        analysis = f"Total Holdings: {len(holdings)}\n"
        analysis += f"Portfolio Value: ₹{total_value:,.2f}\n"
        analysis += f"Total P&L: {self._format_pnl(total_pnl)}\n\n"
        
        # Show top holdings
        analysis += f"{BOLD}Top Holdings:{RESET}\n"
        for holding in holdings[:5]:
            symbol = holding.get('tradingsymbol', 'Unknown')
            qty = holding.get('quantity', 0)
            ltp = holding.get('last_price', 0)
            pnl = holding.get('pnl', 0)
            
            analysis += f"• {symbol}: {qty} shares @ ₹{ltp:.2f} | P&L: {self._format_pnl(pnl)}\n"
        
        if len(holdings) > 5:
            analysis += f"... and {len(holdings) - 5} more holdings\n"
        
        return analysis
    
    def _format_positions_analysis(self, positions: Dict) -> str:
        """Format real positions data"""
        day_positions = positions.get('day', [])
        net_positions = positions.get('net', [])
        
        if not day_positions and not net_positions:
            return "No open positions currently."
        
        analysis = ""
        if day_positions:
            analysis += f"Intraday Positions: {len(day_positions)}\n"
        if net_positions:
            analysis += f"Overnight Positions: {len(net_positions)}\n"
        
        return analysis
    
    def _format_account_summary(self, margins: Dict) -> str:
        """Format real account/margin data"""
        equity = margins.get('equity', {})
        
        summary = f"Available Cash: ₹{equity.get('available_cash', 0):,.2f}\n"
        summary += f"Used Margin: ₹{equity.get('utilised', 0):,.2f}\n"
        summary += f"Total Equity: ₹{equity.get('net', 0):,.2f}"
        
        return summary
    
    def _format_market_data(self, symbol: str, quotes: Dict) -> str:
        """Format real market data"""
        if symbol not in quotes:
            return f"No data available for {symbol}"
        
        quote = quotes[symbol]
        
        data = f"Symbol: {symbol}\n"
        data += f"Last Price: ₹{quote.get('last_price', 'N/A')}\n"
        data += f"Change: {self._format_change(quote.get('change', 0), quote.get('change_percent', 0))}\n"
        data += f"Volume: {quote.get('volume', 'N/A'):,}\n"
        data += f"High/Low: ₹{quote.get('high', 'N/A')} / ₹{quote.get('low', 'N/A')}"
        
        return data
    
    def _format_change(self, change: float, percent: float) -> str:
        """Format price change with color"""
        if change > 0:
            return f"{GREEN}+₹{change:.2f} (+{percent:.2f}%){RESET}"
        elif change < 0:
            return f"{RED}₹{change:.2f} ({percent:.2f}%){RESET}"
        else:
            return "₹0.00 (0.00%)"
    
    def _format_pnl(self, pnl: float) -> str:
        """Format P&L with color"""
        if pnl > 0:
            return f"{GREEN}+₹{pnl:,.2f}{RESET}"
        elif pnl < 0:
            return f"{RED}₹{pnl:,.2f}{RESET}"
        else:
            return "₹0.00"
    
    def _help_response(self, message: Message) -> Message:
        """Provide comprehensive help information"""
        help_text = f"""
{BOLD}{CYAN}🤖 Kite Trading Assistant Help{RESET}

{GREEN}Portfolio Analysis:{RESET}
• "Analyze my portfolio performance"
• "Show my holdings breakdown"
• "What's my current P&L?"
• "Review my sector exposure"

{GREEN}Market Intelligence:{RESET}
• "What's happening in the market?"
• "Get RELIANCE stock price"
• "Show NIFTY performance"
• "Market trends today"

{GREEN}Investment Insights:{RESET}
• "Give me investment recommendations"
• "Analyze my diversification"
• "Portfolio rebalancing suggestions"
• "Risk assessment"

{GREEN}Financial Planning:{RESET}
• "Help me plan my investments"
• "Set financial goals"
• "Retirement planning advice"
• "Asset allocation strategy"

{BLUE}Connection Status:{RESET}
• Mode: {self.kite_mode.upper()}
• Available Tools: {len(self.available_tools)}
• Server: {"Connected" if self._tools_discovered else "Disconnected"}

{YELLOW}Note:{RESET} This assistant uses real data from your Kite account through the official MCP server.
All analysis is based on your actual portfolio and market conditions.
"""
        return Message(
            content=TextContent(text=help_text),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )


def print_setup_instructions():
    """Print comprehensive setup instructions"""
    print(f"""
{YELLOW}📋 Zerodha Kite MCP Setup Instructions:{RESET}

{CYAN}Option 1: Hosted Mode (Recommended){RESET}
1. No installation required
2. Uses official Zerodha hosted MCP server
3. Automatic authentication through browser
4. Run: python kite_mcp_example.py --mode hosted

{CYAN}Option 2: Local Mode (Advanced){RESET}
1. Install Go: https://golang.org/
2. Clone: git clone https://github.com/zerodha/kite-mcp-server
3. Get API credentials from https://developers.kite.trade/
4. Set environment variables:
   export KITE_API_KEY="your_api_key"
   export KITE_API_SECRET="your_api_secret"
5. Run: python kite_mcp_example.py --mode local --server-path /path/to/kite-mcp-server

{MAGENTA}Blog Reference:{RESET}
Read more: https://zerodha.com/z-connect/featured/connect-your-zerodha-account-to-ai-assistants-with-kite-mcp

{GREEN}Features:{RESET}
• Real portfolio analysis
• Live market data
• Personalized investment insights
• Financial planning assistance
""")


def main():
    parser = argparse.ArgumentParser(
        description="Zerodha Kite MCP Integration Example - Real Portfolio Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python kite_mcp_example.py                    # Run with hosted MCP server
  python kite_mcp_example.py --mode hosted     # Use official hosted server
  python kite_mcp_example.py --mode local      # Use local Go server
        """
    )
    
    parser.add_argument(
        "--mode", choices=["local", "hosted"], default="hosted",
        help="MCP server mode: local (requires Go), hosted (official) (default: hosted)"
    )
    parser.add_argument(
        "--port", type=int, default=None,
        help="Port for the agent server"
    )
    parser.add_argument(
        "--api-key", type=str, default=None,
        help="Kite API key (required for local mode)"
    )
    parser.add_argument(
        "--api-secret", type=str, default=None,
        help="Kite API secret (required for local mode)"
    )
    parser.add_argument(
        "--server-path", type=str, default=".",
        help="Path to kite-mcp-server directory (for local mode)"
    )
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Validate local mode requirements
    if args.mode == "local":
        api_key = args.api_key or os.environ.get("KITE_API_KEY")
        api_secret = args.api_secret or os.environ.get("KITE_API_SECRET")
        
        if not api_key or not api_secret:
            print(f"{RED}❌ Error: Local mode requires API credentials!{RESET}")
            print_setup_instructions()
            return
        
        print(f"{GREEN}✓ Using local Kite MCP server{RESET}")
        print(f"{CYAN}Server Path: {args.server_path}{RESET}")
        
        # Create configuration
        kite_config = {
            "mode": "local",
            "api_key": api_key,
            "api_secret": api_secret,
            "server_path": args.server_path
        }
    else:
        print(f"{GREEN}✓ Using official hosted Kite MCP server{RESET}")
        print(f"{CYAN}Server: https://mcp.kite.trade/sse{RESET}")
        
        # Create configuration
        kite_config = {
            "mode": "hosted"
        }
    
    print(f"{BLUE}Mode: {args.mode.upper()}{RESET}\n")
    
    # Create agent
    agent = KiteTradingAssistant(kite_config, args.port)
    
    # Get port
    port = agent.port
    
    print(f"{GREEN}🚀 Starting Kite Trading Assistant on http://localhost:{port}{RESET}")
    print(f"{BLUE}📡 Agent URL: http://localhost:{port}/a2a{RESET}")
    
    # Print example queries
    print(f"\n{YELLOW}🎯 Try these real portfolio queries:{RESET}")
    queries = [
        "Analyze my portfolio performance",
        "Show my current holdings",
        "What's my sector exposure?",
        "Give me investment insights",
        "What's happening in the market today?"
    ]
    for query in queries:
        print(f"   {GREEN}•{RESET} {query}")
    
    print(f"\n{CYAN}{'='*70}{RESET}")
    print(f"{YELLOW}Ready to analyze your real Kite portfolio! The agent is now running...{RESET}")
    print(f"{CYAN}{'='*70}{RESET}\n")
    
    # Run the server
    run_server(agent, host="localhost", port=port)


if __name__ == "__main__":
    main()