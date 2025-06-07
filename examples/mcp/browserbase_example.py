"""
Browserbase MCP Server Example

This example demonstrates how to use the Browserbase MCP server with python-a2a.
It shows browser automation capabilities including navigation, interactions, and data extraction.

Available operations:
- Navigation: navigate(), navigate_back(), navigate_forward()
- Interaction: click_element(element, ref), type_text(element, ref, text), hover_element(element, ref)
- Form handling: press_key(), select_option(element, ref, values), drag_element()
- Data extraction: get_text(), create_snapshot(), get_element_refs()
- Waiting: wait_time(seconds)
- Monitoring: take_screenshot(), create_snapshot()
- Session management: create_context(), create_session(), etc.

Note: Interaction methods require element references from snapshots!
"""

import asyncio
import os
import base64
import json
from python_a2a.mcp.providers import BrowserbaseMCPServer


async def main():
    # Check for Browserbase credentials
    api_key = os.getenv("BROWSERBASE_API_KEY")
    project_id = os.getenv("BROWSERBASE_PROJECT_ID")
    
    if not api_key or not project_id:
        print("❌ Missing Browserbase credentials")
        print("Please set BROWSERBASE_API_KEY and BROWSERBASE_PROJECT_ID environment variables")
        print("\n📋 To get started:")
        print("1. Sign up at https://browserbase.com")
        print("2. Create a project and get your API key")
        print("3. Set the environment variables")
        return

    print("🌐 Browserbase MCP Server Example")
    print("=" * 60)
    print("This example demonstrates browser automation with MCP:")
    print("- Browser navigation and interaction")
    print("- Page data extraction and screenshots")
    print("- Session and context management\n")

    # Create Browserbase MCP server instance
    browser = BrowserbaseMCPServer(
        api_key=api_key,
        project_id=project_id
    )

    # Use context manager for resource management
    async with browser:
        print("🔌 Browserbase MCP server connected successfully!\n")

        # List all available tools
        print("🛠️  Available Browserbase MCP Tools:")
        print("-" * 40)
        try:
            tools = await browser.list_tools()
            
            if tools:
                # Group tools by category for better display
                tool_categories = {
                    "Navigation": [],
                    "Interaction": [],
                    "Data Extraction": [],
                    "Screenshots & Monitoring": [],
                    "Session Management": []
                }
                
                for tool in tools:
                    tool_name = tool.get('name', 'Unknown') if isinstance(tool, dict) else str(tool)
                    
                    if any(keyword in tool_name for keyword in ['navigate', 'url']):
                        tool_categories["Navigation"].append(tool_name)
                    elif any(keyword in tool_name for keyword in ['click', 'type', 'scroll', 'wait', 'hover', 'drag', 'press', 'select']):
                        tool_categories["Interaction"].append(tool_name)
                    elif any(keyword in tool_name for keyword in ['extract', 'text', 'title', 'source', 'get']):
                        tool_categories["Data Extraction"].append(tool_name)
                    elif any(keyword in tool_name for keyword in ['screenshot', 'console', 'monitor', 'snapshot']):
                        tool_categories["Screenshots & Monitoring"].append(tool_name)
                    elif any(keyword in tool_name for keyword in ['context', 'session']):
                        tool_categories["Session Management"].append(tool_name)
                    else:
                        tool_categories["Navigation"].append(tool_name)  # Default
                
                total_tools = 0
                for category, category_tools in tool_categories.items():
                    if category_tools:
                        print(f"\n📂 {category}:")
                        for tool in sorted(category_tools):
                            print(f"   • {tool}")
                            total_tools += 1
                
                print(f"\n📊 Total available tools: {total_tools}")
                
            else:
                print("❌ No tools found")
                
        except Exception as e:
            print(f"❌ Failed to list tools: {e}")

        # Browser automation demo
        print(f"\n🌐 Browser Automation Demo:")
        print("-" * 30)
        
        # First create a context
        print("🔧 Creating browser context...")
        context_id = None
        try:
            context_result = await browser.create_context()
            print(f"✅ Context created: {context_result}")
            
            # Extract context ID if available
            if isinstance(context_result, dict) and 'id' in context_result:
                context_id = context_result['id']
            elif isinstance(context_result, dict) and 'contextId' in context_result:
                context_id = context_result['contextId']
                
        except Exception as e:
            print(f"❌ Context creation failed: {e}")
            # Continue without context, some operations might still work
        
        # Create a session
        print("🔧 Creating browser session...")
        session_id = None
        try:
            session_result = await browser.create_session()
            print(f"✅ Session created: {session_result}")
            
            # Extract session ID if available
            if isinstance(session_result, dict) and 'id' in session_result:
                session_id = session_result['id']
            elif isinstance(session_result, dict) and 'sessionId' in session_result:
                session_id = session_result['sessionId']
            
            # Wait a moment for session to be ready
            import asyncio
            await asyncio.sleep(2)
                
        except Exception as e:
            print(f"❌ Session creation failed: {e}")
            return
        
        # Navigate to a test website
        print("🔗 Navigating to example website...")
        try:
            nav_result = await browser.navigate("https://httpbin.org/html")
            if isinstance(nav_result, str) and "Error" in nav_result:
                print(f"❌ Navigation failed: {nav_result}")
                return
            else:
                print("✅ Navigation successful")
                print(f"📍 Navigation result: {nav_result}")
            
        except Exception as e:
            print(f"❌ Navigation failed: {e}")
            return

        # Extract page information
        print(f"\n📄 Page Information Extraction:")
        print("-" * 30)
        
        try:
            # Extract text from h1 (main heading)
            h1_text = await browser.get_text("h1")
            if isinstance(h1_text, str) and "Error" in h1_text:
                print("📋 No H1 found")
            else:
                print(f"📋 H1 text: {h1_text}")
            
            # Extract text from first paragraph
            p_text = await browser.get_text("p")
            if isinstance(p_text, str) and "Error" in p_text:
                print("📝 No paragraphs found")
            else:
                print(f"📝 First paragraph: {p_text[:100]}...")
            
            # Extract page title using title element
            try:
                title = await browser.get_text("title")
                print(f"📄 Page title: {title}")
            except Exception:
                print("📄 Title not available")
            
        except Exception as e:
            print(f"❌ Data extraction failed: {e}")

        # Take screenshot
        print(f"\n📸 Screenshot Demo:")
        print("-" * 30)
        
        try:
            screenshot_data = await browser.take_screenshot()
            if isinstance(screenshot_data, str) and "Error" in screenshot_data:
                print(f"❌ Screenshot failed: {screenshot_data}")
            else:
                # Save screenshot to file
                import base64
                screenshot_filename = "browserbase_screenshot.jpg"
                try:
                    with open(screenshot_filename, "wb") as f:
                        f.write(base64.b64decode(screenshot_data))
                    print(f"✅ Screenshot saved to: {screenshot_filename}")
                except Exception as save_error:
                    print(f"✅ Screenshot captured ({len(screenshot_data)} bytes base64 data)")
                    print(f"⚠️  Could not save to file: {save_error}")
            
        except Exception as e:
            print(f"❌ Screenshot failed: {e}")

        # Create snapshot
        print(f"\n📊 Page Snapshot:")
        print("-" * 30)
        
        try:
            snapshot = await browser.create_snapshot()
            if isinstance(snapshot, str) and "Error" in snapshot:
                print(f"❌ Snapshot failed: {snapshot}")
            else:
                # Save snapshot to file
                snapshot_filename = "browserbase_snapshot.json"
                try:
                    import json
                    with open(snapshot_filename, "w") as f:
                        if isinstance(snapshot, dict):
                            json.dump(snapshot, f, indent=2)
                        else:
                            f.write(str(snapshot))
                    print(f"✅ Snapshot saved to: {snapshot_filename}")
                except Exception as save_error:
                    print(f"✅ Snapshot created: {snapshot}")
                    print(f"⚠️  Could not save to file: {save_error}")
            
        except Exception as e:
            print(f"❌ Snapshot failed: {e}")

        # Browser interaction demo
        print(f"\n🖱️ Interaction Demo:")
        print("-" * 30)
        
        print("ℹ️  Note: Browserbase interactions require element references from snapshots")
        print("   This is how the actual Browserbase MCP server works.")
        
        # First, demonstrate operations that don't need element refs
        try:
            # Test keyboard input (doesn't require element refs)
            key_result = await browser.press_key("Tab", "Press Tab key")
            if isinstance(key_result, str) and "Error" in key_result:
                print(f"❌ Key press failed: {key_result}")
            else:
                print(f"✅ Key press successful: {key_result}")
            
        except Exception as e:
            print(f"❌ Key press failed: {e}")
            
        try:
            # Test wait with time
            wait_result = await browser.wait_time(1.0)  # Wait 1 second
            if isinstance(wait_result, str) and "Error" in wait_result:
                print(f"❌ Wait failed: {wait_result}")
            else:
                print(f"✅ Wait (1 second) successful: {wait_result}")
            
        except Exception as e:
            print(f"❌ Wait failed: {e}")
        
        # Now demonstrate the full Browserbase workflow for element interactions
        print("\n📸 Getting element references for interactions...")
        try:
            # Step 1: Take a snapshot to get element references
            snapshot_for_refs = await browser.create_snapshot()
            print("✅ Snapshot taken for element references")
            
            # In a real implementation, you would parse the snapshot to extract actual refs
            # For demo purposes, we'll show what the workflow would look like
            print("\n🔍 Examining snapshot structure...")
            if isinstance(snapshot_for_refs, dict):
                print(f"   Snapshot type: {snapshot_for_refs.get('type', 'unknown')}")
                print(f"   Status: {snapshot_for_refs.get('status', 'unknown')}")
                if 'page_data' in snapshot_for_refs:
                    print(f"   Page has H1: {snapshot_for_refs['page_data'].get('h1', 'none')}")
            
            # Note: Real Browserbase snapshots contain element references in a specific format
            # that can be used with the interaction methods
            print("\n📋 Real workflow would be:")
            print("   1. Parse snapshot to find element refs")
            print("   2. Use refs like: await browser.click_element('main heading', 'ref_123')")
            print("   3. Element refs are unique identifiers from the snapshot")
            
        except Exception as e:
            print(f"❌ Snapshot for refs failed: {e}")
        
        # Demo additional keyboard interactions
        print(f"\n⌨️  Additional Keyboard Interactions:")
        print("-" * 30)
        
        keyboard_actions = [
            ("Enter", "Press Enter key"),
            ("Escape", "Press Escape key"), 
            ("ArrowDown", "Press down arrow"),
            ("Space", "Press spacebar")
        ]
        
        for key, description in keyboard_actions:
            try:
                result = await browser.press_key(key, description)
                if isinstance(result, str) and "Error" in result:
                    print(f"❌ {description} failed: {result}")
                else:
                    print(f"✅ {description} successful")
                
                # Small delay between actions
                await browser.wait_time(0.5)
                
            except Exception as e:
                print(f"❌ {description} failed: {e}")
        
        # Demo browser navigation actions
        print(f"\n🧭 Navigation Interactions:")
        print("-" * 30)
        
        try:
            # Navigate to a form page for more interaction possibilities
            form_nav = await browser.navigate("https://httpbin.org/forms/post")
            print(f"✅ Navigated to form page: {form_nav}")
            
            # Wait for page to load
            await browser.wait_time(2.0)
            print("✅ Waited for form page to load")
            
            # Try to get text from form elements
            try:
                form_text = await browser.get_text("form")
                if form_text and len(form_text) > 10:
                    print(f"✅ Form detected on page: {form_text[:50]}...")
                else:
                    print("ℹ️  Form structure detected")
            except Exception:
                print("ℹ️  Form page loaded")
            
            # Navigate back to demonstrate browser controls
            back_result = await browser.navigate_back()
            print(f"✅ Navigate back successful: {back_result}")
            
            await browser.wait_time(1.0)
            
            # Navigate forward
            forward_result = await browser.navigate_forward()
            print(f"✅ Navigate forward successful: {forward_result}")
            
        except Exception as e:
            print(f"❌ Navigation interactions failed: {e}")
        
        # Demo browser control operations
        print(f"\n🖥️  Browser Control:")
        print("-" * 30)
        
        try:
            # Resize browser window
            resize_result = await browser.resize_browser(1024, 768)
            print(f"✅ Browser resized to 1024x768: {resize_result}")
            
            await browser.wait_time(1.0)
            
            # Resize back to original
            resize_back = await browser.resize_browser(1280, 720)
            print(f"✅ Browser resized back to 1280x720: {resize_back}")
            
        except Exception as e:
            print(f"❌ Browser control failed: {e}")
        
        # Summary of interaction capabilities
        print("\n📋 Complete Browserbase Interaction Workflow:")
        print("-" * 50)
        print("✅ Direct operations (no refs needed):")
        print("   • press_key() - Keyboard input")
        print("   • wait_time() - Time-based waiting") 
        print("   • navigate() - Page navigation")
        print("   • resize_browser() - Window control")
        print("   • take_screenshot() - Visual capture")
        print("   • get_text() - Text extraction")
        
        print("\n🔗 Ref-based operations (need snapshot refs):")
        print("   • click_element(element, ref) - Click interactions")
        print("   • hover_element(element, ref) - Hover effects")
        print("   • type_text(element, ref, text) - Text input")
        print("   • select_option(element, ref, values) - Dropdown selection")
        print("   • drag_element(source, target) - Drag and drop")
        
        print("\n🎯 For ref-based operations:")
        print("   1. snapshot = await browser.create_snapshot()")
        print("   2. Parse snapshot for element references")
        print("   3. Use element refs with interaction methods")
        print("   This is the official Browserbase MCP protocol.")

        # Performance notes
        print(f"\n⚠️  Browser Automation Notes:")
        print("-" * 30)
        print("• Cloud browsers provide consistent environment")
        print("• Some operations may timeout due to network latency")
        print("• Sessions can be persisted across requests")
        print("• Context and session management ensures proper cleanup")
        print("• Advanced stealth mode requires Enterprise plan")

        # Available method categories
        print(f"\n🎯 Available Python Methods:")
        print("-" * 30)
        method_categories = {
            "🔗 Navigation": [
                "navigate()", "navigate_back()", "navigate_forward()"
            ],
            "🖱️ Interaction": [
                "click_element(element, ref)", "type_text(element, ref, text)", "hover_element(element, ref)", "drag_element()",
                "press_key()", "select_option(element, ref, values)", "wait_time(seconds)"
            ],
            "📊 Data Extraction": [
                "get_text()"
            ],
            "📸 Monitoring": [
                "take_screenshot()", "create_snapshot()"
            ],
            "🗂️ Session Management": [
                "create_context()", "delete_context()", "create_session()", 
                "close_session()", "resize_browser()", "close_browser()"
            ]
        }
        
        for category, methods in method_categories.items():
            print(f"\n{category}:")
            for method in methods:
                print(f"   • browser.{method}")

        print("\n" + "=" * 60)
        print("🎉 Browserbase MCP Integration Complete!")
        print("📚 Context manager handled connection lifecycle")
        print("🌐 Powered by Browserbase cloud browsers")
        print("🔌 MCP server automatically disconnected")


if __name__ == "__main__":
    asyncio.run(main())