#!/usr/bin/env python3
"""
Playwright MCP Server Example

This example demonstrates browser automation using the Playwright MCP server.
The PlaywrightMCPServer provider automatically handles all setup including:
- Node.js and npm detection
- @playwright/mcp package installation
- Browser installation (chromium, firefox, webkit)
- Cross-platform compatibility (Windows, macOS, Linux)

Just run: python3 playwright_example.py

No manual setup required!
"""

import asyncio
from python_a2a.mcp.providers import PlaywrightMCPServer


async def simple_browser_automation():
    """Simple browser automation example."""
    print("🎭 Simple Playwright Browser Automation")
    print("=" * 60)
    
    # All complexity is handled automatically by the provider
    async with PlaywrightMCPServer() as playwright:
        
        # Navigate to a website
        print("🌐 Navigating to example.com...")
        await playwright.navigate("https://example.com")
        
        # Take a screenshot
        print("📸 Taking screenshot...")
        await playwright.take_screenshot("example_page.png")
        
        # Get page title
        print("📄 Getting page information...")
        snapshot = await playwright.get_snapshot()
        
        print("✅ Browser automation completed!")
        print(f"   Screenshot saved: example_page.png")


async def advanced_browser_automation():
    """Advanced browser automation with custom settings."""
    print("\n🎯 Advanced Playwright Browser Automation")
    print("=" * 60)
    
    # Customize browser settings
    async with PlaywrightMCPServer(
        browser="chromium",      # Use Chromium
        headless=False,          # Show browser window
        viewport_width=1400,     # Set viewport size
        viewport_height=900,
        slow_mo=1000            # Slow down for visual demo
    ) as playwright:
        
        print("🛠️ Available browser automation tools:")
        tools = await playwright.list_tools()
        for i, tool in enumerate(tools[:5], 1):
            print(f"   {i}. {tool['name']} - {tool['description']}")
        print(f"   ... and {len(tools) - 5} more tools")
        
        print(f"\n🚀 Browser automation workflow:")
        
        # Navigate to different sites
        print("1. Navigating to GitHub...")
        await playwright.navigate("https://github.com")
        await asyncio.sleep(2)  # Pause for visual demo
        
        # Take screenshot
        print("2. Taking screenshot...")
        await playwright.take_screenshot("github_page.png")
        
        # Navigate to another site
        print("3. Navigating to example.com...")
        await playwright.navigate("https://example.com")
        await asyncio.sleep(2)
        
        # Test navigation controls
        print("4. Testing navigation controls...")
        await playwright.go_back()  # Back to GitHub
        await asyncio.sleep(1)
        
        await playwright.go_forward()  # Forward to example.com
        await asyncio.sleep(1)
        
        # Resize browser
        print("5. Resizing browser window...")
        await playwright.resize_browser(1200, 800)
        await asyncio.sleep(1)
        
        print("✅ Advanced automation completed!")
        print("   Screenshots: github_page.png, example_page.png")


async def multi_browser_demo():
    """Demonstrate different browsers."""
    print("\n🌐 Multi-Browser Support Demo")
    print("=" * 60)
    
    browsers = ["chromium", "firefox", "webkit"]
    
    for browser in browsers:
        print(f"\n🔧 Testing {browser.title()} browser...")
        try:
            async with PlaywrightMCPServer(
                browser=browser,
                headless=True,  # Run headless for speed
                timeout=20.0    # Shorter timeout
            ) as playwright:
                
                await playwright.navigate("https://httpbin.org/user-agent")
                await playwright.take_screenshot(f"user_agent_{browser}.png")
                
                print(f"   ✅ {browser.title()} working! Screenshot: user_agent_{browser}.png")
                
        except Exception as e:
            print(f"   ⚠️ {browser.title()} test failed: {e}")


async def main():
    """Run all examples."""
    try:
        # Run examples in sequence
        await simple_browser_automation()
        await advanced_browser_automation()
        await multi_browser_demo()
        
        print("\n" + "=" * 60)
        print("🎉 All Playwright examples completed successfully!")
        print("\nKey Features Demonstrated:")
        print("   • 🚀 Zero-configuration setup")
        print("   • 🌐 Cross-platform compatibility")
        print("   • 📦 Automatic dependency management")
        print("   • 🎯 Multiple browser support")
        print("   • 📸 Professional screenshots")
        print("   • 🧭 Navigation controls")
        print("   • 🔧 Customizable settings")
        print("\nNext Steps:")
        print("   • Use get_snapshot() to find elements for interaction")
        print("   • Combine with AI agents for intelligent automation")
        print("   • Build custom workflows for your needs")
        
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        print("\nIf you see setup errors, the provider will guide you through installation.")


if __name__ == "__main__":
    asyncio.run(main())