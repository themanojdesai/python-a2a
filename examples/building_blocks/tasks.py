#!/usr/bin/env python
"""
A2A Tasks

This example demonstrates how to work with A2A tasks, which are the
core units of work in the A2A protocol. Tasks encapsulate messages,
their statuses, and results.

To run:
    python tasks.py

Requirements:
    pip install python-a2a
"""

import sys
import json
import time
from datetime import datetime

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import python_a2a
        print("✅ python-a2a is installed correctly!")
        return True
    except ImportError:
        print("❌ python-a2a is not installed!")
        print("\nPlease install it with:")
        print("    pip install python-a2a")
        print("\nThen run this example again.")
        return False

def main():
    # First, check dependencies
    if not check_dependencies():
        return 1
    
    # Import after checking dependencies
    from python_a2a import (
        Task, TaskStatus, TaskState,
        Message, MessageRole, TextContent
    )
    
    print("\n🌟 A2A Tasks 🌟")
    print("This example shows how to work with A2A tasks, the core units of work in A2A.\n")
    
    # Create a message to use in our tasks
    user_message = Message(
        content=TextContent(text="What's the weather forecast for Paris this weekend?"),
        role=MessageRole.USER
    )
    
    print("=== Creating Tasks ===")
    
    # Method 1: Create a task from a message dictionary
    task1 = Task(message=user_message.to_dict())
    print(f"Created Task 1 (from message dict) with ID: {task1.id}")
    
    # Method 2: Create a task with explicit ID
    custom_id = "weather-task-123"
    task2 = Task(
        id=custom_id,
        message=user_message.to_dict()
    )
    print(f"Created Task 2 (with custom ID): {task2.id}")
    
    # Method 3: Create a task with additional metadata
    task3 = Task(
        message=user_message.to_dict(),
        metadata={
            "priority": "high",
            "user_id": "u-12345",
            "source": "mobile-app"
        }
    )
    print(f"Created Task 3 (with metadata) with ID: {task3.id}")
    
    print("\n=== Task States and Status Updates ===")
    
    # Demonstrate the task lifecycle with state transitions
    print("\nSimulating a task lifecycle:")
    
    # Create the task
    weather_task = Task(message=user_message.to_dict())
    print(f"1. Created task with ID: {weather_task.id}")
    print(f"   Initial state: {weather_task.status.state}")
    
    # Update to WAITING state (e.g., waiting for function call)
    weather_task.status = TaskStatus(
        state=TaskState.WAITING,
        message={"info": "Retrieving weather data"}
    )
    print(f"2. Updated state to: {weather_task.status.state}")
    print(f"   Status message: {weather_task.status.message}")
    time.sleep(1)  # Simulate some time passing
    
    # Update to INPUT_REQUIRED (e.g., need user to specify which day)
    weather_task.status = TaskStatus(
        state=TaskState.INPUT_REQUIRED,
        message={"prompt": "Do you want the forecast for Saturday or Sunday?"}
    )
    print(f"3. Updated state to: {weather_task.status.state}")
    print(f"   Status message: {weather_task.status.message}")
    time.sleep(1)  # Simulate some time passing
    
    # Simulate user providing input (new message added to history)
    weather_task.history.append({
        "role": "user",
        "content": {"type": "text", "text": "Saturday please"}
    })
    print(f"4. User provided input: 'Saturday please'")
    
    # Update to WAITING again
    weather_task.status = TaskStatus(
        state=TaskState.WAITING,
        message={"info": "Retrieving Saturday forecast for Paris"}
    )
    print(f"5. Updated state to: {weather_task.status.state}")
    time.sleep(1)  # Simulate some time passing
    
    # Completed with response
    weather_task.status = TaskStatus(
        state=TaskState.COMPLETED,
        message={"info": "Forecast retrieved successfully"}
    )
    
    # Add the response artifact
    weather_task.artifacts = [
        {
            "parts": [
                {
                    "type": "text",
                    "text": "The forecast for Paris this Saturday is mostly sunny with a high of 72°F (22°C) and a low of 54°F (12°C). There's a 10% chance of rain in the evening."
                }
            ]
        }
    ]
    
    print(f"6. Task completed with state: {weather_task.status.state}")
    print(f"   Response: {weather_task.artifacts[0]['parts'][0]['text'][:50]}...")
    
    print("\n=== Alternative Task States ===")
    
    # Show other possible task states
    
    # 1. Canceled task
    canceled_task = Task(
        message={"content": {"type": "text", "text": "Book a flight to London"}}
    )
    canceled_task.status = TaskStatus(
        state=TaskState.CANCELED,
        message={"reason": "User canceled the request"}
    )
    print(f"Canceled task state: {canceled_task.status.state}")
    print(f"Reason: {canceled_task.status.message.get('reason')}")
    
    # 2. Failed task
    failed_task = Task(
        message={"content": {"type": "text", "text": "Book a table at Le Cinq restaurant"}}
    )
    failed_task.status = TaskStatus(
        state=TaskState.FAILED,
        message={"error": "Restaurant booking service unavailable"}
    )
    print(f"Failed task state: {failed_task.status.state}")
    print(f"Error: {failed_task.status.message.get('error')}")
    
    print("\n=== Task Serialization and Storage ===")
    
    # Convert task to JSON for storage or transmission
    task_json = json.dumps(weather_task.to_dict(), indent=2)
    
    # Save to file
    with open("weather_task.json", "w") as f:
        f.write(task_json)
    print("Saved task to weather_task.json")
    
    # Demonstrate loading a task
    with open("weather_task.json", "r") as f:
        loaded_task_data = json.load(f)
    
    loaded_task = Task.from_dict(loaded_task_data)
    print(f"Loaded task with ID: {loaded_task.id}")
    
    # Demonstrate retrieving text content
    text_content = loaded_task.get_text()
    print(f"Retrieved text content: {text_content[:50]}...")
    
    print("\n=== Task Management Example ===")
    
    # Demonstrate a simple task management system
    task_store = {}
    
    # Create some tasks
    for i in range(5):
        message = Message(
            content=TextContent(text=f"Sample task #{i+1}"),
            role=MessageRole.USER
        )
        task = Task(message=message.to_dict())
        task_store[task.id] = task
    
    print(f"Created {len(task_store)} tasks in our task store")
    
    # Update task statuses randomly
    import random
    states = [TaskState.SUBMITTED, TaskState.WAITING, TaskState.COMPLETED, TaskState.FAILED]
    
    for task_id, task in task_store.items():
        # Set a random state
        state = random.choice(states)
        task.status = TaskStatus(
            state=state,
            timestamp=datetime.now().isoformat()
        )
        
        # Add an artifact if completed
        if state == TaskState.COMPLETED:
            task.artifacts = [
                {
                    "parts": [
                        {
                            "type": "text",
                            "text": f"Completed task {task_id}"
                        }
                    ]
                }
            ]
    
    # List all tasks with their states
    print("\nTask Status Overview:")
    print("-" * 50)
    print(f"{'ID':<12} {'State':<12} {'Timestamp'}")
    print("-" * 50)
    
    for task_id, task in task_store.items():
        print(f"{task_id[:10]:<12} {task.status.state.value:<12} {task.status.timestamp}")
    
    # Filter tasks by state
    completed_tasks = [t for t in task_store.values() if t.status.state == TaskState.COMPLETED]
    print(f"\nNumber of completed tasks: {len(completed_tasks)}")
    
    print("\n=== What's Next? ===")
    print("1. Try 'agent_skills.py' to learn about using the @skill decorator")
    print("2. Try 'function_calling.py' to see tasks with function calls")
    print("3. Try 'simple_server.py' to build a server that processes tasks")
    
    print("\n🎉 You've learned how to work with A2A tasks! 🎉")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n✅ Program interrupted by user")
        sys.exit(0)