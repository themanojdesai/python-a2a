# Python A2A

<div align="center">

[![PyPI version](https://img.shields.io/pypi/v/python-a2a.svg)](https://pypi.org/project/python-a2a/)
[![Python Versions](https://img.shields.io/pypi/pyversions/python-a2a.svg)](https://pypi.org/project/python-a2a/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI Downloads](https://static.pepy.tech/badge/python-a2a)](https://pepy.tech/project/python-a2a)
[![Documentation Status](https://readthedocs.org/projects/python-a2a/badge/?version=latest)](https://python-a2a.readthedocs.io/en/latest/?badge=latest)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![UV Compatible](https://img.shields.io/badge/UV-Compatible-5C63FF.svg)](https://github.com/astral-sh/uv)
[![GitHub stars](https://img.shields.io/github/stars/themanojdesai/python-a2a?style=social)](https://github.com/themanojdesai/python-a2a/stargazers)

  <p>
      <a href="README.md">English</a> | <a href="README_zh.md">简体中文</a> | <a href="README_zh-TW.md">繁體中文</a> | <a href="README_ja.md">日本語</a> | <a href="README_es.md">Español</a> | <a href="README_de.md">Deutsch</a> | <a href="README_fr.md">Français</a>
      <!-- Add other languages here like: | <a href="README_de.md">Deutsch</a> -->
  </p>

**Google Agent-to-Agent (A2A) 协议的官方 Python 实现，集成 Model Context Protocol (MCP)**

</div>

## 🌟 概述

Python A2A 是一个全面且适用于生产环境的库，用于实现 Google 的 [Agent-to-Agent (A2A) 协议](https://google.github.io/A2A/)，并完全支持 [Model Context Protocol (MCP)](https://contextual.ai/introducing-mcp/)。它提供了构建可互操作的 AI 代理生态系统所需的所有功能，这些代理可以无缝协作以解决复杂问题。

A2A 协议为 AI 代理之间的交互建立了标准通信格式，而 MCP 通过提供标准化的方法扩展了这一功能，使代理能够访问外部工具和数据源。Python A2A 通过直观的 API 使这些协议易于使用，开发者可以使用这些 API 构建复杂的多代理系统。

## 📋 v0.5.X 新增功能

- **代理发现**：内置代理注册表和发现功能，完全兼容 Google A2A 协议
- **LangChain 集成**：与 LangChain 的工具和代理无缝集成
- **扩展的工具生态系统**：在任何代理中使用 LangChain 和 MCP 工具
- **增强的代理互操作性**：在 A2A 代理和 LangChain 代理之间进行转换
- **混合工作流引擎**：构建结合两种生态系统的复杂工作流
- **简化代理开发**：即时访问数千个预构建工具
- **高级流架构**：增强的 Server-Sent Events (SSE) 流、更好的错误处理和强大的回退机制
- **基于任务的流**：新的 `tasks_send_subscribe` 方法用于实时流式任务更新
- **流式数据块 API**：改进的 `StreamingChunk` 类用于结构化流式数据处理
- **多端点支持**：在多个流式端点之间自动发现和回退

## 📋 v0.4.X 新增功能

- **代理网络系统**：使用新的 `AgentNetwork` 类管理和发现多个代理
- **实时流式处理**：使用 `StreamingClient` 实现响应式 UI 的流式响应
- **工作流引擎**：使用新的流畅 API 定义复杂多代理工作流，支持条件分支和并行执行
- **AI 路由器**：使用 `AIAgentRouter` 自动将查询路由到最合适的代理
- **命令行界面**：通过新的 CLI 工具从终端控制代理
- **增强的异步支持**：在整个库中改进了 async/await 支持
- **新的连接选项**：改进了代理通信的错误处理和重试逻辑

## ✨ 为什么选择 Python A2A？

- **完整实现**：完全实现官方 A2A 规范，无任何妥协
- **代理发现**：内置代理注册表和发现功能，用于构建代理生态系统
- **MCP 集成**：对 Model Context Protocol 的一流支持，实现强大的工具使用代理
- **企业级就绪**：为生产环境构建，具有强大的错误处理和验证功能
- **框架无关**：与任何 Python 框架兼容（Flask、FastAPI、Django 等）
- **LLM 提供商灵活性**：原生集成 OpenAI、Anthropic、AWS Bedrock 等
- **最小依赖**：核心功能仅依赖 `requests` 库
- **卓越的开发者体验**：全面的文档、类型提示和示例

## 📦 安装

### 使用 pip（传统方式）

安装包含所有依赖项的基础包：

```bash
pip install python-a2a  # 包含 LangChain、MCP 和其他集成
```

或根据需求安装特定组件：

```bash
# 安装 Flask 服务器支持
pip install "python-a2a[server]"

# 安装 OpenAI 集成
pip install "python-a2a[openai]"

# 安装 Anthropic Claude 集成
pip install "python-a2a[anthropic]"

# 安装 AWS-Bedrock 集成
pip install "python-a2a[bedrock]"

# 安装 MCP 支持（Model Context Protocol）
pip install "python-a2a[mcp]"

# 安装所有可选依赖项
pip install "python-a2a[all]"
```

### 使用 UV（推荐）

[UV](https://github.com/astral-sh/uv) 是一个现代的 Python 包管理工具，比 pip 更快更可靠。使用 UV 安装：

```bash
# 如果尚未安装 UV，请先安装
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装基础包
uv install python-a2a
```

### 开发安装

开发环境推荐使用 UV 以获得更佳性能：

```bash
# 克隆仓库
git clone https://github.com/themanojdesai/python-a2a.git
cd python-a2a

# 创建虚拟环境并安装开发依赖项
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

> 💡 **提示**：点击代码块可复制到剪贴板

## 🚀 快速入门示例

### 1. 创建带有技能的简单 A2A 代理

```python
from python_a2a import A2AServer, skill, agent, run_server, TaskStatus, TaskState

@agent(
    name="Weather Agent",
    description="Provides weather information",
    version="1.0.0"
)
class WeatherAgent(A2AServer):
    
    @skill(
        name="Get Weather",
        description="Get current weather for a location",
        tags=["weather", "forecast"]
    )
    def get_weather(self, location):
        """Get weather for a location."""
        # Mock implementation
        return f"It's sunny and 75°F in {location}"
    
    def handle_task(self, task):
        # Extract location from message
        message_data = task.message or {}
        content = message_data.get("content", {})
        text = content.get("text", "") if isinstance(content, dict) else ""
        
        if "weather" in text.lower() and "in" in text.lower():
            location = text.split("in", 1)[1].strip().rstrip("?.")
            
            # Get weather and create response
            weather_text = self.get_weather(location)
            task.artifacts = [{
                "parts": [{"type": "text", "text": weather_text}]
            }]
            task.status = TaskStatus(state=TaskState.COMPLETED)
        else:
            task.status = TaskStatus(
                state=TaskState.INPUT_REQUIRED,
                message={"role": "agent", "content": {"type": "text", 
                         "text": "Please ask about weather in a specific location."}}
            )
        return task

# Run the server
if __name__ == "__main__":
    agent = WeatherAgent()
    run_server(agent, port=5000)
```

### 2. 构建包含多个代理的代理网络

```python
from python_a2a import AgentNetwork, A2AClient, AIAgentRouter

# 创建代理网络
network = AgentNetwork(name="Travel Assistant Network")

# 添加代理到网络
network.add("weather", "http://localhost:5001")
network.add("hotels", "http://localhost:5002")
network.add("attractions", "http://localhost:5003")

# 创建路由器以智能地将查询定向到最佳代理
router = AIAgentRouter(
    llm_client=A2AClient("http://localhost:5000/openai"),  # 用于路由决策的 LLM
    agent_network=network
)

# 将查询路由到适当的代理
agent_name, confidence = router.route_query("What's the weather like in Paris?")
print(f"Routing to {agent_name} with {confidence:.2f} confidence")

# 获取选定的代理并提问
agent = network.get_agent(agent_name)
response = agent.ask("What's the weather like in Paris?")
print(f"Response: {response}")

# 列出所有可用代理
print("\nAvailable Agents:")
for agent_info in network.list_agents():
    print(f"- {agent_info['name']}: {agent_info['description']}")
```

### 实时流式处理

通过全面的流式支持从代理获取实时响应：

```python
import asyncio
from python_a2a import StreamingClient, Message, TextContent, MessageRole

async def main():
    client = StreamingClient("http://localhost:5000")
    
    # 创建带有必需 role 参数的消息
    message = Message(
        content=TextContent(text="Tell me about A2A streaming"),
        role=MessageRole.USER
    )
    
    # 流式处理响应并实时处理数据块
    try:
        async for chunk in client.stream_response(message):
            # 处理不同格式的数据块（字符串或字典）
            if isinstance(chunk, dict):
                if "content" in chunk:
                    print(chunk["content"], end="", flush=True)
                elif "text" in chunk:
                    print(chunk["text"], end="", flush=True)
                else:
                    print(str(chunk), end="", flush=True)
            else:
                print(str(chunk), end="", flush=True)
    except Exception as e:
        print(f"Streaming error: {e}")
```

查看 `examples/streaming/` 目录中的完整流式示例：

- **basic_streaming.py**：最小化流式实现（从这里开始！）
- **01_basic_streaming.py**：流式基础的全面介绍
- **02_advanced_streaming.py**：使用不同分块策略的高级流式处理
- **03_streaming_llm_integration.py**：将流式处理与 LLM 提供商集成
- **04_task_based_streaming.py**：基于任务的流式处理与进度跟踪
- **05_streaming_ui_integration.py**：流式 UI 集成（CLI 和 Web）
- **06_distributed_streaming.py**：分布式流式架构

### 3. 工作流引擎

新的工作流引擎允许您定义复杂代理交互：

```python
from python_a2a import AgentNetwork, Flow
import asyncio

async def main():
    # 设置代理网络
    network = AgentNetwork()
    network.add("research", "http://localhost:5001")
    network.add("summarizer", "http://localhost:5002")
    network.add("factchecker", "http://localhost:5003")
    
    # 定义研究报告生成工作流
    flow = Flow(agent_network=network, name="Research Report Workflow")
    
    # 首先收集初始研究
    flow.ask("research", "Research the latest developments in {topic}")
    
    # 然后并行处理结果
    parallel_results = (flow.parallel()
        # 分支 1：创建摘要
        .ask("summarizer", "Summarize this research: {latest_result}")
        # 分支 2：验证关键事实
        .branch()
        .ask("factchecker", "Verify these key facts: {latest_result}")
        # 结束并行处理并收集结果
        .end_parallel(max_concurrency=2))
    
    # 根据验证结果提取见解
    flow.execute_function(
        lambda results, context: f"Summary: {results['1']}\nVerified Facts: {results['2']}",
        parallel_results
    )
    
    # 执行工作流
    result = await flow.run({
        "topic": "quantum computing advancements in the last year"
    })
    
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

### 4. AI 驱动的路由器

智能路由以选择每个查询的最佳代理：

```python
from python_a2a import AgentNetwork, AIAgentRouter, A2AClient
import asyncio

async def main():
    # 创建带有专用代理的网络
    network = AgentNetwork()
    network.add("math", "http://localhost:5001")
    network.add("history", "http://localhost:5002")
    network.add("science", "http://localhost:5003")
    network.add("literature", "http://localhost:5004")
    
    # 创建使用 LLM 进行决策的路由器
    router = AIAgentRouter(
        llm_client=A2AClient("http://localhost:5000/openai"),
        agent_network=network
    )
    
    # 要路由的示例查询
    queries = [
        "What is the formula for the area of a circle?",
        "Who wrote The Great Gatsby?",
        "When did World War II end?",
        "How does photosynthesis work?",
        "What are Newton's laws of motion?"
    ]
    
    # 将每个查询路由到最佳代理
    for query in queries:
        agent_name, confidence = router.route_query(query)
        agent = network.get_agent(agent_name)
        
        print(f"Query: {query}")
        print(f"Routed to: {agent_name} (confidence: {confidence:.2f})")
        
        # 从选定代理获取响应
        response = agent.ask(query)
        print(f"Response: {response[:100]}...\n")

if __name__ == "__main__":
    asyncio.run(main())
```

### 5. 定义包含多个代理的复杂工作流

```python
from python_a2a import AgentNetwork, Flow, AIAgentRouter
import asyncio

async def main():
    # 创建代理网络
    network = AgentNetwork()
    network.add("weather", "http://localhost:5001")
    network.add("recommendations", "http://localhost:5002")
    network.add("booking", "http://localhost:5003")
    
    # 创建路由器
    router = AIAgentRouter(
        llm_client=network.get_agent("weather"),  # 使用一个代理作为 LLM 进行路由
        agent_network=network
    )
    
    # 定义带有条件逻辑的工作流
    flow = Flow(agent_network=network, router=router, name="Travel Planning Workflow")
    
    # 首先获取天气
    flow.ask("weather", "What's the weather in {destination}?")
    
    # 根据天气条件分支
    flow.if_contains("sunny")
    
    # 如果晴朗，推荐户外活动
    flow.ask("recommendations", "Recommend outdoor activities in {destination}")
    
    # 结束条件并添加 else 分支
    flow.else_branch()
    
    # 如果不晴朗，推荐室内活动
    flow.ask("recommendations", "Recommend indoor activities in {destination}")
    
    # 结束 if-else 块
    flow.end_if()
    
    # 添加并行处理步骤
    (flow.parallel()
        .ask("booking", "Find hotels in {destination}")
        .branch()
        .ask("booking", "Find restaurants in {destination}")
        .end_parallel())
    
    # 使用初始上下文执行工作流
    result = await flow.run({
        "destination": "Paris",
        "travel_dates": "June 12-20"
    })
    
    print("Workflow result:")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

### 6. 使用命令行界面

```bash
# 向代理发送消息
a2a send http://localhost:5000 "What is artificial intelligence?"

# 实时流式响应
a2a stream http://localhost:5000 "Generate a step-by-step tutorial for making pasta"

# 启动 OpenAI 驱动的 A2A 服务器
a2a openai --model gpt-4 --system-prompt "You are a helpful coding assistant"

# 启动 Anthropic 驱动的 A2A 服务器
a2a anthropic --model claude-3-opus-20240229 --system-prompt "You are a friendly AI teacher"

# 启动带有工具的 MCP 服务器
a2a mcp-serve --name "Data Analysis MCP" --port 5001 --script analysis_tools.py

# 启动启用 MCP 的 A2A 代理
a2a mcp-agent --servers data=http://localhost:5001 calc=http://localhost:5002

# 直接调用 MCP 工具
a2a mcp-call http://localhost:5001 analyze_csv --params file=data.csv columns=price,date

# 管理代理网络
a2a network --add weather=http://localhost:5001 travel=http://localhost:5002 --save network.json

# 从脚本运行工作流
a2a workflow --script research_workflow.py --context initial_data.json
```

## 🔄 LangChain 集成（v0.5.X 新增）

Python A2A 包含内置的 LangChain 集成，使您可以轻松结合两种生态系统的最佳功能：

### 1. 将 MCP 工具转换为 LangChain

```python
from python_a2a.mcp import FastMCP, text_response
from python_a2a.langchain import to_langchain_tool

# 创建带有工具的 MCP 服务器
mcp_server = FastMCP(name="Basic Tools", description="Simple utility tools")

@mcp_server.tool(
    name="calculator",
    description="Calculate a mathematical expression"
)
def calculator(input):
    """Simple calculator that evaluates an expression."""
    try:
        result = eval(input)
        return text_response(f"Result: {result}")
    except Exception as e:
        return text_response(f"Error: {e}")

# 启动服务器
import threading, time
def run_server(server, port):
    server.run(host="0.0.0.0", port=port)
server_thread = threading.Thread(target=run_server, args=(mcp_server, 5000), daemon=True)
server_thread.start()
time.sleep(2)  # 允许服务器启动

# 将 MCP 工具转换为 LangChain
calculator_tool = to_langchain_tool("http://localhost:5000", "calculator")

# 在 LangChain 中使用工具
result = calculator_tool.run("5 * 9 + 3")
print(f"Result: {result}")
```

### 2. 将 LangChain 工具转换为 MCP 服务器

```python
from langchain.tools import Tool
from langchain_core.tools import BaseTool
from python_a2a.langchain import to_mcp_server

# 创建 LangChain 工具
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression"""
    try:
        result = eval(expression)
        return f"Result: {expression} = {result}"
    except Exception as e:
        return f"Error: {e}"

calculator_tool = Tool(
    name="calculator",
    description="Evaluate a mathematical expression",
    func=calculator
)

# 转换为 MCP 服务器
mcp_server = to_mcp_server(calculator_tool)

# 运行服务器
mcp_server.run(port=5000)
```

### 3. 将 LangChain 组件转换为 A2A 服务器

```python
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from python_a2a import A2AClient, run_server
from python_a2a.langchain import to_a2a_server

# 创建 LangChain LLM
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# 转换为 A2A 服务器
llm_server = to_a2a_server(llm)

# 创建简单链
template = "You are a helpful travel guide.\n\nQuestion: {query}\n\nAnswer:"
prompt = PromptTemplate.from_template(template)
travel_chain = prompt | llm | StrOutputParser()

# 转换为 A2A 服务器
travel_server = to_a2a_server(travel_chain)

# 在后台线程中运行服务器
import threading
llm_thread = threading.Thread(
    target=lambda: run_server(llm_server, port=5001),
    daemon=True
)
llm_thread.start()

travel_thread = threading.Thread(
    target=lambda: run_server(travel_server, port=5002),
    daemon=True
)
travel_thread.start()

# 测试服务器
llm_client = A2AClient("http://localhost:5001")
travel_client = A2AClient("http://localhost:5002")

llm_result = llm_client.ask("What is the capital of France?")
travel_result = travel_client.ask('{"query": "What are some must-see attractions in Paris?"}')
```

LangChain 会自动作为依赖项安装，因此一切开箱即用：

```bash
pip install python-a2a
# 完成！LangChain 会自动包含
```

## 🧩 核心功能

### 代理网络

Python A2A 现在包含一个强大的代理管理系统：

```python
from python_a2a import AgentNetwork, A2AClient

# 创建代理网络
network = AgentNetwork(name="Medical Assistant Network")

# 以不同方式添加代理
network.add("diagnosis", "http://localhost:5001")  # 从 URL 添加
network.add("medications", A2AClient("http://localhost:5002"))  # 从客户端实例添加

# 从 URL 列表发现代理
discovered_count = network.discover_agents([
    "http://localhost:5003",
    "http://localhost:5004",
    "http://localhost:5005"
])
print(f"Discovered {discovered_count} new agents")

# 列出网络中的所有代理
for agent_info in network.list_agents():
    print(f"Agent: {agent_info['name']}")
    print(f"URL: {agent_info['url']}")
    if 'description' in agent_info:
        print(f"Description: {agent_info['description']}")
    print()

# 获取特定代理
agent = network.get_agent("diagnosis")
response = agent.ask("What are the symptoms of the flu?")
```

### 7. 代理发现和注册表

```python
from python_a2a import AgentCard, A2AServer, run_server
from python_a2a.discovery import AgentRegistry, run_registry, enable_discovery, DiscoveryClient
import threading
import time

# 创建注册表服务器
registry = AgentRegistry(
    name="A2A Registry Server",
    description="Central registry for agent discovery"
)

# 在后台线程中运行注册表
registry_port = 8000
thread = threading.Thread(
    target=lambda: run_registry(registry, host="0.0.0.0", port=registry_port),
    daemon=True
)
thread.start()
time.sleep(1)  # 等待注册表启动

# 创建示例代理
agent_card = AgentCard(
    name="Weather Agent",
    description="Provides weather information",
    url="http://localhost:8001",
    version="1.0.0",
    capabilities={
        "weather_forecasting": True,
        "google_a2a_compatible": True  # 启用 Google A2A 兼容性
    }
)
agent = A2AServer(agent_card=agent_card)

# 启用发现 - 这会向注册表注册
registry_url = f"http://localhost:{registry_port}"
discovery_client = enable_discovery(agent, registry_url=registry_url)

# 在单独线程中运行代理
agent_thread = threading.Thread(
    target=lambda: run_server(agent, host="0.0.0.0", port=8001),
    daemon=True
)
agent_thread.start()
time.sleep(1)  # 等待代理启动

# 创建用于发现代理的客户端
client = DiscoveryClient(agent_card=None)  # 仅发现不需要代理卡
client.add_registry(registry_url)

# 发现所有代理
agents = client.discover()
print(f"Discovered {len(agents)} agents:")
for agent in agents:
    print(f"- {agent.name} at {agent.url}")
    print(f"  Capabilities: {agent.capabilities}")
```

## 📖 架构与设计原则

Python A2A 基于三个核心设计原则：

1. **协议优先**：严格遵守 A2A 和 MCP 协议规范以实现最大互操作性
2. **模块化**：所有组件均可组合和替换
3. **渐进增强**：从简单开始，仅在需要时增加复杂性

架构包含八个主要组件：

- **Models**：表示 A2A 消息、任务和代理卡的数据结构
- **Client**：用于向 A2A 代理发送消息和管理代理网络的组件
- **Server**：用于构建 A2A 兼容代理的组件
- **Discovery**：代理生态系统的注册表和发现机制
- **MCP**：实现 Model Context Protocol 服务器和客户端的工具
- **LangChain**：LangChain 集成的桥接组件
- **Workflow**：用于协调复杂代理交互的工作流引擎
- **Utils**：常用任务的辅助函数
- **CLI**：与代理交互的命令行界面

## 🗺️ 用例

Python A2A 可用于构建各种 AI 系统：

### 研究与开发

- **实验框架**：在保持相同代理接口的同时轻松替换不同的 LLM 后端
- **基准套件**：在标准化任务上比较不同代理实现的性能
- **流式研究助手**：使用流式处理创建响应式研究工具

### 企业系统

- **AI 协调**：使用代理网络协调不同部门的多个 AI 代理
- **遗留系统集成**：通过 A2A 接口包装遗留系统以实现 AI 访问
- **Workflow**：用于协调复杂代理交互的工作流引擎
- **Utils**：常用任务的辅助函数
- **CLI**：与代理交互的命令行界面

## 🗺️ 用例

Python A2A 可用于构建各种 AI 系统：

### 研究与开发

- **实验框架**：在保持相同代理接口的同时轻松切换不同的 LLM 后端
- **基准套件**：在标准化任务上比较不同代理实现的性能
- **流式研究助手**：使用流式传输创建具有实时输出的研究工具

### 企业系统

- **AI 协调**：使用代理网络跨不同部门协调多个 AI 代理
- **遗留系统集成**：使用 A2A 接口包装遗留系统以实现 AI 访问
- **复杂工作流**：使用多代理工作流和条件分支创建复杂业务流程

### 面向客户的应用

- **多阶段助手**：将复杂用户查询分解为由专用代理处理的子任务
- **工具使用代理**：使用 MCP 将 LLM 连接到数据库代理、计算代理等
- **实时聊天界面**：构建支持流式响应的响应式聊天应用

### 教育与培训

- **AI 教育**：创建展示代理协作的教育系统
- **模拟环境**：构建多个代理交互的模拟环境
- **教育工作流**：设计带反馈循环的分步学习流程

## 🛠️ 实际应用示例

查看 [`examples/`](https://github.com/themanojdesai/python-a2a/tree/main/examples) 目录中的实际应用示例，包括：

- 多代理客户支持系统
- 带工具访问的 LLM 驱动研究助手
- 实时流式传输实现
- LangChain 集成示例
- 各种工具的 MCP 服务器实现
- 工作流协调示例
- 代理网络管理

## 🔄 相关项目

AI 代理和互操作性领域的相关项目：

- [**Google A2A**](https://github.com/google/A2A) - 官方 Google A2A 协议规范
- [**LangChain**](https://github.com/langchain-ai/langchain) - 构建 LLM 应用的框架
- [**AutoGen**](https://github.com/microsoft/autogen) - Microsoft 的多代理对话框架
- [**CrewAI**](https://github.com/joaomdmoura/crewAI) - 角色扮演代理的协调框架
- [**MCP**](https://github.com/contextco/mcp) - 工具使用代理的 Model Context Protocol

## 👥 贡献者

感谢所有贡献者！

<a href="https://github.com/themanojdesai/python-a2a/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=themanojdesai/python-a2a" />
</a>

想贡献？查看我们的 [贡献指南](https://python-a2a.readthedocs.io/en/latest/contributing.html)。

## 🤝 社区与支持

- **[GitHub Issues](https://github.com/themanojdesai/python-a2a/issues)**：报告错误或请求功能
- **[GitHub Discussions](https://github.com/themanojdesai/python-a2a/discussions)**：提问和分享想法
- **[贡献指南](https://python-a2a.readthedocs.io/en/latest/contributing.html)**：学习如何为项目做贡献
- **[ReadTheDocs](https://python-a2a.readthedocs.io/en/latest/)**：访问我们的文档网站

## 📝 引用该项目

如果您在研究或学术工作中使用 Python A2A，请引用如下：

```
@software{desai2025pythona2a,
  author = {Desai, Manoj},
  title = {Python A2A: A Comprehensive Implementation of the Agent-to-Agent Protocol},
  url = {https://github.com/themanojdesai/python-a2a},
  version = {0.5.0},
  year = {2025},
}
```

## ⭐ 在 GitHub 上为该项目点赞

如果您发现这个库有用，请考虑在 GitHub 上为该项目点赞！这有助于他人发现该项目并激励进一步开发。

[![GitHub Repo stars](https://img.shields.io/github/stars/themanojdesai/python-a2a?style=social)](https://github.com/themanojdesai/python-a2a/stargazers)

### 点赞历史

[![Star History Chart](https://api.star-history.com/svg?repos=themanojdesai/python-a2a&type=Date)](https://star-history.com/#themanojdesai/python-a2a&Date)

## 🙏 致谢

- [Google A2A 团队](https://github.com/google/A2A) 为创建 A2A 协议
- [Contextual AI 团队](https://contextual.ai/) 为 Model Context Protocol
- [LangChain 团队](https://github.com/langchain-ai) 为强大的 LLM 框架
- 所有 [贡献者](https://github.com/themanojdesai/python-a2a/graphs/contributors) 为他们的宝贵输入

## 👨‍💻 作者

**Manoj Desai**

- GitHub: [themanojdesai](https://github.com/themanojdesai)
- LinkedIn: [themanojdesai](https://www.linkedin.com/in/themanojdesai/)
- Medium: [@the_manoj_desai](https://medium.com/@the_manoj_desai)

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

---

由 [Manoj Desai](https://github.com/themanojdesai) 用心制作
