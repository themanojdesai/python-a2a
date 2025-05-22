#!/usr/bin/env python
"""
04_task_based_streaming.py - Task-Based Streaming Example

This example demonstrates task-based streaming in the A2A protocol,
which provides a more structured approach to streaming than message-based
streaming. Tasks have state transitions, artifacts, and metadata.

Key concepts demonstrated:
- Creating task-based streaming servers
- Task state transitions during streaming
- Streaming task artifacts
- Using tasks_send_subscribe for streaming
- Multi-step task execution with streaming updates

Usage:
    python 04_task_based_streaming.py [--port PORT] [--query QUERY]
    
Options:
    --port PORT           Port to run the server on
    --query QUERY         Query to send to the agent
    --steps STEPS         Number of steps to execute (default: 3)
    -i, --interactive     Enable interactive mode
"""

import asyncio
import sys
import time
import random
import threading
import argparse
import uuid
import json
from typing import Dict, Any, List, Optional, AsyncGenerator, Union

# Import python_a2a components
from python_a2a import (
    BaseA2AServer, AgentCard, Message, TextContent, MessageRole, run_server
)
from python_a2a.client.streaming import StreamingClient
from python_a2a.models.task import Task, TaskStatus, TaskState

# ANSI colors for prettier output
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
RED = "\033[31m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Default configuration
DEFAULT_QUERY = "Process this text and extract key information"
DEFAULT_STEPS = 3


