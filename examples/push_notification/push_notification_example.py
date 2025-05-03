#!/usr/bin/env python
"""
push_notification_example.py - Python A2A Push Notification Example

This example demonstrates how to use push notifications (subscribe and receive updates)
in the python-a2a library.

To run:
    python push_notification_example.py
"""

import asyncio
import time
import threading
import uuid
import json
from queue import Queue
from threading import Event

# Import python_a2a components
from python_a2a import BaseA2AServer, AgentCard, run_server
from python_a2a import Message, TextContent, MessageRole
from python_a2a.models.task import Task, TaskStatus, TaskState
from python_a2a.client.streaming import StreamingClient
from flask import Response, request, jsonify

class PushNotificationServer(BaseA2AServer):
    """
    Server that demonstrates push notifications in python-a2a.
    """

    def __init__(self):
        # Create agent card with streaming capability
        self.agent_card = AgentCard(
            name="Push Notification Demo",
            description="Demonstrates push notifications",
            url="http://localhost:8000",  # Will be overridden
            version="1.0.0",
            capabilities={
                "streaming": True,
                "tasks": True,
                "task_streaming": True
            }
        )

    def handle_message(self, message):
        """
        Handle standard messages (required to implement the abstract method)
        """
        # Extract text content
        text = ""
        if hasattr(message.content, "text"):
            text = message.content.text

        # Return a simple response
        return Message(
            content=TextContent(
                text="This demo shows push notifications. Please use task streaming."
            ),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )

    def handle_task(self, task):
        """Handle regular (non-streaming) tasks"""
        task.status = TaskStatus(state=TaskState.COMPLETED)
        task.artifacts = [{
            "parts": [{
                "type": "text",
                "text": "For push notifications, use streaming API"
            }]
        }]
        return task

    def setup_routes(self, app):
        """Set up custom routes for SSE streaming"""

        @app.route("/a2a/tasks/stream", methods=["POST"])
        def handle_task_streaming():
            """Route that handles SSE for push notifications"""
            try:
                # Get the task data
                data = request.json
                print(f"Received streaming request: {json.dumps(data)[:100]}...")

                # Parse the task
                if "task" in data:
                    task = Task.from_dict(data["task"])
                else:
                    task = Task.from_dict(data)

                # Set up streaming with Server-Sent Events
                def generate():
                    """Generate SSE events for push notifications"""
                    # Set up communication between threads
                    notification_queue = Queue()
                    done_event = Event()

                    def process_notifications():
                        """Process notifications in a separate thread"""
                        try:
                            # Set task to waiting
                            task.status = TaskStatus(state=TaskState.WAITING)
                            print("Sending initial waiting status")

                            # Queue initial notification
                            notification_queue.put({
                                "event": "update",
                                "data": {
                                    "task": task.to_dict(),
                                    "index": 0,
                                    "append": True
                                }
                            })

                            # Send 5 notifications
                            for i in range(1, 6):
                                # Wait between notifications
                                time.sleep(1)

                                # Update notification content
                                task.status = TaskStatus(
                                    state=TaskState.WAITING,
                                    message={"step": i, "total_steps": 5}
                                )

                                task.artifacts = [{
                                    "parts": [{
                                        "type": "text",
                                        "text": f"Notification #{i}: Processing step {i}/5"
                                    }]
                                }]

                                # Queue notification
                                print(f"Sending notification {i}/5")
                                notification_queue.put({
                                    "event": "update",
                                    "data": {
                                        "task": task.to_dict(),
                                        "index": i,
                                        "append": True
                                    }
                                })

                            # Send completion
                            time.sleep(1)
                            task.status = TaskStatus(state=TaskState.COMPLETED)
                            task.artifacts = [{
                                "parts": [{
                                    "type": "text",
                                    "text": "All notifications delivered successfully!"
                                }]
                            }]

                            # Queue completion notification
                            print("Sending completion notification")
                            notification_queue.put({
                                "event": "complete",
                                "data": {
                                    "task": task.to_dict(),
                                    "index": 6,
                                    "append": True,
                                    "lastUpdate": True
                                }
                            })

                        except Exception as e:
                            print(f"Error processing notifications: {e}")
                            notification_queue.put({
                                "event": "error",
                                "data": {"error": str(e)}
                            })

                        finally:
                            # Signal completion
                            done_event.set()

                    # Start processing thread
                    thread = threading.Thread(target=process_notifications)
                    thread.daemon = True
                    thread.start()

                    # SSE header comment
                    yield ": Push notification channel established\n\n"

                    # Process notifications as they arrive
                    timeout = time.time() + 60  # 1-minute timeout
                    while not done_event.is_set() and time.time() < timeout:
                        try:
                            # Check for notifications
                            if not notification_queue.empty():
                                notification = notification_queue.get(block=False)

                                # Format as SSE event
                                event_type = notification.get("event", "update")
                                data = notification.get("data", {})

                                # Send the notification
                                yield f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

                                # Check for completion
                                if event_type == "complete" or data.get("lastUpdate", False):
                                    break

                            else:
                                # No data yet, wait briefly
                                time.sleep(0.1)

                        except Exception as e:
                            print(f"Error sending notification: {e}")
                            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
                            break

                    # Handle timeout
                    if time.time() >= timeout and not done_event.is_set():
                        yield f"event: error\ndata: {json.dumps({'error': 'Timeout'})}\n\n"

                # Create and return SSE response
                response = Response(generate(), mimetype="text/event-stream")
                response.headers["Cache-Control"] = "no-cache"
                response.headers["Connection"] = "keep-alive"
                response.headers["X-Accel-Buffering"] = "no"
                return response

            except Exception as e:
                print(f"Error handling streaming request: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({"error": str(e)}), 500

        # Also register at root /stream endpoint for compatibility
        @app.route("/stream", methods=["POST"])
        def stream_fallback():
            return handle_task_streaming()

async def client_demo(port):
    """
    Client that subscribes to and receives push notifications.
    """
    print("\n[Client] Starting push notification client")

    # Create streaming client
    client = StreamingClient(f"http://localhost:{port}")

    # Create message
    message = Message(
        content=TextContent(text="Send me notifications"),
        role=MessageRole.USER
    )

    # Create task
    task = Task(
        id=f"notification-{int(time.time())}",
        message=message.to_dict()
    )

    print("[Client] Subscribing to push notifications...")

    try:
        # Subscribe to push notifications
        notification_count = 0

        # Process notifications as they arrive
        async for update in client.tasks_send_subscribe(task):
            notification_count += 1

            # Extract status
            status = update.status.state.value if update.status else "unknown"

            # Display notification
            print(f"\n[Client] Received notification #{notification_count}")
            print(f"[Client] Status: {status}")

            # Display progress if available
            if update.status and update.status.message:
                message = update.status.message
                if isinstance(message, dict) and "step" in message:
                    step = message.get("step", 0)
                    total = message.get("total_steps", 0)
                    print(f"[Client] Progress: Step {step}/{total}")

            # Display content
            if update.artifacts:
                for artifact in update.artifacts:
                    if isinstance(artifact, dict) and "parts" in artifact:
                        for part in artifact["parts"]:
                            if isinstance(part, dict) and part.get("type") == "text":
                                print(f"[Client] Content: {part.get('text')}")

            # Check for completion
            if update.status and update.status.state == TaskState.COMPLETED:
                print("[Client] All notifications received!")

        print(f"\n[Client] Successfully received {notification_count} push notifications")

    except Exception as e:
        print(f"[Client] Error: {e}")
        import traceback
        traceback.print_exc()

def find_free_port():
    """Find an available port."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 0))
        return s.getsockname()[1]

def run_notification_demo():
    """Run both server and client."""
    # Get a free port
    port = find_free_port()

    print(f"Starting push notification demo on port {port}")

    # Create server
    server = PushNotificationServer()

    # Start server in background thread
    server_thread = threading.Thread(
        target=lambda: run_server(server, host="localhost", port=port),
        daemon=True
    )
    server_thread.start()

    # Wait for server to start
    print("Starting server...")
    time.sleep(2)

    # Run client
    asyncio.run(client_demo(port))

    print("\nDemo complete!")

if __name__ == "__main__":
    try:
        run_notification_demo()
    except KeyboardInterrupt:
        print("\nExiting...")

