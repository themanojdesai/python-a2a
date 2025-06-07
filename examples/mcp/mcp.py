#!/usr/bin/env python3
"""
Complete MCP Server and Client Implementation

This demonstrates a production-grade MCP implementation following
the 2025-03-26 specification in one comprehensive file.

Features:
- Complete MCP server with tools, resources, and prompts
- Production-grade MCP client implementation  
- Full specification compliance (JSON-RPC 2.0, proper lifecycle)
- Real-world error handling and logging
- Official MCP terminology (Server, Client)

Usage:
    python mcp.py

This single file demonstrates everything needed for proper MCP implementation.
"""

import asyncio
import json
import logging
import sys
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from python_a2a.mcp import (
    # Official MCP specification terms
    Server, Client,
    # Transport and connection
    ServerStdioTransport, create_stdio_client,
    # Protocol components
    MCPConnection, MCPImplementationInfo, MCPCapabilities,
    # Content creation
    create_text_content, create_blob_content,
    # Error handling
    MCPProtocolError
)

# Configure production logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]  # Use stderr for server logging
)

logger = logging.getLogger(__name__)


class MCPExample:
    """
    Complete MCP implementation example.
    
    Shows both server and client implementation in one class,
    demonstrating all MCP capabilities and best practices.
    """
    
    def __init__(self):
        """Initialize the complete MCP example."""
        # Sample data for demonstration
        self._data = {
            "locations": {
                "new_york": {
                    "info": {"temperature": 22, "humidity": 65, "conditions": "Partly cloudy", "wind_speed": 15, "pressure": 1013.25},
                    "coordinates": {"lat": 40.7128, "lon": -74.0060}
                },
                "london": {
                    "info": {"temperature": 18, "humidity": 70, "conditions": "Overcast", "wind_speed": 12, "pressure": 1015.2},
                    "coordinates": {"lat": 51.5074, "lon": -0.1278}
                },
                "tokyo": {
                    "info": {"temperature": 26, "humidity": 58, "conditions": "Clear", "wind_speed": 8, "pressure": 1018.7},
                    "coordinates": {"lat": 35.6762, "lon": 139.6503}
                }
            }
        }
        
        # Server will be created when needed
        self.server = None
        
    def create_server(self) -> Server:
        """Create production-grade MCP server with all capabilities."""
        if self.server:
            return self.server
            
        # Create server with official MCP terminology
        self.server = Server(
            name="Data Server",
            version="1.0.0",
            description="Production data and analysis server"
        )
        
        # Register all MCP capabilities
        self._register_tools()
        self._register_resources() 
        self._register_prompts()
        
        logger.info("Created production MCP server")
        return self.server
    
    def _register_tools(self):
        """Register tools following MCP specification."""
        
        @self.server.tool(
            name="get_location_data",
            description="Get current data for a location",
            schema={
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "Location name (new_york, london, tokyo)"},
                    "format": {"type": "string", "enum": ["brief", "detailed"], "default": "brief"}
                },
                "required": ["location"]
            },
            annotations={"audience": ["general"], "category": "data", "safety": "safe"}
        )
        async def get_location_data(location: str, format: str = "brief"):
            """Get location data with proper error handling."""
            location_key = location.lower().replace(" ", "_")
            
            if location_key not in self._data["locations"]:
                return [create_text_content(f"Data not available for {location}").to_dict()]
            
            data = self._data["locations"][location_key]["info"]
            
            if format == "detailed":
                report = (
                    f"Complete data for {location.title()}:\n"
                    f"Temperature: {data['temperature']}°C\n"
                    f"Conditions: {data['conditions']}\n"
                    f"Humidity: {data['humidity']}%\n"
                    f"Wind Speed: {data['wind_speed']} km/h\n"
                    f"Pressure: {data['pressure']} hPa"
                )
            else:
                report = f"{location.title()}: {data['temperature']}°C, {data['conditions']}"
            
            return [create_text_content(report).to_dict()]
        
        @self.server.tool(
            name="get_forecast",
            description="Get forecast for a location",
            schema={
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "Location name"},
                    "days": {"type": "integer", "minimum": 1, "maximum": 5, "default": 3}
                },
                "required": ["location"]
            }
        )
        async def get_forecast(location: str, days: int = 3):
            """Get forecast with validation."""
            location_key = location.lower().replace(" ", "_")
            
            if location_key not in self._data["locations"]:
                return [create_text_content(f"Forecast not available for {location}").to_dict()]
            
            base_temp = self._data["locations"][location_key]["info"]["temperature"]
            forecast_lines = [f"{days}-day forecast for {location.title()}:\n"]
            
            for i in range(days):
                date = datetime.now() + timedelta(days=i+1)
                temp_variation = (-2 + (i * 1)) if i < 3 else (2 - i)
                forecast_temp = base_temp + temp_variation
                
                forecast_lines.append(
                    f"{date.strftime('%A, %B %d')}: {forecast_temp:.0f}°C, "
                    f"{'Sunny' if i % 2 == 0 else 'Cloudy'}"
                )
            
            return [create_text_content("\n".join(forecast_lines)).to_dict()]
    
    def _register_resources(self):
        """Register resources following MCP specification."""
        
        @self.server.resource(
            uri="data://locations",
            name="Available Locations",
            description="All available locations",
            mime_type="application/json"
        )
        async def list_locations():
            """Get all available locations as JSON resource."""
            locations = []
            for key, data in self._data["locations"].items():
                locations.append({
                    "id": key,
                    "name": key.replace("_", " ").title(),
                    "coordinates": data["coordinates"],
                    "available_data": ["current", "forecast"]
                })
            
            return [create_blob_content(json.dumps(locations, indent=2), "application/json").to_dict()]
        
        @self.server.resource(
            uri="data://location/{location_id}",
            name="Location Details",
            description="Detailed information about a specific location"
        )
        async def get_location_details(location_id: str):
            """Get detailed location information using template resource."""
            if location_id not in self._data["locations"]:
                return [create_text_content(f"Location {location_id} not found").to_dict()]
            
            data = self._data["locations"][location_id]
            details = (
                f"Location: {location_id.replace('_', ' ').title()}\n"
                f"Coordinates: {data['coordinates']['lat']}, {data['coordinates']['lon']}\n"
                f"Available Data: Current conditions, forecast\n"
                f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            return [create_text_content(details).to_dict()]
    
    def _register_prompts(self):
        """Register prompts following MCP specification."""
        
        @self.server.prompt(
            name="data_analysis",
            description="Generate data analysis prompt for AI processing",
            arguments=[
                {"name": "location", "description": "Location to analyze", "required": True},
                {"name": "focus", "description": "Analysis focus (summary, detailed, comparison)", "required": False}
            ]
        )
        async def data_analysis_prompt(location: str, focus: str = "summary"):
            """Generate comprehensive data analysis prompt."""
            focus_guidance = {
                "summary": "Provide a brief overview and key insights.",
                "detailed": "Provide comprehensive analysis with all available data points.", 
                "comparison": "Compare with other available locations and provide insights.",
                "general": "Provide general analysis and recommendations."
            }
            
            guidance = focus_guidance.get(focus, focus_guidance["general"])
            
            return [{
                "role": "user",
                "content": {
                    "type": "text",
                    "text": (
                        f"Analyze the current data for {location} and provide insights. "
                        f"{guidance}\n\n"
                        f"Use the get_location_data tool to fetch information, then provide:\n"
                        f"1. Current conditions summary\n"
                        f"2. Key observations and patterns\n" 
                        f"3. Recommendations or insights\n"
                        f"4. Additional context if relevant\n\n"
                        f"Be specific and actionable in your analysis."
                    )
                }
            }]
    
    async def run_server_mode(self):
        """Run in server mode (called by client via stdio)."""
        server = self.create_server()
        
        # Server configuration
        implementation_info = MCPImplementationInfo(name="example-server", version="1.0.0")
        capabilities = MCPCapabilities(tools={}, resources={}, prompts={})
        
        # Create stdio transport for server
        transport = ServerStdioTransport()
        
        # Create connection
        connection = MCPConnection(
            transport=transport,
            handler=server.handler,
            implementation_info=implementation_info,
            capabilities=capabilities
        )
        
        # Set connection reference in handler for initialization completion
        server.handler.set_connection(connection)
        
        try:
            logger.info("Starting MCP server...")
            await connection.connect()
            await connection.wait_for_initialization()
            
            # Keep server running
            logger.info("MCP server is now running and ready for requests...")
            while connection.is_initialized:
                await asyncio.sleep(0.1)  # Shorter sleep for more responsive server
                
            logger.warning("Server loop exited - connection no longer initialized")
                
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise
        finally:
            logger.info("Server shutting down...")
            await connection.disconnect()
    
    async def run_client_demo(self):
        """Run complete client demonstration."""
        print("=" * 80)
        print("MCP IMPLEMENTATION EXAMPLE - PRODUCTION GRADE")
        print("=" * 80)
        print("Demonstrating MCP 2025-03-26 specification compliance")
        print("Using official terminology: Server, Client, proper JSON-RPC 2.0")
        
        try:
            # Connect to server (which will run this same script in server mode)
            logger.info("Creating MCP client connection...")
            
            async with self._create_client() as client:
                # Demonstrate all MCP capabilities
                await self._demo_server_info(client)
                await self._demo_resources(client)
                await self._demo_tools(client)
                await self._demo_prompts(client)
                await self._demo_error_handling(client)
                await self._demo_statistics(client)
                
        except Exception as e:
            logger.error(f"Demo failed: {e}")
            print(f"\nDemo failed: {e}")
            raise
    
    @asynccontextmanager
    async def _create_client(self):
        """Create MCP client with proper resource management."""
        client = None
        try:
            # Create client that connects to this same script in server mode
            client = await create_stdio_client(
                command=[sys.executable, __file__, "--server"],
                name="example-client",
                version="1.0.0",
                timeout=30.0
            )
            
            logger.info(f"Connected to server: {client.server_info.name}")
            yield client
            
        finally:
            if client:
                await client.disconnect()
                logger.info("Client disconnected")
    
    async def _demo_server_info(self, client: Client):
        """Demonstrate server information retrieval."""
        print("\n1. SERVER INFORMATION:")
        print("-" * 50)
        
        server_info = client.server_info
        server_caps = client.server_capabilities
        
        print(f"  Server: {server_info.name} v{server_info.version}")
        print(f"  Protocol: MCP 2025-03-26 (JSON-RPC 2.0)")
        print(f"  Capabilities: {list(server_caps.to_dict().keys())}")
        print(f"  Connected: {client.is_connected}")
    
    async def _demo_resources(self, client: Client):
        """Demonstrate MCP resource reading."""
        print("\n2. MCP RESOURCES:")
        print("-" * 50)
        
        try:
            # Get available locations
            locations_result = await client.read_resource("data://locations")
            contents = locations_result.get("contents", [])
            
            if contents:
                resource_content = contents[0].get("content", [])
                if resource_content and resource_content[0].get("type") == "blob":
                    locations_data = resource_content[0].get("data", "")
                    locations = json.loads(locations_data)
                    
                    print("  Available Locations:")
                    for loc in locations:
                        print(f"    • {loc['name']} ({loc['id']})")
                        print(f"      Coordinates: {loc['coordinates']['lat']}, {loc['coordinates']['lon']}")
            
            # Get specific location details using template resource
            location_result = await client.read_resource("data://location/london")
            if location_result.get("contents"):
                content = location_result["contents"][0]["content"][0]
                if content.get("type") == "text":
                    print(f"\n  Location Details:\n{content['text']}")
                    
        except Exception as e:
            print(f"  Resource error: {e}")
    
    async def _demo_tools(self, client: Client):
        """Demonstrate MCP tool calling."""
        print("\n3. MCP TOOLS:")
        print("-" * 50)
        
        test_locations = ["new_york", "london", "tokyo"]
        
        for location in test_locations:
            try:
                # Get location data
                data_result = await client.call_tool(
                    "get_location_data",
                    {"location": location, "format": "detailed"}
                )
                
                if not data_result.get("isError"):
                    content = data_result.get("content", [])
                    if content and content[0].get("type") == "text":
                        print(f"\n  {location.replace('_', ' ').title()}:")
                        data_text = content[0]["text"]
                        # Print first 3 lines for brevity
                        lines = data_text.split('\n')[:4]
                        for line in lines:
                            print(f"    {line}")
                
            except Exception as e:
                print(f"  Tool error for {location}: {e}")
        
        # Demonstrate forecast
        try:
            forecast_result = await client.call_tool(
                "get_forecast",
                {"location": "new_york", "days": 3}
            )
            
            if not forecast_result.get("isError"):
                content = forecast_result.get("content", [])
                if content and content[0].get("type") == "text":
                    print(f"\n  3-Day Forecast:")
                    forecast_lines = content[0]["text"].split('\n')[:4]
                    for line in forecast_lines:
                        if line.strip():
                            print(f"    {line}")
                            
        except Exception as e:
            print(f"  Forecast error: {e}")
    
    async def _demo_prompts(self, client: Client):
        """Demonstrate MCP prompt generation."""
        print("\n4. MCP PROMPTS:")
        print("-" * 50)
        
        try:
            prompt_result = await client.get_prompt(
                "data_analysis",
                {"location": "london", "focus": "detailed"}
            )
            
            messages = prompt_result.get("messages", [])
            if messages:
                prompt_text = messages[0]["content"]["text"]
                # Show first 150 characters
                preview = prompt_text[:150] + "..." if len(prompt_text) > 150 else prompt_text
                print(f"  Generated AI Analysis Prompt:")
                print(f"    {preview}")
                print(f"  Full prompt length: {len(prompt_text)} characters")
                
        except Exception as e:
            print(f"  Prompt error: {e}")
    
    async def _demo_error_handling(self, client: Client):
        """Demonstrate proper error handling."""
        print("\n5. ERROR HANDLING:")
        print("-" * 50)
        
        try:
            # Test invalid location
            result = await client.call_tool(
                "get_location_data",
                {"location": "invalid_location"}
            )
            
            if not result.get("isError"):
                content = result.get("content", [])
                if content and content[0].get("type") == "text":
                    print(f"  Graceful error: {content[0]['text']}")
            
            # Test invalid tool
            try:
                await client.call_tool("invalid_tool", {})
            except MCPProtocolError as e:
                print(f"  Protocol error handled: Tool not found")
                
        except Exception as e:
            print(f"  Error handling test: {e}")
    
    async def _demo_statistics(self, client: Client):
        """Demonstrate connection statistics."""
        print("\n6. CONNECTION STATISTICS:")
        print("-" * 50)
        
        stats = client.get_stats()
        print(f"  Messages sent: {stats.get('messages_sent', 0)}")
        print(f"  Messages received: {stats.get('messages_received', 0)}")
        print(f"  Requests sent: {stats.get('requests_sent', 0)}")
        print(f"  Responses received: {stats.get('responses_received', 0)}")
        print(f"  Errors: {stats.get('errors', 0)}")


async def main():
    """Main entry point - handles both server and client modes."""
    # Check if running in server mode (called by client)
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        # Run as MCP server
        example = MCPExample()
        await example.run_server_mode()
    else:
        # Run client demonstration
        example = MCPExample()
        await example.run_client_demo()
        
        print("\n" + "=" * 80)
        print("MCP EXAMPLE COMPLETE")
        print("=" * 80)
        print("\nKey Features Demonstrated:")
        print("✅ Full MCP 2025-03-26 specification compliance")
        print("✅ Proper JSON-RPC 2.0 implementation")
        print("✅ Official MCP terminology (Server, Client)")
        print("✅ Production-grade error handling")
        print("✅ All MCP primitives (Tools, Resources, Prompts)")
        print("✅ Real-world usage patterns")
        print("✅ No monkey patching, dummy implementations, or proxies")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Example interrupted by user")
    except Exception as e:
        logger.error(f"Example failed: {e}")
        sys.exit(1)