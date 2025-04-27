#!/usr/bin/env python
"""
Simple Google A2A Compatibility Test

A very basic test script that directly tests format conversion and compatibility
without requiring servers or complex setup.
"""

import sys
import json

try:
    from python_a2a import Message, MessageRole, TextContent, Conversation
    from python_a2a.models.task import Task, TaskStatus, TaskState
except ImportError:
    print("❌ python_a2a package not found. Please install it first.")
    sys.exit(1)

def print_separator():
    print("\n" + "-" * 60 + "\n")

# Basic format conversion test
def test_message_conversion():
    print("Testing Message format conversion:")
    
    # Create a standard python_a2a message
    message = Message(
        content=TextContent(text="This is a test message"),
        role=MessageRole.USER
    )
    
    # Get original format
    orig_format = message.to_dict()
    print("\nOriginal python_a2a format:")
    print(json.dumps(orig_format, indent=2))
    
    # Convert to Google A2A format
    google_format = message.to_google_a2a()
    print("\nConverted to Google A2A format:")
    print(json.dumps(google_format, indent=2))
    
    # Convert back to python_a2a (via from_google_a2a)
    converted_message = Message.from_google_a2a(google_format)
    converted_format = converted_message.to_dict()
    print("\nBack to python_a2a format:")
    print(json.dumps(converted_format, indent=2))
    
    # Check conversion success
    if converted_message.content.text == message.content.text and converted_message.role == message.role:
        print("\n✅ Message conversion test PASSED")
    else:
        print("\n❌ Message conversion test FAILED")
        print(f"Original text: '{message.content.text}', Converted text: '{converted_message.content.text}'")

# Test Task format conversion
def test_task_conversion():
    print("Testing Task format conversion:")
    
    # Create a standard python_a2a task
    task = Task(
        id="test-task-id",
        session_id="test-session-id",
        status=TaskStatus(state=TaskState.COMPLETED),
        message={
            "content": {
                "type": "text",
                "text": "Test task message"
            },
            "role": "user"
        },
        artifacts=[{
            "parts": [{
                "type": "text",
                "text": "Test response"
            }]
        }]
    )
    
    # Get original format
    orig_format = task.to_dict()
    print("\nOriginal python_a2a task format:")
    print(json.dumps(orig_format, indent=2))
    
    # Convert to Google A2A format
    google_format = task.to_google_a2a()
    print("\nConverted to Google A2A task format:")
    print(json.dumps(google_format, indent=2))
    
    # Convert back
    converted_task = Task.from_google_a2a(google_format)
    
    # Check conversion success
    if converted_task.id == task.id and converted_task.status.state == task.status.state:
        print("\n✅ Task conversion test PASSED")
    else:
        print("\n❌ Task conversion test FAILED")

# Test compatibility mode
def test_compatibility_mode():
    print("Testing compatibility mode:")
    
    # Create a message
    message = Message(
        content=TextContent(text="Test compatibility mode"),
        role=MessageRole.USER
    )
    
    # Standard python_a2a format (default)
    standard_format = message.to_dict()
    print("\nBefore enabling compatibility mode:")
    print(json.dumps(standard_format, indent=2))
    
    # Enable Google A2A compatibility mode
    Message.enable_google_a2a_compatibility(True)
    
    # Now to_dict() should return Google A2A format
    compat_format = message.to_dict()
    print("\nAfter enabling compatibility mode:")
    print(json.dumps(compat_format, indent=2))
    
    # Check compatibility mode success
    if "parts" in compat_format and not "parts" in standard_format:
        print("\n✅ Compatibility mode test PASSED")
    else:
        print("\n❌ Compatibility mode test FAILED")
    
    # Reset compatibility mode
    Message.enable_google_a2a_compatibility(False)

def main():
    print("=" * 60)
    print("SIMPLE GOOGLE A2A COMPATIBILITY TEST")
    print("=" * 60)
    print("This test validates basic format conversion functionality")
    
    # Test message conversion
    test_message_conversion()
    print_separator()
    
    # Test task conversion
    test_task_conversion()
    print_separator()
    
    # Test compatibility mode
    test_compatibility_mode()
    print_separator()
    
    print("Tests completed!")

if __name__ == "__main__":
    main()