"""
Filesystem MCP Server Example

This example demonstrates how to use the Filesystem MCP server with python-a2a.
It shows basic file operations like reading, writing, directory listing, and file management.
"""

import asyncio
import os
import tempfile
from pathlib import Path
from python_a2a.mcp.providers import FilesystemMCPServer


async def main():
    print("🗂️  Filesystem MCP Server Example")
    print("=" * 60)
    print("This example demonstrates filesystem MCP server integration:")
    print("- File reading and writing operations")
    print("- Directory listing and management")
    print("- File search and metadata operations\n")

    # Create test directory  
    temp_path = "/tmp/mcp_filesystem_test"
    os.makedirs(temp_path, exist_ok=True)
    
    # Resolve real path (macOS /tmp -> /private/tmp)
    test_dir = str(Path(temp_path).resolve())
    print(f"🔒 Using test directory: {test_dir}")

    # Create filesystem MCP server instance
    fs = FilesystemMCPServer(allowed_directories=[test_dir])

    # Use context manager for resource management
    async with fs:
        print("\n🔌 Filesystem MCP server connected successfully!\n")

        # List all available tools
        print("🛠️  Available Filesystem MCP Tools:")
        print("-" * 40)
        try:
            tools = await fs.list_tools()
            
            if tools:
                for i, tool in enumerate(tools, 1):
                    tool_name = tool.get('name', 'Unknown')
                    tool_desc = tool.get('description', 'No description')
                    # Truncate long descriptions
                    if len(tool_desc) > 80:
                        tool_desc = tool_desc[:80] + "..."
                    
                    print(f"{i:2d}. {tool_name}")
                    print(f"     {tool_desc}")
                    print()
                
                print(f"📊 Total available tools: {len(tools)}")
            else:
                print("❌ No tools found")
                
        except Exception as e:
            print(f"❌ Failed to list tools: {e}")

        # Demonstrate file operations
        print(f"\n📁 File Operations Demo:")
        print("-" * 30)
        
        # Test file creation
        test_file = os.path.join(test_dir, "test.txt")
        test_content = "Hello from MCP Filesystem Server!\nThis is a test file.\n"
        
        print("📝 Creating test file...")
        write_result = await fs.write_file(test_file, test_content)
        if isinstance(write_result, str) and "Error" in write_result:
            print(f"❌ Failed to create file: {write_result}")
        else:
            print(f"✅ Created: {os.path.basename(test_file)}")
        
        # Test file reading
        print("\n📖 Reading file content...")
        try:
            content = await fs.read_file(test_file)
            if isinstance(content, str) and "Error" in content:
                print(f"❌ Failed to read file: {content}")
            else:
                print(f"✅ Content: {repr(str(content)[:50])}...")
        except Exception as e:
            print(f"❌ Error reading file: {e}")
        
        # Test directory listing
        print(f"\n📋 Listing directory contents...")
        files = await fs.list_directory(test_dir)
        if isinstance(files, str) and "Error" in files:
            print(f"❌ Failed to list directory: {files}")
        else:
            print(f"✅ Found {len(files)} items:")
            for item in files[:5]:  # Show first 5 items
                print(f"   • {item}")
        
        # Test file info
        print(f"\n📊 Getting file metadata...")
        file_info = await fs.get_file_info(test_file)
        if isinstance(file_info, str) and "Error" in file_info:
            print(f"❌ Failed to get file info: {file_info}")
        elif isinstance(file_info, dict):
            print(f"✅ File size: {file_info.get('size', 'unknown')} bytes")
            print(f"   File type: {file_info.get('type', 'unknown')}")
            print(f"   Modified: {file_info.get('lastModified', 'unknown')}")
        else:
            print(f"❌ Unexpected file info format: {type(file_info)}")
        
        # Test multiple file operations
        print(f"\n📚 Creating multiple test files...")
        test_files = []
        for i in range(3):
            file_path = os.path.join(test_dir, f"file_{i}.txt")
            result = await fs.write_file(file_path, f"Content of file {i}")
            if not (isinstance(result, str) and "Error" in result):
                test_files.append(file_path)
        
        print(f"✅ Created {len(test_files)} files")
        
        # Test multiple file reading  
        if test_files:
            print(f"\n📖 Reading multiple files...")
            contents = await fs.read_multiple_files(test_files)
            if isinstance(contents, list):
                print(f"✅ Read {len(contents)} files successfully")
            else:
                print(f"❌ Failed to read multiple files: {contents}")
        
        # Test search functionality
        print(f"\n🔍 Searching for files...")
        search_results = await fs.search_files(test_dir, "file_")
        if isinstance(search_results, list):
            print(f"✅ Found {len(search_results)} files matching pattern")
            for result in search_results[:3]:  # Show first 3
                print(f"   • {os.path.basename(result)}")
        else:
            print(f"❌ Search failed: {search_results}")
        
        # Test directory creation
        print(f"\n📁 Creating subdirectory...")
        sub_dir = os.path.join(test_dir, "subdir")
        dir_result = await fs.create_directory(sub_dir)
        if isinstance(dir_result, str) and "Error" in dir_result:
            print(f"❌ Failed to create directory: {dir_result}")
        else:
            print(f"✅ Created: {os.path.basename(sub_dir)}")
        
        # Test directory tree
        print(f"\n🌳 Getting directory tree...")
        tree = await fs.directory_tree(test_dir)
        if isinstance(tree, str) and "Error" in tree:
            print(f"❌ Failed to get directory tree: {tree}")
        elif isinstance(tree, dict):
            print(f"✅ Directory tree contains: {tree.get('name', 'unknown')}")
            children = tree.get('children', [])
            print(f"   📂 {len(children)} items in directory")
        elif isinstance(tree, list):
            print(f"✅ Directory contains {len(tree)} items:")
            for item in tree[:3]:
                if isinstance(item, dict):
                    print(f"   📄 {item.get('name', 'unknown')} ({item.get('type', 'unknown')})")
        else:
            print(f"❌ Unexpected tree format: {type(tree)}")
        
        # Test allowed directories
        print(f"\n🔒 Checking allowed directories...")
        allowed = await fs.list_allowed_directories()
        print(f"✅ Server can access {len(allowed)} directories:")
        for directory in allowed:
            print(f"   • {directory}")
        
        # Performance note
        print(f"\n⚠️  Security & Performance Notes:")
        print("-" * 30)
        print("• Server only accesses explicitly allowed directories")
        print("• All operations are sandboxed for security")
        print("• File operations are efficient for individual files")
        print("• Directory traversal respects permission boundaries")

        # Available method categories
        print(f"\n🎯 Available Python Methods:")
        print("-" * 30)
        method_categories = {
            "📄 File Operations": [
                "read_file()", "read_multiple_files()", "write_file()", "edit_file()"
            ],
            "📁 Directory Operations": [
                "create_directory()", "list_directory()", "directory_tree()"
            ],
            "🔍 Search & Discovery": [
                "search_files()", "get_file_info()", "list_allowed_directories()"
            ],
            "🔄 File Management": [
                "move_file()"
            ]
        }
        
        for category, methods in method_categories.items():
            print(f"\n{category}:")
            for method in methods:
                print(f"   • fs.{method}")

        print("\n" + "=" * 60)
        print("🎉 Filesystem MCP Integration Complete!")
        print("📚 Context manager handled connection lifecycle")
        print("🔒 All operations are secure and sandboxed")
        print("🔌 MCP server automatically disconnected")
        
    # Cleanup test directory
    try:
        import shutil
        shutil.rmtree(test_dir)
        print(f"\n🧹 Cleaned up test directory")
    except Exception as e:
        print(f"⚠️  Could not clean up {test_dir}: {e}")


if __name__ == "__main__":
    asyncio.run(main())