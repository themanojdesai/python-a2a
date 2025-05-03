# A2A Streaming Examples

This directory contains a series of examples demonstrating the streaming capabilities of the A2A (Agent-to-Agent) library. Each example builds on concepts from previous examples to showcase different aspects of streaming functionality.

## Dependencies

Before running these examples, make sure you have the required dependencies installed:

```bash
# Core requirements
pip install python-a2a

# Additional requirements for UI examples (05_streaming_ui_integration.py)
pip install colorama tqdm flask

# Additional requirements for distributed examples (06_distributed_streaming.py)
pip install aiohttp tqdm
```

## Example Overview

0. **basic_streaming.py** - Minimal streaming implementation
   - Simplest possible streaming server (only core essentials)
   - Minimal streaming client with proper error handling
   - Proper dictionary chunk handling
   - Ideal starting point for understanding streaming

1. **01_basic_streaming.py** - Comprehensive introduction to streaming basics
   - Simple streaming server implementation
   - Basic client for consuming streams
   - Comparison between streamed and non-streamed responses
   - Simulated thinking delays and natural language chunking

2. **02_advanced_streaming.py** - Advanced streaming techniques
   - Metrics tracking for streaming performance
   - Different chunking strategies (sentence, word, paragraph)
   - Performance visualization and analytics
   - Stream buffering and handling

3. **03_streaming_llm_integration.py** - Integrating with LLM providers
   - Bridging LLM provider streaming APIs with A2A
   - Handling different provider formats (OpenAI, Anthropic, Bedrock)
   - Transformer pipelines for content processing
   - Error handling and fallback mechanisms

4. **04_task_based_streaming.py** - Structured task-based streaming
   - Task state transitions (WAITING, COMPLETED, etc.)
   - Progress tracking with step-by-step updates
   - Artifact generation during streaming
   - Partial and final results as structured artifacts

5. **05_streaming_ui_integration.py** - Integrating streaming with UIs
   - CLI-based streaming visualization
   - Web interface using Server-Sent Events (SSE)
   - Interactive streaming controls (pause, resume, cancel)
   - Real-time progress visualization

6. **06_distributed_streaming.py** - Distributed streaming architecture
   - Multiple streaming servers with load balancing
   - Stream aggregation from multiple sources
   - Fault tolerance and failover strategies
   - Performance monitoring and metrics

## Running the Examples

Each example is designed to be run independently. Simply use Python to execute the desired example:

```bash
python 01_basic_streaming.py
```

For the more advanced examples, make sure to install the dependencies first:

```bash
# For UI integration example
python 05_streaming_ui_integration.py

# For distributed streaming example
python 06_distributed_streaming.py
```

### Troubleshooting Common Issues

1. **Missing Module Errors**: Make sure to install all required dependencies as listed in the Dependencies section.

2. **"Message.__init__() missing required argument 'role'"**: This error occurs because the Message constructor requires a role parameter. If you're creating your own code based on these examples, always include `role=MessageRole.USER` or `role=MessageRole.AGENT` when creating Message objects.

3. **Type Errors with Dictionary Chunks**: When handling streamed chunks, remember they can sometimes be dictionaries rather than simple strings. Handle this properly by checking types and extracting content when needed.

4. **Port Conflicts**: If a server won't start due to a port being in use, modify the port number in the code or wait a few moments for the previous server process to fully terminate.

## Key Concepts

The examples in this directory demonstrate these key streaming concepts:

1. **Stream Creation**: How to implement streaming on the server side using async generators
2. **Stream Consumption**: How to consume streams on the client side
3. **Chunking Strategies**: Different approaches to breaking content into streamable chunks
4. **Error Handling**: Robust error handling for streaming scenarios
5. **Performance Metrics**: Tracking and analyzing streaming performance
6. **UI Integration**: Techniques for rendering streaming content in user interfaces
7. **LLM Integration**: Connecting A2A streaming with LLM providers
8. **Distributed Architecture**: Advanced patterns for scalable streaming systems

## Debugging Streaming Issues

If you encounter issues with streaming, the `core_streaming_test.py` script provides a simple test harness to verify that core streaming functionality is working correctly.

## Further Resources

For more information on A2A streaming, refer to:

- [A2A Example Documentation](https://github.com/anthropics/python-a2a/blob/main/examples/streaming/README.md)
- The implementation in `python_a2a/server/http.py` and `python_a2a/client/streaming.py`
- [Official Documentation](https://python-a2a.readthedocs.io/) for the full API reference