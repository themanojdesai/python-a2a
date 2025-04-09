# Python A2A Examples

This directory contains examples demonstrating the use of the Python A2A package to implement Google's Agent-to-Agent protocol.

## Why A2A Matters

The Agent-to-Agent (A2A) protocol enables interoperability between AI agents, allowing them to work together to solve complex problems. This has several key benefits:

1. **Specialization**: Agents can specialize in specific tasks, leading to better performance.
2. **Modularity**: Components can be improved or replaced independently.
3. **Extensibility**: New capabilities can be added by connecting new agents.
4. **Robustness**: If one agent fails, others can continue to operate.
5. **Scalability**: Complex workflows can be broken down into manageable pieces.

## Examples

### Basic

- **echo_server.py**: A simple echo server that demonstrates the basics of the A2A protocol.
- **simple_client.py**: A client that can send messages to any A2A-compatible agent.

```bash
# Start the echo server
python examples/basic/echo_server.py --port 5000

# Send a message to the echo server
python examples/basic/simple_client.py http://localhost:5000/a2a "Hello, A2A!"
```

### Agent Chain

- **weather_agent.py**: A specialized agent that provides weather information.
- **planning_agent.py**: An agent that helps plan trips and can consult with the weather agent.
- **agent_chain.py**: A script that chains multiple agents together to solve a complex task.

```bash
# Start the weather agent
python examples/chain/weather_agent.py --port 5001

# Start the planning agent (connected to the weather agent)
python examples/chain/planning_agent.py --port 5002 --weather-endpoint http://localhost:5001/a2a

# Run the chaining example
python examples/chain/agent_chain.py --weather-endpoint http://localhost:5001/a2a --planning-endpoint http://localhost:5002/a2a --location "Tokyo"
```

### Function Calling

- **calculator_agent.py**: An agent that provides mathematical calculation functions.
- **orchestrator.py**: An agent that delegates tasks to specialized function-providing agents.

```bash
# Start the calculator agent
python examples/function_calling/calculator_agent.py --port 5004

# Start the weather agent
python examples/chain/weather_agent.py --port 5001

# Start the orchestrator agent
python examples/function_calling/orchestrator.py --port 5005 --calculator-endpoint http://localhost:5004/a2a --weather-endpoint http://localhost:5001/a2a
```

### LLM Integration

- **openai_agent.py**: An A2A agent powered by OpenAI's GPT models.
- **claude_agent.py**: An A2A agent powered by Anthropic's Claude models.

```bash
# Start an OpenAI-powered agent
python examples/llm/openai_agent.py --port 5003 --api-key YOUR_OPENAI_API_KEY --model gpt-4
```

### Applications

- **research_assistant**: A research assistant application that coordinates multiple specialized agents.

## Learning from These Examples

These examples demonstrate several key patterns for using A2A:

1. **Specialization**: Create agents that do one thing well, rather than trying to build monolithic agents.
2. **Chaining**: Connect multiple agents in sequence to solve complex problems.
3. **Orchestration**: Use a central orchestrator agent to delegate tasks to specialized agents.
4. **Function Calling**: Expose specific capabilities as functions that other agents can call.
5. **Metadata**: Use agent metadata to discover and leverage agent capabilities dynamically.

## Creating Your Own A2A Agents

When creating your own A2A agents, consider the following:

1. What is the agent's specific area of expertise?
2. What functions or capabilities does it expose to other agents?
3. How will it interact with other agents in a larger system?
4. What information does it need from other agents to do its job?

A2A makes it easy to build modular, extensible AI systems where specialized agents collaborate to solve complex problems.