class TaskStreamingServer(BaseA2AServer):
    """
    A2A server that implements task-based streaming.
    
    This server handles task-based streaming, which provides more structure
    than simple message-based streaming. Tasks have state transitions,
    artifacts, and metadata.
    """
    
    def __init__(self, url: str = "http://localhost:8000", steps: int = 3):
        """
        Initialize the task streaming server.
        
        Args:
            url: Server URL
            steps: Number of processing steps to simulate
        """
        # Create an agent card with task capabilities
        self.agent_card = AgentCard(
            name="Task-Based Streaming Demo",
            description="Demonstrates task-based streaming in the A2A protocol",
            url=url,
            version="1.0.0",
            capabilities={
                "streaming": True,
                "tasks": True,
                "task_streaming": True,
                "multi_step_tasks": True
            }
        )
        
        # Store configuration
        self.steps = steps
        
        # Store active tasks
        self.tasks = {}
    
    def setup_routes(self, app):
        """
        Set up custom routes for this agent.
        
        This is called by the Flask app creation process to add
        custom routes for this specific agent.
        
        Args:
            app: The Flask application to add routes to
        """
        import json
        import asyncio
        import threading
        from queue import Queue
        from flask import request, Response, jsonify
        import time
        import traceback
        from contextlib import contextmanager

        STREAM_TIMEOUT = 300
        QUEUE_CHECK_INTERVAL = 0.01

        @contextmanager
        def managed_thread(target_func, daemon=True):
            thread = threading.Thread(target=target_func)
            thread.daemon = daemon
            thread.start()
            try:
                yield thread
            finally:
                pass

        def create_sse_event(event_type, data):
            if event_type:
                return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
            return f"data: {json.dumps(data)}\n\n"

        def log_with_context(message, task_id=None, level="info"):
            log_context = {"task_id": task_id} if task_id else {}
            log_data = {"message": message, "level": level, "context": log_context}
            print(f"{level.upper()}: {message}")
            return log_data

        async def process_task_stream(task, queue, done_event, error_event, error_message):
            task_id = task.id if task else "unknown"
            task_stream = None
            try:
                task_stream = self.tasks_send_subscribe(task)
                index = 0
                last_task_update = None

                async for task_update in task_stream:
                    last_task_update = task_update
                    update_dict = task_update.to_dict()
                    queue.put({
                        "task": update_dict,
                        "index": index,
                        "append": True
                    })
                    index += 1

                if last_task_update:
                    final_dict = last_task_update.to_dict()
                    if isinstance(final_dict.get("status"), dict):
                        final_dict["status"]["state"] = "completed"
                    queue.put({
                        "task": final_dict,
                        "index": index,
                        "append": True,
                        "lastChunk": True
                    })

            except asyncio.CancelledError:
                error_message[0] = "Task streaming cancelled"
                error_event.set()
            except Exception as e:
                error_message[0] = str(e)
                error_event.set()
            finally:
                done_event.set()
                if hasattr(task_stream, 'aclose') and callable(task_stream.aclose):
                    try:
                        await task_stream.aclose()
                    except Exception as e:
                        log_with_context(f"Error closing task stream: {e}", task_id, "error")

        def run_task_stream(task, queue, done_event, error_event, error_message):
            task_id = task.id if task else "unknown"
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                main_task = loop.create_task(process_task_stream(task, queue, done_event, error_event, error_message))
                try:
                    loop.run_until_complete(main_task)
                except Exception as e:
                    error_message[0] = f"Event loop error: {str(e)}"
                    error_event.set()
                finally:
                    pending = asyncio.all_tasks(loop)
                    for pending_task in pending:
                        pending_task.cancel()
                    if pending:
                        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    loop.close()
            except Exception as e:
                error_message[0] = f"Thread setup error: {str(e)}"
                error_event.set()
                done_event.set()

        @app.route("/a2a/tasks/stream", methods=["POST"])
        def handle_task_streaming():
            task = None
            try:
                data = request.json
                if "task" in data:
                    task = Task.from_dict(data["task"])
                else:
                    task = Task.from_dict(data)

                if not hasattr(self, 'tasks_send_subscribe'):
                    return jsonify({"error": "This agent does not support task streaming"}), 405

                def generate():
                    queue = Queue()
                    done_event = threading.Event()
                    error_event = threading.Event()
                    error_message = [None]
                    task_id = task.id if task else "unknown"

                    with managed_thread(lambda: run_task_stream(task, queue, done_event, error_event, error_message)):
                        yield create_sse_event(None, {"message": "Task streaming established"})
                        
                        deadline = time.time() + STREAM_TIMEOUT
                        sent_last_chunk = False

                        while (not done_event.is_set() or not queue.empty()) and time.time() < deadline:
                            if error_event.is_set():
                                yield create_sse_event("error", {"error": error_message[0] or "Unknown error"})
                                break

                            try:
                                if not queue.empty():
                                    update = queue.get(block=False)
                                    yield create_sse_event(None, update)
                                    if update.get("lastChunk", False):
                                        sent_last_chunk = True
                                        break
                                else:
                                    time.sleep(QUEUE_CHECK_INTERVAL)
                            except Exception as e:
                                yield create_sse_event("error", {"error": str(e)})
                                break

                        if time.time() >= deadline and not done_event.is_set():
                            yield create_sse_event("error", {"error": "Task streaming timed out"})

                response = Response(generate(), mimetype="text/event-stream")
                response.headers.update({
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                    "Transfer-Encoding": "chunked"
                })
                return response

            except Exception as e:
                task_id = task.id if task else None
                log_with_context(f"Exception in task streaming handler: {str(e)}", task_id, "error")
                traceback.print_exc()
                return jsonify({"error": str(e)}), 500
    
    def handle_message(self, message: Message) -> Message:
        """
        Handle standard (non-streaming, non-task) message.
        
        Args:
            message: Incoming message
            
        Returns:
            Response message
        """
        query = message.content.text if hasattr(message.content, "text") else "No query provided"
        
        return Message(
            content=TextContent(
                text=(
                    f"This server is optimized for task-based streaming. "
                    f"For the best experience, please use the task API instead of the message API. "
                    f"Your query was: \"{query}\""
                )
            ),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )
    
    def handle_task(self, task: Task) -> Task:
        """
        Process a task synchronously.
        
        This method is used for non-streaming task requests.
        
        Args:
            task: Task to process
            
        Returns:
            Processed task
        """
        # Extract message and query
        message = task.message or {}
        query = ""
        
        if isinstance(message, dict):
            if "content" in message and "text" in message["content"]:
                query = message["content"]["text"]
            elif "parts" in message:
                for part in message["parts"]:
                    if isinstance(part, dict) and part.get("type") == "text":
                        query = part.get("text", "")
                        break
        
        # Generate a complete (non-streaming) response
        task.status = TaskStatus(state=TaskState.COMPLETED)
        
        # Create a result artifact
        task.artifacts = [{
            "type": "text",
            "role": "assistant",
            "parts": [{
                "type": "text",
                "text": (
                    f"This is a non-streaming task response. For the best experience, "
                    f"please use the task streaming API with tasks_send_subscribe. "
                    f"Your query was: \"{query}\""
                )
            }]
        }]
        
        return task
    
    async def tasks_send_subscribe(self, task: Task) -> AsyncGenerator[Task, None]:
        """
        Process a task with streaming updates.
        
        This method is the task-based equivalent of stream_response.
        It yields task updates as the task progresses through its lifecycle.
        
        Args:
            task: Task to process
            
        Yields:
            Task updates as the task progresses
        """
        # Store the task
        task_id = task.id
        self.tasks[task_id] = task
        
        # Extract message and query
        message = task.message or {}
        query = ""
        
        if isinstance(message, dict):
            if "content" in message and "text" in message["content"]:
                query = message["content"]["text"]
            elif "parts" in message:
                for part in message["parts"]:
                    if isinstance(part, dict) and part.get("type") == "text":
                        query = part.get("text", "")
                        break
        
        print(f"[Server] Processing task {task_id}")
        print(f"[Server] Query: {query[:50]}...")
        
        task.status = TaskStatus(state=TaskState.SUBMITTED)
        
        print(f"[Server] Task {task_id}: Yielding SUBMITTED state")
        yield Task(
            id=task.id,
            status=TaskStatus(
                state=task.status.state,
                message=task.status.message.copy() if task.status.message else None,
                timestamp=task.status.timestamp
            ),
            message=task.message,
            session_id=task.session_id,
            artifacts=task.artifacts.copy() if task.artifacts else []
        )
        
        # Update task status to waiting (analogous to in_progress)
        task.status = TaskStatus(state=TaskState.WAITING)
        
        # Yield the initial task state
        print(f"[Server] Task {task_id}: Yielding initial WAITING state")
        # Create a deep copy of the task
        yield Task(
            id=task.id,
            status=TaskStatus(
                state=task.status.state,
                message=task.status.message.copy() if task.status.message else None,
                timestamp=task.status.timestamp
            ),
            message=task.message,
            session_id=task.session_id,
            artifacts=task.artifacts.copy() if task.artifacts else []
        )
        
        # Determine number of steps and processing strategy
        steps = self.steps
        step_labels = [
            "Analyzing input",
            "Processing content",
            "Generating results",
            "Finalizing output",
            "Optimizing response",
            "Verifying results",
            "Formatting output"
        ]
        
        # Choose labels for steps based on requested step count
        selected_steps = step_labels[:steps]
        if steps > len(step_labels):
            # Add generic steps if requested more than predefined
            selected_steps += [f"Additional processing {i+1}" for i in range(steps - len(step_labels))]
        
        # Process each step
        for i, step_label in enumerate(selected_steps):
            # Update status message with current step
            task.status.message = {"step": i + 1, "total_steps": steps, "action": step_label}
            
            # Simulate processing time
            await asyncio.sleep(random.uniform(0.5, 1.2))
            
            # Add a progress artifact
            progress_artifact = {
                "type": "progress_update",
                "role": "system",
                "step": i + 1,
                "total_steps": steps,
                "action": step_label,
                "progress": (i + 1) / steps
            }
            
            # Update artifacts with progress
            task.artifacts = [progress_artifact] + (task.artifacts or [])
            
            # Yield the task update
            print(f"[Server] Task {task_id}: Step {i+1}/{steps} - {step_label}")
            # Create a deep copy of the task
            yield Task(
                id=task.id,
                status=TaskStatus(
                    state=task.status.state,
                    message=task.status.message.copy() if task.status.message else None,
                    timestamp=task.status.timestamp
                ),
                message=task.message,
                session_id=task.session_id,
                artifacts=task.artifacts.copy() if task.artifacts else []
            )
            
            # Simulate generating partial results
            if i > 0 and i < steps - 1:
                # For middle steps, add some partial content
                partial_result = self._generate_partial_result(query, i, steps)
                
                # Create a partial result artifact
                partial_artifact = {
                    "type": "partial_result",
                    "role": "assistant",
                    "step": i + 1,
                    "parts": [{
                        "type": "text",
                        "text": partial_result
                    }]
                }
                
                # Update artifacts with partial result
                task.artifacts = [partial_artifact] + task.artifacts
                
                # Yield the task update with partial result
                print(f"[Server] Task {task_id}: Adding partial result ({len(partial_result)} chars)")
                # Create a deep copy of the task
                yield Task(
                    id=task.id,
                    status=TaskStatus(
                        state=task.status.state,
                        message=task.status.message.copy() if task.status.message else None,
                        timestamp=task.status.timestamp
                    ),
                    message=task.message,
                    session_id=task.session_id,
                    artifacts=task.artifacts.copy() if task.artifacts else []
                )
        
        # Generate the final result
        await asyncio.sleep(random.uniform(0.8, 1.5))
        
        # Create the final result artifact
        final_result = self._generate_final_result(query, steps)
        final_artifact = {
            "type": "result",
            "role": "assistant",
            "parts": [{
                "type": "text",
                "text": final_result
            }]
        }
        
        # Update artifacts with final result
        task.artifacts = [final_artifact] + task.artifacts
        
        # Update task status to completed
        task.status = TaskStatus(state=TaskState.COMPLETED)
        
        # Yield the final task state
        print(f"[Server] Task {task_id}: Yielding final COMPLETED state")
        # Create a deep copy of the task
        yield Task(
            id=task.id,
            status=TaskStatus(
                state=task.status.state,
                message=task.status.message.copy() if task.status.message else None,
                timestamp=task.status.timestamp
            ),
            message=task.message,
            session_id=task.session_id,
            artifacts=task.artifacts.copy() if task.artifacts else []
        )
        
        print(f"[Server] Task {task_id}: Processing complete")
    
    def _generate_partial_result(self, query: str, step: int, total_steps: int) -> str:
        """
        Generate a partial result for a given step.
        
        Args:
            query: User query
            step: Current step number
            total_steps: Total number of steps
            
        Returns:
            Partial result text
        """
        # Generate different partial results based on step
        if step == 1:
            return (
                f"## Partial Analysis (Step {step}/{total_steps})\n\n"
                f"Initial processing of your query: \"{query[:30]}...\"\n\n"
                f"Currently analyzing the input and preparing for further processing. "
                f"This is an intermediate result and will be expanded in subsequent steps."
            )
        else:
            progress = (step / total_steps) * 100
            return (
                f"## Processing Update (Step {step}/{total_steps})\n\n"
                f"Progress: {progress:.1f}% complete\n\n"
                f"Continuing to process your request about \"{query[:20]}...\"\n\n"
                f"We've completed the initial analysis and are now working on synthesizing "
                f"the results. More details will be provided in the final response."
            )
    
    def _generate_final_result(self, query: str, steps: int) -> str:
        """
        Generate a final result for the task.
        
        Args:
            query: User query
            steps: Number of steps used
            
        Returns:
            Final result text
        """
        query_lower = query.lower()
        
        # Generate different responses based on query content
        if "extract" in query_lower and ("information" in query_lower or "key" in query_lower):
            return (
                f"# Analysis Results\n\n"
                f"I've processed your request: \"{query}\"\n\n"
                f"## Key Information Extracted\n\n"
                f"1. **Primary Concept**: Information extraction from text\n"
                f"2. **User Intent**: Automated processing of textual content\n"
                f"3. **Complexity Level**: Medium (based on query structure)\n\n"
                f"## Processing Details\n\n"
                f"- Completed {steps} processing steps\n"
                f"- Applied natural language understanding techniques\n"
                f"- Used structural analysis for key information identification\n\n"
                f"## Recommendations\n\n"
                f"For more specific extraction, consider providing structured text or "
                f"specifying particular types of information you're looking for. "
                f"This allows for more targeted extraction and analysis."
            )
        else:
            return (
                f"# Task Processing Complete\n\n"
                f"I've processed your request: \"{query}\"\n\n"
                f"## Process Summary\n\n"
                f"- Executed {steps} processing steps\n"
                f"- Analyzed content using multiple techniques\n"
                f"- Generated comprehensive results\n\n"
                f"## Key Takeaways\n\n"
                f"1. Task-based streaming allows for structured updates during processing\n"
                f"2. Each step can provide partial results and progress information\n"
                f"3. The final artifact contains the complete response\n\n"
                f"## Next Steps\n\n"
                f"You can use this task-based approach for complex, multi-step processes "
                f"that benefit from incremental updates and progress tracking. It's "
                f"particularly useful for long-running tasks where users need visibility "
                f"into the processing status."
            )


