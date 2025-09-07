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

**Google Agent-to-Agent (A2A) 協議的官方 Python 實現，整合 Model Context Protocol (MCP)**

</div>

## 🌟 概述

Python A2A 是一個全面且適用於生產環境的庫，用於實現 Google 的 [Agent-to-Agent (A2A) 協議](https://google.github.io/A2A/)，並完全支持 [Model Context Protocol (MCP)](https://contextual.ai/introducing-mcp/)。它提供了構建可相互操作的 AI 代理生態系統所需的所有功能，這些代理可以無縫協作以解決複雜問題。

A2A 協議爲 AI 代理之間的交流建立了標準通信格式，而 MCP 通過提供標準化的方法擴展了這一功能，使代理能夠訪問外部工具和數據來源。Python A2A 通過直觀的 API 使這些協議易於使用，開發者可以使用這些 API 構建複雜的多代理系統。

## 📋 v0.5.X 新增功能

- **代理發現**：內建代理註冊表和發現功能，完全兼容 Google A2A 協議
- **LangChain 整合**：與 LangChain 的工具和代理無縫整合
- **擴展的工具生態系統**：在任何代理中使用 LangChain 和 MCP 工具
- **增強的代理互操作性**：在 A2A 代理和 LangChain 代理之間進行轉換
- **混合工作流引擎**：構建結合兩種生態系統的複雜工作流
- **簡化代理開發**：即時訪問數千個預構建工具
- **高級流架構**：強化的 Server-Sent Events (SSE) 流、更好的偵錯處理和強大的恢復機制
- **基於任務的流**：新的 `tasks_send_subscribe` 方法用於實時流式任務更新
- **流式數據塊 API**：改進的 `StreamingChunk` 類用於結構化流式數據處理
- **多端點支持**：在多個流式端點之間自動發現和恢復

## 📋 v0.4.X 新增功能

- **代理網絡系統**：使用新的 `AgentNetwork` 類管理和發現多個代理
- **實時流式處理**：使用 `StreamingClient` 實現響應式 UI 的流式響應
- **工作流引擎**：使用新的流暢 API 定義複雜多代理工作流，支持條件分歧和並行處理
- **AI 路由器**：使用 `AIAgentRouter` 自動將查詢路由到最合適的代理
- **命令行界面**：通過新的 CLI 工具從終端控制代理
- **增強的異步支持**：在整個庫中改進了 async/await 支援
- **新的連接選項**：改進了代理通信的錯誤處理和重試邏輯

## ✨ 爲什麼選擇 Python A2A？

- **完整實現**：完全實現官方 A2A 規格，無任何妥協
- **代理發現**：內置代理註冊表和發現功能，用於構建代理生態系統
- **MCP 集成**：對 Model Context Protocol 的一流支持，實現強大的工具使用代理
- **企業級就緒**：爲生產環境構建，具有強大的錯誤處理和驗證功能
- **框架無關**：與任何 Python 框架兼容（Flask、FastAPI、Django 等）
- **LLM 提供商靈活性**：原生集成 OpenAI、Anthropic、AWS Bedrock 等
- **最小依賴**：核心功能僅依賴 `requests` 庫
- **卓越的開發者體驗**：全面的文檔、類型提示和示例

## 📦 安装

### 使用 pip（傳統方式）

安裝包含所有依賴項的基礎程式庫：

```bash
pip install python-a2a  # 包含 LangChain、MCP 和其他整合
```

或根據需求安裝特定元件：

```bash
# 安装 Flask 伺服器
pip install "python-a2a[server]"

# 安装 OpenAI 整合庫
pip install "python-a2a[openai]"

# 安装 Anthropic Claude 整合庫
pip install "python-a2a[anthropic]"

# 安装 AWS-Bedrock 整合庫
pip install "python-a2a[bedrock]"

# 安装 MCP 程式庫（Model Context Protocol）
pip install "python-a2a[mcp]"

# 安裝所有可選依賴程式庫
pip install "python-a2a[all]"
```

### 使用 UV（推薦）

[UV](https://github.com/astral-sh/uv) 是一個近代的 Python 程式庫管理工具，比 pip 更快更可靠。使用 UV 安裝：

```bash
# 如果尚未安裝 UV，請先安裝
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安裝基礎程式庫
uv install python-a2a
```

### 開發安裝

開發環境推薦使用 UV 以獲得更佳效能：

```bash
# 拷貝程式庫
git clone https://github.com/themanojdesai/python-a2a.git
cd python-a2a

# 創建虛擬環境並安裝開發依賴程式庫
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

> 💡 **提示**：點擊代碼區塊可複製到剪貼簿

## 🚀 快速入門範例

### 1. 創建帶有技能的簡易 A2A 代理

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

### 2. 構築包含多個代理的代理網路

```python
from python_a2a import AgentNetwork, A2AClient, AIAgentRouter

# 構築代理網路
network = AgentNetwork(name="Travel Assistant Network")

# 添加代理到網路
network.add("weather", "http://localhost:5001")
network.add("hotels", "http://localhost:5002")
network.add("attractions", "http://localhost:5003")

# 創立路由器並智能地將查詢定位到最佳代理
router = AIAgentRouter(
    llm_client=A2AClient("http://localhost:5000/openai"),  # 用於路由決策的 LLM
    agent_network=network
)

# 將查詢路由到適當的代理
agent_name, confidence = router.route_query("What's the weather like in Paris?")
print(f"Routing to {agent_name} with {confidence:.2f} confidence")

# 獲取選定的代理並發問
agent = network.get_agent(agent_name)
response = agent.ask("What's the weather like in Paris?")
print(f"Response: {response}")

# 列出所有可用代理
print("\nAvailable Agents:")
for agent_info in network.list_agents():
    print(f"- {agent_info['name']}: {agent_info['description']}")
```

### 即時流式處理

通過全方位的流式支持從代理得到即時響應：

```python
import asyncio
from python_a2a import StreamingClient, Message, TextContent, MessageRole

async def main():
    client = StreamingClient("http://localhost:5000")
    
    # 創立帶有必備 role 參數的訊息
    message = Message(
        content=TextContent(text="Tell me about A2A streaming"),
        role=MessageRole.USER
    )
    
    # 流式處理響應並即時處理數據區塊
    try:
        async for chunk in client.stream_response(message):
            # 處理不同格式的數據區塊（串列或字典）
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

查詢 `examples/streaming/` 目錄中的完整流式範例：

- **basic_streaming.py**：最小化流式實做（從這裡開始！）
- **01_basic_streaming.py**：流式基礎的全方位介紹
- **02_advanced_streaming.py**：使用不同分類策略的高級流式處理
- **03_streaming_llm_integration.py**：將流式處理與 LLM 提供商整合
- **04_task_based_streaming.py**：基於任務的流式處理與進度跟蹤
- **05_streaming_ui_integration.py**：流式 UI 整合（CLI 和 Web）
- **06_distributed_streaming.py**：分散式流式架構

### 3. 工作流引擎

新的工作流引擎允許您定義複雜代理交互：

```python
from python_a2a import AgentNetwork, Flow
import asyncio

async def main():
    # 設置代理網路
    network = AgentNetwork()
    network.add("research", "http://localhost:5001")
    network.add("summarizer", "http://localhost:5002")
    network.add("factchecker", "http://localhost:5003")
    
    # 定義研究報告生成工作流
    flow = Flow(agent_network=network, name="Research Report Workflow")
    
    # 首先收集初始研究
    flow.ask("research", "Research the latest developments in {topic}")
    
    # 然後並行處理結果
    parallel_results = (flow.parallel()
        # 分支 1：創建摘要
        .ask("summarizer", "Summarize this research: {latest_result}")
        # 分支 2：驗證關鍵事實
        .branch()
        .ask("factchecker", "Verify these key facts: {latest_result}")
        # 結束並行處理並收集結果
        .end_parallel(max_concurrency=2))
    
    # 根據驗證結果提取見解
    flow.execute_function(
        lambda results, context: f"Summary: {results['1']}\nVerified Facts: {results['2']}",
        parallel_results
    )
    
    # 執行工作流
    result = await flow.run({
        "topic": "quantum computing advancements in the last year"
    })
    
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

### 4. AI 驅動的路由器

智能路由以選擇每個查詢的最佳代理：

```python
from python_a2a import AgentNetwork, AIAgentRouter, A2AClient
import asyncio

async def main():
    # 創建帶有專用代理的網路
    network = AgentNetwork()
    network.add("math", "http://localhost:5001")
    network.add("history", "http://localhost:5002")
    network.add("science", "http://localhost:5003")
    network.add("literature", "http://localhost:5004")
    
    # 創立使用 LLM 進行決策的路由器
    router = AIAgentRouter(
        llm_client=A2AClient("http://localhost:5000/openai"),
        agent_network=network
    )
    
    # 要路由的範例查詢
    queries = [
        "What is the formula for the area of a circle?",
        "Who wrote The Great Gatsby?",
        "When did World War II end?",
        "How does photosynthesis work?",
        "What are Newton's laws of motion?"
    ]
    
    # 將每個查詢路由到最佳代理
    for query in queries:
        agent_name, confidence = router.route_query(query)
        agent = network.get_agent(agent_name)
        
        print(f"Query: {query}")
        print(f"Routed to: {agent_name} (confidence: {confidence:.2f})")
        
        # 從選定代理獲取響應
        response = agent.ask(query)
        print(f"Response: {response[:100]}...\n")

if __name__ == "__main__":
    asyncio.run(main())
```

### 5. 定義包含多個代理的複雜工作流

```python
from python_a2a import AgentNetwork, Flow, AIAgentRouter
import asyncio

async def main():
    # 創建代理網路
    network = AgentNetwork()
    network.add("weather", "http://localhost:5001")
    network.add("recommendations", "http://localhost:5002")
    network.add("booking", "http://localhost:5003")
    
    # 創立路由器
    router = AIAgentRouter(
        llm_client=network.get_agent("weather"),  # 使用一個代理作爲 LLM 進行路由
        agent_network=network
    )
    
    # 定義帶有條件邏輯的工作流
    flow = Flow(agent_network=network, router=router, name="Travel Planning Workflow")
    
    # 首先獲取天氣
    flow.ask("weather", "What's the weather in {destination}?")
    
    # 根據天氣條件分支
    flow.if_contains("sunny")
    
    # 如果放晴，推薦戶外活動
    flow.ask("recommendations", "Recommend outdoor activities in {destination}")
    
    # 結束條件並添加 else 分支
    flow.else_branch()
    
    # 如果不放晴，推薦室內活動
    flow.ask("recommendations", "Recommend indoor activities in {destination}")
    
    # 結束 if-else 區塊
    flow.end_if()
    
    # 添加並行處理步驟
    (flow.parallel()
        .ask("booking", "Find hotels in {destination}")
        .branch()
        .ask("booking", "Find restaurants in {destination}")
        .end_parallel())
    
    # 使用初始上下文執行工作流
    result = await flow.run({
        "destination": "Paris",
        "travel_dates": "June 12-20"
    })
    
    print("Workflow result:")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

### 6. 使用終端機界面

```bash
# 向代理發送消息
a2a send http://localhost:5000 "What is artificial intelligence?"

# 即時流式響應
a2a stream http://localhost:5000 "Generate a step-by-step tutorial for making pasta"

# 啓動 OpenAI 驅動的 A2A 伺服器
a2a openai --model gpt-4 --system-prompt "You are a helpful coding assistant"

# 啓動 Anthropic 驅動的 A2A 伺服器
a2a anthropic --model claude-3-opus-20240229 --system-prompt "You are a friendly AI teacher"

# 啓動帶有工具的 MCP 伺服器
a2a mcp-serve --name "Data Analysis MCP" --port 5001 --script analysis_tools.py

# 啓動開啟 MCP 的 A2A 代理
a2a mcp-agent --servers data=http://localhost:5001 calc=http://localhost:5002

# 直接使用 MCP 工具
a2a mcp-call http://localhost:5001 analyze_csv --params file=data.csv columns=price,date

# 管理代理網路
a2a network --add weather=http://localhost:5001 travel=http://localhost:5002 --save network.json

# 從指令碼執行工作流
a2a workflow --script research_workflow.py --context initial_data.json
```

## 🔄 LangChain 整合（v0.5.X 新增）

Python A2A 包含內建的 LangChain 整合，使您可以輕鬆結合兩種生態系統的最佳功能：

### 1. 將 MCP 工具轉換爲 LangChain

```python
from python_a2a.mcp import FastMCP, text_response
from python_a2a.langchain import to_langchain_tool

# 創立帶有工具的 MCP 伺服器
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

# 啓動伺服器
import threading, time
def run_server(server, port):
    server.run(host="0.0.0.0", port=port)
server_thread = threading.Thread(target=run_server, args=(mcp_server, 5000), daemon=True)
server_thread.start()
time.sleep(2)  # 允許伺服器啓動

# 將 MCP 工具轉換爲 LangChain
calculator_tool = to_langchain_tool("http://localhost:5000", "calculator")

# 在 LangChain 中使用工具
result = calculator_tool.run("5 * 9 + 3")
print(f"Result: {result}")
```

### 2. 將 LangChain 工具轉換爲 MCP 伺服器

```python
from langchain.tools import Tool
from langchain_core.tools import BaseTool
from python_a2a.langchain import to_mcp_server

# 創建 LangChain 工具
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

# 轉換爲 MCP 伺服器
mcp_server = to_mcp_server(calculator_tool)

# 運行伺服器
mcp_server.run(port=5000)
```

### 3. 將 LangChain 組件轉換爲 A2A 伺服器

```python
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from python_a2a import A2AClient, run_server
from python_a2a.langchain import to_a2a_server

# 創建 LangChain LLM
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# 轉換爲 A2A 伺服器
llm_server = to_a2a_server(llm)

# 創建提示詞的鏈
template = "You are a helpful travel guide.\n\nQuestion: {query}\n\nAnswer:"
prompt = PromptTemplate.from_template(template)
travel_chain = prompt | llm | StrOutputParser()

# 轉換爲 A2A 伺服器
travel_server = to_a2a_server(travel_chain)

# 在執行緒中運行伺服器
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

# 測試伺服器
llm_client = A2AClient("http://localhost:5001")
travel_client = A2AClient("http://localhost:5002")

llm_result = llm_client.ask("What is the capital of France?")
travel_result = travel_client.ask('{"query": "What are some must-see attractions in Paris?"}')
```

LangChain 會自動作爲依賴項安裝，因此一切開箱即用：

```bash
pip install python-a2a
# 完成！LangChain 會自動包含
```

## 🧩 核心功能

### 代理網路

Python A2A 現在包含一個強大的代理管理系統：

```python
from python_a2a import AgentNetwork, A2AClient

# 創立代理網路
network = AgentNetwork(name="Medical Assistant Network")

# 以不同方式添加代理
network.add("diagnosis", "http://localhost:5001")  # 從 URL 添加
network.add("medications", A2AClient("http://localhost:5002"))  # 從客戶端實例添加

# 從 URL 列表發現代理
discovered_count = network.discover_agents([
    "http://localhost:5003",
    "http://localhost:5004",
    "http://localhost:5005"
])
print(f"Discovered {discovered_count} new agents")

# 列出網路中的所有代理
for agent_info in network.list_agents():
    print(f"Agent: {agent_info['name']}")
    print(f"URL: {agent_info['url']}")
    if 'description' in agent_info:
        print(f"Description: {agent_info['description']}")
    print()

# 獲取特定代理
agent = network.get_agent("diagnosis")
response = agent.ask("What are the symptoms of the flu?")
```

### 7. 代理發現和註冊表

```python
from python_a2a import AgentCard, A2AServer, run_server
from python_a2a.discovery import AgentRegistry, run_registry, enable_discovery, DiscoveryClient
import threading
import time

# 創建註冊表伺服器
registry = AgentRegistry(
    name="A2A Registry Server",
    description="Central registry for agent discovery"
)

# 在執行緒中運行註冊表
registry_port = 8000
thread = threading.Thread(
    target=lambda: run_registry(registry, host="0.0.0.0", port=registry_port),
    daemon=True
)
thread.start()
time.sleep(1)  # 等待註冊表啓動

# 創建範例代理
agent_card = AgentCard(
    name="Weather Agent",
    description="Provides weather information",
    url="http://localhost:8001",
    version="1.0.0",
    capabilities={
        "weather_forecasting": True,
        "google_a2a_compatible": True  # 啓用 Google A2A 兼容性
    }
)
agent = A2AServer(agent_card=agent_card)

# 啓用發現 - 這會向註冊表註冊
registry_url = f"http://localhost:{registry_port}"
discovery_client = enable_discovery(agent, registry_url=registry_url)

# 在單線程執行緒中運行代理
agent_thread = threading.Thread(
    target=lambda: run_server(agent, host="0.0.0.0", port=8001),
    daemon=True
)
agent_thread.start()
time.sleep(1)  # 等待代理啓動

# 創立用於發現代理的客戶端
client = DiscoveryClient(agent_card=None)  # 僅發現不需要代理卡
client.add_registry(registry_url)

# 發現所有代理
agents = client.discover()
print(f"Discovered {len(agents)} agents:")
for agent in agents:
    print(f"- {agent.name} at {agent.url}")
    print(f"  Capabilities: {agent.capabilities}")
```

## 📖 架構與設計原則

Python A2A 基於三個核心設計原則：

1. **協議優先**：嚴格遵守 A2A 和 MCP 協議規範以實現最大相互操作性
2. **模塊化**：所有組件均可組合和替換
3. **漸進增強**：從簡單開始，僅在需要時增加複雜性

架構包含八個主要組件：

- **Models**：表示 A2A 消息、任務和代理卡的數據結構
- **Client**：用於向 A2A 代理發送消息和管理代理網絡的組件
- **Server**：用於構建 A2A 兼容代理的組件
- **Discovery**：代理生態系統的註冊表和發現機制
- **MCP**：實現 Model Context Protocol 服務器和客戶端的工具
- **LangChain**：LangChain 整合的橋接組件
- **Workflow**：用於協調複雜代理交互的工作流引擎
- **Utils**：常用任務的輔助函數
- **CLI**：與代理交互的命令行界面

## 🗺️ 實用例

Python A2A 可用於構建各種 AI 系統：

### 研究與開發

- **實驗框架**：在保持相同代理埠的同時輕鬆替換不同的 LLM 後端
- **基準套件**：在標準化任務上比較不同代理實現的性能
- **流式研究助手**：使用流式處理創建響應式研究工具

### 企業系統

- **AI 協調**：使用代理網路協調不同部門的多個 AI 代理
- **遺留系統集成**：通過 A2A 埠包裝遺留系統以實現 AI 訪問
- **複雜工作流**：使用多代理工作流和條件分支創建複雜業務流程
- **Utils**：常用任務的輔助函數
- **CLI**：與代理交互的命令行界面

### 面向客戶的應用

- **多階段助手**：將複雜用戶查詢分解爲由專用代理處理的子任務
- **工具使用代理**：使用 MCP 將 LLM 連接到數據庫代理、計算代理等
- **實時聊天界面**：構建支持流式響應的響應式聊天應用

### 教育與培訓

- **AI 教育**：創建展示代理協作的教育系統
- **模擬環境**：構建多個代理交互的模擬環境
- **教育工作流**：設計帶反饋循環的分步學習流程

## 🛠️ 實際應用範例

查看 [`examples/`](https://github.com/themanojdesai/python-a2a/tree/main/examples) 目錄中的實際應用範例，包括：

- 多代理客戶支持系統
- 帶工具訪問的 LLM 驅動研究助手
- 實時流式傳輸實現
- LangChain 整合範例
- 各種工具的 MCP 伺服器實做
- 工作流協調範例
- 代理網路管理

## 🔄 相關專案

AI 代理和互操作性領域的相關專案：

- [**Google A2A**](https://github.com/google/A2A) - 官方 Google A2A 協議規範
- [**LangChain**](https://github.com/langchain-ai/langchain) - 構建 LLM 應用的框架
- [**AutoGen**](https://github.com/microsoft/autogen) - Microsoft 的多代理對話框架
- [**CrewAI**](https://github.com/joaomdmoura/crewAI) - 角色扮演代理的協調框架
- [**MCP**](https://github.com/contextco/mcp) - 工具使用代理的 Model Context Protocol

## 👥 貢獻者

感謝所有貢獻者！

<a href="https://github.com/themanojdesai/python-a2a/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=themanojdesai/python-a2a" />
</a>

想貢獻？查看我們的 [貢獻指南](https://python-a2a.readthedocs.io/en/latest/contributing.html)。

## 🤝 社群與支持

- **[GitHub Issues](https://github.com/themanojdesai/python-a2a/issues)**：報告錯誤或請求功能
- **[GitHub Discussions](https://github.com/themanojdesai/python-a2a/discussions)**：提問和分享想法
- **[貢獻指南](https://python-a2a.readthedocs.io/en/latest/contributing.html)**：學習如何爲專案做貢獻
- **[ReadTheDocs](https://python-a2a.readthedocs.io/en/latest/)**：訪問我們的文檔網站

## 📝 引用該專案

如果您在研究或學術工作中使用 Python A2A，請引用如下：

```
@software{desai2025pythona2a,
  author = {Desai, Manoj},
  title = {Python A2A: A Comprehensive Implementation of the Agent-to-Agent Protocol},
  url = {https://github.com/themanojdesai/python-a2a},
  version = {0.5.0},
  year = {2025},
}
```

## ⭐ 在 GitHub 上爲該專案點讚

如果您發現這個程式庫有用，請考慮在 GitHub 上爲該專案點讚！這有助於他人發現該專案並激勵進一步開發。

[![GitHub Repo stars](https://img.shields.io/github/stars/themanojdesai/python-a2a?style=social)](https://github.com/themanojdesai/python-a2a/stargazers)

### 點讚歷史

[![Star History Chart](https://api.star-history.com/svg?repos=themanojdesai/python-a2a&type=Date)](https://star-history.com/#themanojdesai/python-a2a&Date)

## 🙏 致謝

- [Google A2A 團隊](https://github.com/google/A2A) 爲創建 A2A 協議
- [Contextual AI 團隊](https://contextual.ai/) 爲 Model Context Protocol
- [LangChain 團隊](https://github.com/langchain-ai) 爲强大的 LLM 框架
- 所有 [貢獻者](https://github.com/themanojdesai/python-a2a/graphs/contributors) 爲他們的寶貴努力

## 👨‍💻 作者

**Manoj Desai**

- GitHub: [themanojdesai](https://github.com/themanojdesai)
- LinkedIn: [themanojdesai](https://www.linkedin.com/in/themanojdesai/)
- Medium: [@the_manoj_desai](https://medium.com/@the_manoj_desai)

## 📄 認證

本專案採用 MIT 認證 - 詳見 [LICENSE](LICENSE) 文件。

---

由 [Manoj Desai](https://github.com/themanojdesai) 用心製作
