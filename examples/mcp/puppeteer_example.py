"""
Puppeteer MCP Server Example

This example demonstrates how to use the Puppeteer MCP server with python-a2a.
It shows browser automation capabilities including navigation, interactions, and data extraction.

Available operations:
- Navigation: puppeteer_navigate() 
- Interaction: puppeteer_click(), puppeteer_fill(), puppeteer_select(), puppeteer_hover()
- Data extraction: puppeteer_evaluate() - Execute JavaScript to extract data
- Monitoring: puppeteer_screenshot() - Take screenshots
- Waiting and scrolling capabilities

Note: All operations work with CSS selectors and JavaScript execution!
"""

import asyncio
import os
import base64
import json
from datetime import datetime
from pathlib import Path
from python_a2a.mcp.providers import PuppeteerMCPServer


async def main():
    print("🌐 Puppeteer MCP Server Example")
    print("=" * 60)
    print("This example demonstrates browser automation with MCP:")
    print("- Browser navigation and interaction with CSS selectors")
    print("- JavaScript execution and data extraction")
    print("- Screenshots and page manipulation\n")

    # Create Puppeteer MCP server instance
    puppeteer = PuppeteerMCPServer(
        headless=False,  # Show browser for demo
        viewport_width=1400,
        viewport_height=900
    )

    # Use context manager for resource management
    async with puppeteer:
        print("🔌 Puppeteer MCP server connected successfully!\n")

        # List all available tools
        print("🛠️  Available Puppeteer MCP Tools:")
        print("-" * 40)
        try:
            tools = await puppeteer.list_tools()
            
            if tools:
                # Group tools by category for better display
                tool_categories = {
                    "Navigation": [],
                    "Interaction": [],
                    "Data Extraction": [],
                    "Monitoring": []
                }
                
                for tool in tools:
                    tool_name = tool.get('name', 'Unknown') if isinstance(tool, dict) else str(tool)
                    
                    if 'navigate' in tool_name:
                        tool_categories["Navigation"].append(tool_name)
                    elif any(keyword in tool_name for keyword in ['click', 'fill', 'select', 'hover']):
                        tool_categories["Interaction"].append(tool_name)
                    elif 'evaluate' in tool_name:
                        tool_categories["Data Extraction"].append(tool_name)
                    elif 'screenshot' in tool_name:
                        tool_categories["Monitoring"].append(tool_name)
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
        
        # Navigate to a test website
        print("🔗 Navigating to example website...")
        try:
            nav_result = await puppeteer._call_tool("puppeteer_navigate", {
                "url": "https://httpbin.org/html"
            })
            print("✅ Navigation successful")
            print(f"📍 Navigation result: {nav_result}")
            
            # Wait for page to load
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"❌ Navigation failed: {e}")
            return

        # Extract page information using JavaScript
        print(f"\n📄 Page Information Extraction:")
        print("-" * 30)
        
        try:
            # Extract page title
            title = await puppeteer._call_tool("puppeteer_evaluate", {
                "script": "document.title"
            })
            print(f"📄 Page title: {title}")
            
            # Extract H1 text
            h1_text = await puppeteer._call_tool("puppeteer_evaluate", {
                "script": "document.querySelector('h1')?.textContent || 'No H1 found'"
            })
            print(f"📋 H1 text: {h1_text}")
            
            # Extract all paragraph text
            paragraphs = await puppeteer._call_tool("puppeteer_evaluate", {
                "script": "Array.from(document.querySelectorAll('p')).map(p => p.textContent).join(' | ')"
            })
            print(f"📝 Paragraphs: {paragraphs}")
            
            # Count elements
            element_count = await puppeteer._call_tool("puppeteer_evaluate", {
                "script": "document.querySelectorAll('*').length"
            })
            print(f"🔢 Total elements on page: {element_count}")
            
            # Get page URL
            current_url = await puppeteer._call_tool("puppeteer_evaluate", {
                "script": "window.location.href"
            })
            print(f"🌐 Current URL: {current_url}")
            
        except Exception as e:
            print(f"❌ Data extraction failed: {e}")

        # Take screenshot
        print(f"\n📸 Screenshot Demo:")
        print("-" * 30)
        
        try:
            screenshot_result = await puppeteer._call_tool("puppeteer_screenshot", {
                "name": "httpbin_page",
                "encoded": True
            })
            
            # Create output directory
            output_dir = Path("puppeteer_demo_output")
            output_dir.mkdir(exist_ok=True)
            
            print(f"✅ Screenshot captured")
            print(f"📁 Screenshot saved with Puppeteer MCP server")
            
        except Exception as e:
            print(f"❌ Screenshot failed: {e}")

        # Navigate to a more interactive page
        print(f"\n🔗 Navigating to interactive page:")
        print("-" * 30)
        
        try:
            # Navigate to a form page
            form_nav = await puppeteer._call_tool("puppeteer_navigate", {
                "url": "https://httpbin.org/forms/post"
            })
            print(f"✅ Navigated to form page: {form_nav}")
            
            # Wait for page to load
            await asyncio.sleep(2)
            
            # Check if form elements exist
            form_check = await puppeteer._call_tool("puppeteer_evaluate", {
                "script": "document.querySelector('form') ? 'Form found' : 'No form found'"
            })
            print(f"📋 Form check: {form_check}")
            
        except Exception as e:
            print(f"❌ Form navigation failed: {e}")

        # Form interaction demo
        print(f"\n📝 Form Interaction Demo:")
        print("-" * 30)
        
        try:
            # Fill out form fields using CSS selectors
            customer_name_result = await puppeteer._call_tool("puppeteer_fill", {
                "selector": "input[name='custname']",
                "value": "John Doe"
            })
            print(f"✅ Customer name filled: {customer_name_result}")
            
            # Fill telephone field
            telephone_result = await puppeteer._call_tool("puppeteer_fill", {
                "selector": "input[name='custtel']",
                "value": "555-1234"
            })
            print(f"✅ Telephone filled: {telephone_result}")
            
            # Fill email field
            email_result = await puppeteer._call_tool("puppeteer_fill", {
                "selector": "input[name='custemail']",
                "value": "john@example.com"
            })
            print(f"✅ Email filled: {email_result}")
            
            # Select pizza size
            size_result = await puppeteer._call_tool("puppeteer_select", {
                "selector": "select[name='size']",
                "value": "large"
            })
            print(f"✅ Pizza size selected: {size_result}")
            
            # Verify form data was filled
            form_data = await puppeteer._call_tool("puppeteer_evaluate", {
                "script": """({
                    name: document.querySelector("input[name='custname']")?.value,
                    tel: document.querySelector("input[name='custtel']")?.value, 
                    email: document.querySelector("input[name='custemail']")?.value,
                    size: document.querySelector("select[name='size']")?.value
                })"""
            })
            print(f"✅ Form data verified: {form_data}")
            
        except Exception as e:
            print(f"❌ Form interaction failed: {e}")

        # Element interaction demo
        print(f"\n🖱️ Element Interaction Demo:")
        print("-" * 30)
        
        try:
            # Hover over submit button
            hover_result = await puppeteer._call_tool("puppeteer_hover", {
                "selector": "input[type='submit']"
            })
            print(f"✅ Hovered over submit button: {hover_result}")
            
            # Get button text
            button_text = await puppeteer._call_tool("puppeteer_evaluate", {
                "script": "document.querySelector('input[type=\"submit\"]')?.value || 'No submit button'"
            })
            print(f"🔘 Submit button text: {button_text}")
            
            # Click the submit button (this will submit the form)
            click_result = await puppeteer._call_tool("puppeteer_click", {
                "selector": "input[type='submit']"
            })
            print(f"✅ Submit button clicked: {click_result}")
            
            # Wait for form submission
            await asyncio.sleep(2)
            
            # Check the result page
            result_check = await puppeteer._call_tool("puppeteer_evaluate", {
                "script": "document.body.textContent.includes('form') ? 'Form submitted successfully' : 'Form submission result'"
            })
            print(f"📋 Form submission result: {result_check}")
            
        except Exception as e:
            print(f"❌ Element interaction failed: {e}")

        # Advanced JavaScript demo
        print(f"\n🔬 Advanced JavaScript Execution:")
        print("-" * 30)
        
        try:
            # Get page metrics
            page_metrics = await puppeteer._call_tool("puppeteer_evaluate", {
                "script": """({
                    viewport: {
                        width: window.innerWidth,
                        height: window.innerHeight
                    },
                    scroll: {
                        x: window.scrollX,
                        y: window.scrollY
                    },
                    elements: {
                        total: document.querySelectorAll('*').length,
                        inputs: document.querySelectorAll('input').length,
                        forms: document.querySelectorAll('form').length,
                        links: document.querySelectorAll('a').length
                    },
                    readyState: document.readyState,
                    referrer: document.referrer || 'Direct navigation'
                })"""
            })
            print(f"📊 Page metrics: {page_metrics}")
            
            # Get all form field values
            form_values = await puppeteer._call_tool("puppeteer_evaluate", {
                "script": """Array.from(document.querySelectorAll('input, select, textarea')).map(el => ({
                    name: el.name || el.id || 'unnamed',
                    type: el.type || el.tagName.toLowerCase(),
                    value: el.value,
                    required: el.required
                }))"""
            })
            print(f"📝 All form fields: {form_values}")
            
        except Exception as e:
            print(f"❌ Advanced JavaScript failed: {e}")

        # Navigation demo
        print(f"\n🧭 Navigation Demo:")
        print("-" * 30)
        
        try:
            # Navigate to another page
            wiki_nav = await puppeteer._call_tool("puppeteer_navigate", {
                "url": "https://httpbin.org/json"
            })
            print(f"✅ Navigated to JSON endpoint: {wiki_nav}")
            
            await asyncio.sleep(2)
            
            # Extract JSON data from the page
            json_data = await puppeteer._call_tool("puppeteer_evaluate", {
                "script": "document.querySelector('pre')?.textContent || document.body.textContent"
            })
            print(f"📄 JSON content: {json_data}")
            
            # Take final screenshot
            final_screenshot = await puppeteer._call_tool("puppeteer_screenshot", {
                "name": "final_page",
                "encoded": True
            })
            print(f"📸 Final screenshot captured")
            
        except Exception as e:
            print(f"❌ Final navigation failed: {e}")

        # Performance and capability summary
        print(f"\n⚠️  Puppeteer Automation Notes:")
        print("-" * 30)
        print("• Direct browser control with Chrome/Chromium")
        print("• Full JavaScript execution capabilities")
        print("• CSS selector-based element targeting")
        print("• Real-time page interaction and data extraction")
        print("• Screenshot and visual monitoring")
        print("• Headless or visible browser modes")

        # Available method categories
        print(f"\n🎯 Available Python Methods:")
        print("-" * 30)
        method_categories = {
            "🔗 Navigation": [
                "puppeteer.navigate(url)", "puppeteer.get_page_url()", "puppeteer.wait_for_navigation()"
            ],
            "🖱️ Interaction": [
                "puppeteer.click(selector)", "puppeteer.fill(selector, value)", 
                "puppeteer.select(selector, value)", "puppeteer.hover(selector)",
                "puppeteer.type_text(selector, text)", "puppeteer.press_key(key)"
            ],
            "📊 Data Extraction": [
                "puppeteer.evaluate(script)", "puppeteer.get_text(selector)",
                "puppeteer.get_attribute(selector, attr)", "puppeteer.get_value(selector)",
                "puppeteer.get_page_title()", "puppeteer.get_page_content()"
            ],
            "📸 Monitoring": [
                "puppeteer.take_screenshot(name)", "puppeteer.screenshot_element(selector)",
                "puppeteer.screenshot_full_page()"
            ],
            "⏳ Waiting & Scrolling": [
                "puppeteer.wait_for_element(selector)", "puppeteer.scroll_to_element(selector)",
                "puppeteer.scroll_by(x, y)", "puppeteer.scroll_to_bottom()"
            ],
            "🔍 Element Utilities": [
                "puppeteer.element_exists(selector)", "puppeteer.element_visible(selector)",
                "puppeteer.count_elements(selector)"
            ]
        }
        
        for category, methods in method_categories.items():
            print(f"\n{category}:")
            for method in methods:
                print(f"   • {method}")

        print(f"\n💡 JavaScript Execution Tips:")
        print("-" * 30)
        print("• Use expressions, not return statements: 'document.title' not 'return document.title'")
        print("• For complex scripts, use IIFE: '(() => { /* code */ })()'")
        print("• CSS selectors work with all interaction methods")
        print("• Combine querySelector with JavaScript for powerful data extraction")

        print("\n" + "=" * 60)
        print("🎉 Puppeteer MCP Integration Complete!")
        print("📚 Context manager handled connection lifecycle")
        print("🌐 Powered by local Chrome/Chromium browser")
        print("🔌 MCP server automatically disconnected")


if __name__ == "__main__":
    asyncio.run(main())