class TaskStreamClient:
    """
    Client for streaming task-based responses.
    
    This client handles task-based streaming, including task state
    transitions, artifact updates, and progress tracking.
    """
    
    def __init__(self, url: str, show_artifacts: bool = True, show_status: bool = True):
        """
        Initialize the task streaming client.
        
        Args:
            url: Server URL
            show_artifacts: Whether to show all artifacts
            show_status: Whether to show status updates
        """
        self.url = url
        self.show_artifacts = show_artifacts
        self.show_status = show_status
        
        # Create streaming client with correct path
        self.client = StreamingClient(url)
        
        # Override streaming endpoints
        self.client._stream_task_url = f"{url}/a2a/tasks/stream"
        
        # Add debugging
        print(f"Task streaming client initialized with URL: {self.client._stream_task_url}")
        
        # Metrics
        self.start_time = time.time()
        self.updates_received = 0
        self.artifacts_received = 0
    
    async def run_task(self, query: str) -> Dict[str, Any]:
        """
        Run a task with streaming updates.
        
        Args:
            query: Query to send
            
        Returns:
            Final task state
        """
        print(f"\n{BLUE}Creating task for query: \"{query}\"{RESET}")
        
        # Create message
        message = Message(
            content=TextContent(text=query),
            role=MessageRole.USER
        )
        
        # Create task
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            message=message.to_dict()
        )
        
        print(f"{BLUE}Streaming task progress:{RESET}")
        print("-" * 60)
        
        # Reset metrics
        self.start_time = time.time()
        self.updates_received = 0
        self.artifacts_received = 0
        latest_update = None
        
        try:
            # Stream task updates
            async for task_update in self.client.tasks_send_subscribe(task):
                print(f"task update is :{task_update}")
                # Track updates
                self.updates_received += 1
                
                print(f"Raw update {self.updates_received} artifacts:")
                for i, artifact in enumerate(task_update.artifacts or []):
                    print(f"  Artifact {i} type: {artifact.get('type', 'MISSING')}")
                    print(f"  Artifact {i} raw: {json.dumps(artifact)[:200]}...")
                
                # Store latest update
                latest_update = task_update
                
                # Process and display the update
                await self._process_task_update(task_update)
            
            # Print final stats
            self._print_final_stats()
            
            return latest_update.to_dict() if latest_update else {}
        
        except Exception as e:
            print(f"\n{RED}Error during task streaming: {e}{RESET}")
            return {}
    
    async def _process_task_update(self, task: Task) -> None:
        """
        Process and display a task update.
        
        Args:
            task: Updated task object
        """
        # Extract status
        status = task.status.state.value if task.status else "unknown"
        message = task.status.message if task.status else {}
        
        # Display status update if enabled
        if self.show_status:
            # Format status line
            if isinstance(message, dict):
                # Formatted status with steps
                if "step" in message and "total_steps" in message:
                    step = message.get("step", 0)
                    total_steps = message.get("total_steps", 0)
                    action = message.get("action", "Processing")
                    
                    status_line = (
                        f"{YELLOW}[Status] {status.upper()} | "
                        f"Step {step}/{total_steps}: {action}{RESET}"
                    )
                else:
                    # Generic status
                    status_line = f"{YELLOW}[Status] {status.upper()}{RESET}"
            else:
                # Simple status
                status_line = f"{YELLOW}[Status] {status.upper()}{RESET}"
            
            print(status_line)
        
        # Process artifacts
        print(f"Task for processing artifact: {task}")
        artifacts = task.artifacts or []
        for artifact in artifacts:
            await self._process_artifact(artifact)
            
        # Small delay for UI updates
        await asyncio.sleep(0.01)
    
    async def _process_artifact(self, artifact: Dict[str, Any]) -> None:
        """
        Process and display a task artifact.
        
        Args:
            artifact: Artifact to process
        """
        # Track artifact
        self.artifacts_received += 1
        
        # Skip display if artifacts not enabled
        if not self.show_artifacts:
            return
        
        # Extract artifact type and role
        artifact_type = artifact.get("type", "unknown")
        role = artifact.get("role", "assistant")
        
        # Process different artifact types
        if artifact_type == "progress_update":
            # Progress update artifact
            step = artifact.get("step", 0)
            total_steps = artifact.get("total_steps", 0)
            action = artifact.get("action", "Processing")
            progress = artifact.get("progress", 0)
            
            # Format progress bar
            bar_width = 30
            filled = int(bar_width * progress)
            bar = f"[{'=' * filled}{' ' * (bar_width - filled)}]"
            
            # Print progress
            print(f"{CYAN}Progress: {bar} {progress*100:.1f}%{RESET}")
            
        elif artifact_type in ("result", "partial_result"):
            # Text result artifact
            text = ""
            
            # Extract text from parts
            parts = artifact.get("parts", [])
            for part in parts:
                if isinstance(part, dict) and part.get("type") == "text":
                    text += part.get("text", "")
            
            # Print with appropriate styling
            if artifact_type == "result":
                # Final result
                print(f"\n{GREEN}{BOLD}Final Result:{RESET}")
                print(f"{text}")
            else:
                # Partial result
                print(f"\n{CYAN}Partial Result:{RESET}")
                print(f"{text}")
        
        elif "parts" in artifact and isinstance(artifact["parts"], list):
            # Handle artifacts with parts but no type
            text = ""
            for part in artifact["parts"]:
                if isinstance(part, dict) and part.get("type") == "text":
                    text += part.get("text", "")
            if text:
                print(f"\n{CYAN}Partial Result:{RESET}")
                print(f"{text}")
        
        elif artifact_type == "text":
            # Simple text artifact
            if "parts" in artifact:
                # Extract text from parts
                parts = artifact.get("parts", [])
                for part in parts:
                    if isinstance(part, dict) and part.get("type") == "text":
                        print(part.get("text", ""))
            elif "text" in artifact:
                # Direct text
                print(artifact["text"])
        
        else:
            # Unknown artifact type - show raw
            print(f"{MAGENTA}[Artifact: {artifact_type}]{RESET}")
            try:
                print(json.dumps(artifact, indent=2))
            except:
                print(str(artifact))
    
    def _print_final_stats(self) -> None:
        """Print final task statistics."""
        elapsed = time.time() - self.start_time
        updates_per_sec = self.updates_received / elapsed if elapsed > 0 else 0
        
        print("\n" + "-" * 60)
        print(f"{GREEN}{BOLD}Task Completed{RESET}")
        print(f"{GREEN}✓ Received {self.updates_received} task updates in {elapsed:.2f} seconds{RESET}")
        print(f"{GREEN}✓ Processed {self.artifacts_received} artifacts{RESET}")
        if elapsed > 0:
            print(f"{GREEN}✓ Update rate: {updates_per_sec:.1f} updates/second{RESET}")


def find_free_port():
    """Find an available port on localhost."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 0))
        return s.getsockname()[1]


async def main_async(args):
    """
    Main async function.
    
    Args:
        args: Command line arguments
    """
    # Get port
    port = args.port or find_free_port()
    server_url = f"http://localhost:{port}"
    
    # Create task streaming server
    server = TaskStreamingServer(
        url=server_url,
        steps=args.steps
    )
    
    # Start server in background thread
    print(f"{BLUE}Starting task streaming server on port {port}...{RESET}")
    print(f"{BLUE}Server configured for {args.steps} processing steps{RESET}")
    
    server_thread = threading.Thread(
        target=lambda: run_server(server, host="localhost", port=port),
        daemon=True
    )
    server_thread.start()
    
    # Wait for server to start
    await asyncio.sleep(1)
    
    # Create client
    client = TaskStreamClient(server_url)
    
    # Run initial task
    await client.run_task(args.query)
    
    # Interactive mode if requested
    if args.interactive:
        try:
            while True:
                print(f"\n{BLUE}Enter a query (or Ctrl+C to exit):{RESET}")
                next_query = input("> ")
                if next_query.strip():
                    await client.run_task(next_query)
                else:
                    print(f"{YELLOW}Query cannot be empty{RESET}")
        except KeyboardInterrupt:
            print(f"\n{BLUE}Exiting interactive mode{RESET}")


def main():
    """Parse arguments and run the example."""
    parser = argparse.ArgumentParser(description="Task-Based Streaming Example")
    parser.add_argument("--query", default=DEFAULT_QUERY,
                       help="Query to send to the agent")
    parser.add_argument("--port", type=int, default=None,
                       help="Port to run the server on (will find a free port if not specified)")
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS,
                       help="Number of processing steps to simulate")
    parser.add_argument("-i", "--interactive", action="store_true",
                       help="Enable interactive mode after initial query")
    
    args = parser.parse_args()
    
    try:
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        print(f"\n{BLUE}Exiting{RESET}")


if __name__ == "__main__":
    main()