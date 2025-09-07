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
  

**Google Agent-to-Agent (A2A) プロトコルの公式 Python 実装、Model Context Protocol (MCP) 統合**

</div>

## 🌟 概要

Python A2A は、Google の [Agent-to-Agent (A2A) プロトコル](https://google.github.io/A2A/) の包括的で本番環境対応のライブラリであり、[Model Context Protocol (MCP)](https://contextual.ai/introducing-mcp/) との完全なサポートを提供します。このプロトコルは、複雑な問題を解決するために AI エージェントがシームレスに協力できるようにするためのすべての機能を提供します。

A2A プロトコルは、AI エージェント間の相互作用のための標準的な通信形式を確立し、MCP はエージェントが外部ツールやデータソースにアクセスするための標準化された方法を提供することで、この機能を拡張します。Python A2A は直感的な API を通じてこれらのプロトコルを簡単に使用できるようにし、これらの API を使用して複雑なマルチエージェントシステムを構築できます。

## 📋 v0.5.X での新機能

- **エージェント発見**: Google A2A プロトコルとの完全な互換性を持つエージェントレジストリおよび発見の組み込みサポート
- **LangChain 統合**: LangChain のツールおよびエージェントとのシームレスな統合
- **拡張されたツールエコシステム**: 任意のエージェントで LangChain および MCP のツールを使用可能
- **強化されたエージェント相互運用性**: A2A エージェントと LangChain エージェントの変換
- **混合ワークフロー エンジン**: 両方のエコシステムを組み合わせたワークフローの構築
- **簡素化されたエージェント開発**: 即座に数千の事前構築済みツールにアクセス可能
- **高度なストリーミングアーキテクチャ**: サーバーセンテッドイベント (SSE)、より良いエラー処理、堅牢なフェールオーバー機構を備えた強化されたストリーミング
- **タスクベースのストリーミング**: 実時間でタスク更新をストリームする新しい `tasks_send_subscribe` メソッド
- **ストリーミングチャンク API**: 構造化ストリーミングデータ用の `StreamingChunk` クラスで改善されたチャンク処理
- **マルチエンドポイントサポート**: 複数のストリーミングエンドポイント間の自動発見およびフェールオーバー

## 📋 v0.4.X での新機能

- **エージェントネットワークシステム**: 新しい `AgentNetwork` クラスで複数のエージェントを管理および発見
- **リアルタイムストリーミング**: `StreamingClient` を使用してレスポンシブな UI でストリーミングレスポンスを実装
- **ワークフロー エンジン**: 条件分岐および並列実行を備えた新しいフuent API を使用して複雑なマルチエージェントワークフローを定義
- **AI パワード ルータ**: `AIAgentRouter` を使用して最も適切なエージェントにクエリを自動ルーティング
- **コマンドライン インターフェース**: 新しい CLI ツールでターミナルからエージェントを制御
- **強化された非同期サポート**: ライブラリ全体でより良い async/await サポート
- **新しい接続オプション**: より堅牢なエージェント通信のための改善されたエラー処理およびリトライロジック

## ✨ なぜ Python A2A を選ぶのか

- **完全な実装**: 公式 A2A 仕様を完全に実装し、妥協なし
- **エージェント発見**: エージェントエコシステムを構築するための組み込みエージェントレジストリおよび発見
- **MCP 統合**: 高度なツール使用エージェントのための Model Context Protocol のファーストクラスサポート
- **企業向け**: 本番環境用に構築され、堅牢なエラー処理および検証
- **フレームワーク非依存**: 任意の Python フレームワーク (Flask、FastAPI、Django など) で動作
- **LLM プロバイダの柔軟性**: OpenAI、Anthropic、AWS Bedrock などとのネイティブ統合
- **最小限の依存関係**: コア機能には `requests` ライブラリのみが必要
- **優れた開発者体験**: 包括的なドキュメント、型ヒント、例

## 📦 インストール

### pip を使用 (従来型)

すべての依存関係を含む基本パッケージをインストール:

```bash
pip install python-a2a  # LangChain、MCP および他の統合を含む
```

または、必要に応じて特定のコンポーネントをインストール:

```bash
# Flask ベースのサーバー対応
pip install "python-a2a[server]"

# OpenAI 統合
pip install "python-a2a[openai]"

# Anthropic Claude 統合
pip install "python-a2a[anthropic]"

# AWS-Bedrock 統合
pip install "python-a2a[bedrock]"

# MCP 統合 (Model Context Protocol)
pip install "python-a2a[mcp]"

# すべてのオプション依存関係
pip install "python-a2a[all]"
```

### UV を使用 (推奨)

[UV](https://github.com/astral-sh/uv) は pip よりも高速で信頼性の高い現代的な Python パッケージ管理ツールです。UV でインストールするには:

```bash
# UV がインストールされていない場合はインストール
curl -LsSf https://astral.sh/uv/install.sh | sh

# 基本パッケージをインストール
uv install python-a2a
```

### 開発インストール

開発用には UV が推奨されます:

```bash
# リポジトリをクローン
git clone https://github.com/themanojdesai/python-a2a.git
cd python-a2a

# 仮想環境を作成して開発依存関係をインストール
uv venv
source .venv/bin/activate  # Windows の場合は .venv\Scripts\activate
uv pip install -e ".[dev]"
```

> 💡 **ヒント**: コードブロックをクリックしてクリップボードにコピーできます。

## 🚀 クイックスタート例

### 1. スキル付きシンプルな A2A エージェントの作成

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
        # モック実装
        return f"It's sunny and 75°F in {location}"
    
    def handle_task(self, task):
        # メッセージから場所を抽出
        message_data = task.message or {}
        content = message_data.get("content", {})
        text = content.get("text", "") if isinstance(content, dict) else ""
        
        if "weather" in text.lower() and "in" in text.lower():
            location = text.split("in", 1)[1].strip().rstrip("?.")
            
            # 天気を取得して応答を作成
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

# サーバーを起動
if __name__ == "__main__":
    agent = WeatherAgent()
    run_server(agent, port=5000)
```

### 2. 複数のエージェントでエージェントネットワークの構築

```python
from python_a2a import AgentNetwork, A2AClient, AIAgentRouter

# エージェントネットワークの作成
network = AgentNetwork(name="Travel Assistant Network")

# ネットワークにエージェントを追加
network.add("weather", "http://localhost:5001")
network.add("hotels", "http://localhost:5002")
network.add("attractions", "http://localhost:5003")

# クエリを最適なエージェントにルーティングするルータの作成
router = AIAgentRouter(
    llm_client=A2AClient("http://localhost:5000/openai"),  # ルーティング決定用の LLM
    agent_network=network
)

# クエリを適切なエージェントにルーティング
agent_name, confidence = router.route_query("What's the weather like in Paris?")
print(f"{agent_name} に {confidence:.2f} の信頼度でルーティング")

# 選択されたエージェントに質問
agent = network.get_agent(agent_name)
response = agent.ask("What's the weather like in Paris?")
print(f"応答: {response}")

# 利用可能なエージェントを一覧表示
print("\n利用可能なエージェント:")
for agent_info in network.list_agents():
    print(f"- {agent_info['name']}: {agent_info['description']}")
```

### 実時間ストリーミング

エージェントから実時間の応答を取得する包括的なストリーミングサポート:

```python
import asyncio
from python_a2a import StreamingClient, Message, TextContent, MessageRole

async def main():
    client = StreamingClient("http://localhost:5000")
    
    # 必要な role パラメータを持つメッセージの作成
    message = Message(
        content=TextContent(text="Tell me about A2A streaming"),
        role=MessageRole.USER
    )
    
    # 応答をストリームしてリアルタイムでチャンクを処理
    try:
        async for chunk in client.stream_response(message):
            # 異なるチャンク形式 (文字列または辞書) を処理
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
        print(f"ストリーミングエラー: {e}")
```

`examples/streaming/` ディレクトリに完全なストリーミング例があります:

- **basic_streaming.py**: 最小限のストリーミング実装 (ここから始めましょう!)
- **01_basic_streaming.py**: ストリーミングの基本の包括的な導入
- **02_advanced_streaming.py**: 異なるチャンキング戦略を使用した高度なストリーミング
- **03_streaming_llm_integration.py**: LLM プロバイダとのストリーミング統合
- **04_task_based_streaming.py**: 進行状況追跡付きタスクベースのストリーミング
- **05_streaming_ui_integration.py**: ストリーミング UI 統合 (CLI および Web)
- **06_distributed_streaming.py**: 分散ストリーミングアーキテクチャ

### 3. ワークフロー エンジン

新しいワークフロー エンジンにより、複雑なエージェント相互作用を定義できます:

```python
from python_a2a import AgentNetwork, Flow
import asyncio

async def main():
    # エージェントネットワークの設定
    network = AgentNetwork()
    network.add("research", "http://localhost:5001")
    network.add("summarizer", "http://localhost:5002")
    network.add("factchecker", "http://localhost:5003")
    
    # 研究レポート生成のワークフローの定義
    flow = Flow(agent_network=network, name="Research Report Workflow")
    
    # 最初に初期研究を収集
    flow.ask("research", "Research the latest developments in {topic}")
    
    # 結果を並列処理
    parallel_results = (flow.parallel()
        # ブランチ 1: 要約を作成
        .ask("summarizer", "Summarize this research: {latest_result}")
        # ブランチ 2: 主な事実を検証
        .branch()
        .ask("factchecker", "Verify these key facts: {latest_result}")
        # 並列処理を終了して結果を収集
        .end_parallel(max_concurrency=2))
    
    # 検証結果に基づいてインサイトを抽出
    flow.execute_function(
        lambda results, context: f"Summary: {results['1']}\nVerified Facts: {results['2']}",
        parallel_results
    )
    
    # ワークフローの実行
    result = await flow.run({
        "topic": "quantum computing advancements in the last year"
    })
    
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

### 4. AI パワード ルータ

各クエリに最適なエージェントを選択するインテリジェント ルーティング:

```python
from python_a2a import AgentNetwork, AIAgentRouter, A2AClient
import asyncio

async def main():
    # 専門分野別のエージェントを持つネットワークの作成
    network = AgentNetwork()
    network.add("math", "http://localhost:5001")
    network.add("history", "http://localhost:5002")
    network.add("science", "http://localhost:5003")
    network.add("literature", "http://localhost:5004")
    
    # LLM を使用して意思決定を行うルータの作成
    router = AIAgentRouter(
        llm_client=A2AClient("http://localhost:5000/openai"),
        agent_network=network
    )
    
    # ルーティングするサンプルクエリ
    queries = [
        "What is the formula for the area of a circle?",
        "Who wrote The Great Gatsby?",
        "When did World War II end?",
        "How does photosynthesis work?",
        "What are Newton's laws of motion?"
    ]
    
    # 各クエリを最適なエージェントにルーティング
    for query in queries:
        agent_name, confidence = router.route_query(query)
        agent = network.get_agent(agent_name)
        
        print(f"クエリ: {query}")
        print(f"ルーティング先: {agent_name} (信頼度: {confidence:.2f})")
        
        # 選択されたエージェントから応答を取得
        response = agent.ask(query)
        print(f"応答: {response[:100]}...\n")

if __name__ == "__main__":
    asyncio.run(main())
```

### 5. 複数のエージェントで複雑なワークフローの定義

```python
from python_a2a import AgentNetwork, Flow, AIAgentRouter
import asyncio

async def main():
    # エージェントネットワークの作成
    network = AgentNetwork()
    network.add("weather", "http://localhost:5001")
    network.add("recommendations", "http://localhost:5002")
    network.add("booking", "http://localhost:5003")
    
    # ルータの作成
    router = AIAgentRouter(
        llm_client=network.get_agent("weather"),  # ルーティング用に 1 つのエージェントを LLM として使用
        agent_network=network
    )
    
    # 条件付きロジックを持つワークフローの定義
    flow = Flow(agent_network=network, router=router, name="Travel Planning Workflow")
    
    # 最初に天気を取得
    flow.ask("weather", "What's the weather in {destination}?")
    
    # 天気に基づいて条件分岐
    flow.if_contains("sunny")
    
    # 晴れていれば屋外アクティビティを推奨
    flow.ask("recommendations", "Recommend outdoor activities in {destination}")
    
    # 条件を終了して else ブランチを追加
    flow.else_branch()
    
    # 晴れていない場合は屋内アクティビティを推奨
    flow.ask("recommendations", "Recommend indoor activities in {destination}")
    
    # if-else ブロックを終了
    flow.end_if()
    
    # 並列処理ステップを追加
    (flow.parallel()
        .ask("booking", "Find hotels in {destination}")
        .branch()
        .ask("booking", "Find restaurants in {destination}")
        .end_parallel())
    
    # 初期コンテキストでワークフローを実行
    result = await flow.run({
        "destination": "Paris",
        "travel_dates": "June 12-20"
    })
    
    print("ワークフローの結果:")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

### 6. コマンドライン インターフェースの使用

```bash
# エージェントにメッセージを送信
a2a send http://localhost:5000 "What is artificial intelligence?"

# 実時間で応答をストリーム
a2a stream http://localhost:5000 "Generate a step-by-step tutorial for making pasta"

# OpenAI パワード A2A サーバーを起動
a2a openai --model gpt-4 --system-prompt "You are a helpful coding assistant"

# Anthropic パワード A2A サーバーを起動
a2a anthropic --model claude-3-opus-20240229 --system-prompt "You are a friendly AI teacher"

# ツール付き MCP サーバーを起動
a2a mcp-serve --name "Data Analysis MCP" --port 5001 --script analysis_tools.py

# MCP 対応 A2A エージェントを起動
a2a mcp-agent --servers data=http://localhost:5001 calc=http://localhost:5002

# MCP ツールを直接呼び出す
a2a mcp-call http://localhost:5001 analyze_csv --params file=data.csv columns=price,date

# エージェントネットワークを管理
a2a network --add weather=http://localhost:5001 travel=http://localhost:5002 --save network.json

# スクリプトからワークフローを実行
a2a workflow --script research_workflow.py --context initial_data.json
```

## 🔄 LangChain 統合 (v0.5.X で新規)

Python A2A には組み込みの LangChain 統合が含まれており、両方のエコシステムの最良部分を簡単に組み合わせることができます:

### 1. MCP ツールを LangChain に変換

```python
from python_a2a.mcp import FastMCP, text_response
from python_a2a.langchain import to_langchain_tool

# MCP サーバーにツールを作成
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

# サーバーを起動
import threading, time
def run_server(server, port):
    server.run(host="0.0.0.0", port=port)
server_thread = threading.Thread(target=run_server, args=(mcp_server, 5000), daemon=True)
server_thread.start()
time.sleep(2)  # サーバーの起動を待つ

# MCP ツールを LangChain に変換
calculator_tool = to_langchain_tool("http://localhost:5000", "calculator")

# LangChain でツールを使用
result = calculator_tool.run("5 * 9 + 3")
print(f"Result: {result}")
```

### 2. LangChain ツールを MCP サーバーに変換

```python
from langchain.tools import Tool
from langchain_core.tools import BaseTool
from python_a2a.langchain import to_mcp_server

# LangChain ツールを作成
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

# MCP サーバーに変換
mcp_server = to_mcp_server(calculator_tool)

# サーバーを起動
mcp_server.run(port=5000)
```

### 3. LangChain コンポーネントを A2A サーバーに変換

```python
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from python_a2a import A2AClient, run_server
from python_a2a.langchain import to_a2a_server

# LangChain LLM を作成
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# LLM を A2A サーバーに変換
llm_server = to_a2a_server(llm)

# 簡単なチェーンを作成
template = "You are a helpful travel guide.\n\nQuestion: {query}\n\nAnswer:"
prompt = PromptTemplate.from_template(template)
travel_chain = prompt | llm | StrOutputParser()

# チェーンを A2A サーバーに変換
travel_server = to_a2a_server(travel_chain)

# 背景スレッドでサーバーを実行
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

# サーバーをテスト
llm_client = A2AClient("http://localhost:5001")
travel_client = A2AClient("http://localhost:5002")

llm_result = llm_client.ask("What is the capital of France?")
travel_result = travel_client.ask('{"query": "What are some must-see attractions in Paris?"}')
```

### 4. A2A エージェントを LangChain エージェントに変換

```python
from python_a2a.langchain import to_langchain_agent

# A2A エージェントを LangChain エージェントに変換
langchain_agent = to_langchain_agent("http://localhost:5000")

# LangChain でエージェントを使用
result = langchain_agent.invoke("What are some famous landmarks in Paris?")
print(result.get('output', ''))

# LangChain パイプラインで使用
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm = ChatOpenAI(temperature=0)
prompt = ChatPromptTemplate.from_template(
    "Generate a specific, detailed travel question about {destination}."
)

# 変換されたエージェントを含むパイプラインの作成
chain = (
    prompt |
    llm |
    StrOutputParser() |
    langchain_agent |
    (lambda x: f"Travel Info: {x.get('output', '')}")
)

result = chain.invoke({"destination": "Japan"})
print(result)
```

LangChain は python-a2a に自動的にインストールされるため、すべてがすぐに動作します:

```bash
pip install python-a2a
# それだけで完了です! LangChain は自動的に含まれます
```

## 🧩 コア機能

### エージェントネットワーク

Python A2A には、複数のエージェントを管理するための強力なシステムが含まれています:

```python
from python_a2a import AgentNetwork, A2AClient

# エージェントネットワークの作成
network = AgentNetwork(name="Medical Assistant Network")

# 異なる方法でエージェントを追加
network.add("diagnosis", "http://localhost:5001")  # URL から
network.add("medications", A2AClient("http://localhost:5002"))  # クライアントインスタンスから

# URL リストからエージェントを発見
discovered_count = network.discover_agents([
    "http://localhost:5003",
    "http://localhost:5004",
    "http://localhost:5005"
])
print(f"{discovered_count} 個の新しいエージェントを発見しました")

# ネットワーク内のすべてのエージェントを一覧表示
for agent_info in network.list_agents():
    print(f"エージェント: {agent_info['name']}")
    print(f"URL: {agent_info['url']}")
    if 'description' in agent_info:
        print(f"説明: {agent_info['description']}")
    print()

# 特定のエージェントを取得
agent = network.get_agent("diagnosis")
response = agent.ask("What are the symptoms of the flu?")
```

### 7. エージェント発見およびレジストリ

```python
from python_a2a import AgentCard, A2AServer, run_server
from python_a2a.discovery import AgentRegistry, run_registry, enable_discovery, DiscoveryClient
import threading
import time

# レジストリサーバーの作成
registry = AgentRegistry(
    name="A2A レジストリサーバー",
    description="エージェント発見のための中央レジストリ"
)

# レジストリを背景スレッドで実行
registry_port = 8000
thread = threading.Thread(
    target=lambda: run_registry(registry, host="0.0.0.0", port=registry_port),
    daemon=True
)
thread.start()
time.sleep(1)  # レジストリの起動を待つ

# サンプルエージェントの作成
agent_card = AgentCard(
    name="Weather Agent",
    description="Provides weather information",
    url="http://localhost:8001",
    version="1.0.0",
    capabilities={
        "weather_forecasting": True,
        "google_a2a_compatible": True  # Google A2A 互換性を有効化
    }
)
agent = A2AServer(agent_card=agent_card)

# 発見を有効化 - これはレジストリに登録します
registry_url = f"http://localhost:{registry_port}"
discovery_client = enable_discovery(agent, registry_url=registry_url)

# 別スレッドでエージェントを実行
agent_thread = threading.Thread(
    target=lambda: run_server(agent, host="0.0.0.0", port=8001),
    daemon=True
)
agent_thread.start()
time.sleep(1)  # エージェントの起動を待つ

# エージェント発見用のクライアントの作成
client = DiscoveryClient(agent_card=None)  # 発見専用にはエージェントカードは必要ありません
client.add_registry(registry_url)

# すべてのエージェントを発見
agents = client.discover()
print(f"{len(agents)} 個のエージェントを発見しました:")
for agent in agents:
    print(f"- {agent.name} は {agent.url} にあります")
    print(f"  能力: {agent.capabilities}")
```

## 📖 アーキテクチャ & 設計原則

Python A2A は 3 つのコア設計原則に基づいて構築されています:

1. **プロトコル第一**: A2A および MCP プロトコル仕様に厳密に従って最大限の相互運用性を確保

2. **モジュール性**: すべてのコンポーネントは組み合わせ可能で置き換え可能に設計されています

3. **進化的強化**: 簡単に始め、必要に応じて複雑さを追加

アーキテクチャは 8 つの主要コンポーネントから構成されています:

- **モデル**: A2A メッセージ、タスク、エージェントカードを表すデータ構造
- **クライアント**: A2A エージェントにメッセージを送信し、エージェントネットワークを管理するコンポーネント
- **サーバー**: A2A 互換エージェントを構築するコンポーネント
- **発見**: エージェントエコシステムのレジストリおよび発見メカニズム
- **MCP**: Model Context Protocol サーバーおよびクライアントを実装するツール
- **LangChain**: LangChain 統合のためのブリッジコンポーネント
- **ワークフロー**: 複雑なエージェント相互作用をオーケストレーションするエンジン
- **ユーティリティ**: 一般的なタスク用のヘルパー関数
- **CLI**: エージェントと対話するためのコマンドラインインターフェース

## 🗺️ 用例

Python A2A は、さまざまな AI システムの構築に使用できます:

### 研究 & 開発

- **実験フレームワーク**: 同じエージェントインターフェースを維持しながら異なる LLM バックエンドを簡単に交換
- **ベンチマークスイート**: 標準化されたタスクで異なるエージェント実装のパフォーマンスを比較
- **ストリーミング研究アシスタント**: ストリーミングを使用して実時間の出力を持つ応答的な研究ツールを作成

### エンタープライズ システム

- **AI オーケストレーション**: エージェントネットワークを使用して異なる部門の AI エージェントを調整
- **レガシーシステム統合**: A2A インターフェースでレガシーシステムをラップして AI へのアクセスを提供
- **複雑なワークフロー**: マルチエージェントワークフローおよび条件分岐を使用した複雑なビジネスプロセスの作成

### カスタマーフレンドリーなアプリケーション

- **マルチステージ アシスタント**: 専門分野別のエージェントで複雑なユーザークエリをサブタスクに分割
- **ツール使用エージェント**: データベースエージェント、計算エージェントなどに LLM を接続する MCP を使用
- **リアルタイムチャットインターフェース**: ストリーミング応答サポートで応答的なチャットアプリケーションを構築

### 教育 & トレーニング

- **AI 教育**: エージェント協力のデモンストレーション用の教育システムの作成
- **シミュレーション環境**: 複数のエージェントが相互作用するシミュレーション環境の構築
- **教育ワークフロー**: フィードバックループを備えたステップバイステップの学習プロセスの設計

## 🛠️ 実世界の例

[`examples/`](https://github.com/themanojdesai/python-a2a/tree/main/examples) ディレクトリに実世界の例を確認してください。これには以下が含まれます:

- マルチエージェントカスタマーサポートシステム
- ツールアクセス付き LLM パワード研究アシスタント
- 実時間ストリーミング実装
- LangChain 統合例
- 各種ツール用 MCP サーバー実装
- ワークフロー オーケストレーション例
- エージェントネットワーク管理

## 🔄 関連プロジェクト

AI エージェントおよび相互運用性空間の関連プロジェクト:

- [**Google A2A**](https://github.com/google/A2A) - 公式 Google A2A プロトコル仕様
- [**LangChain**](https://github.com/langchain-ai/langchain) - LLM を使用したアプリケーション構築のためのフレームワーク
- [**AutoGen**](https://github.com/microsoft/autogen) - Microsoft のマルチエージェント会話フレームワーク
- [**CrewAI**](https://github.com/joaomdmoura/crewAI) - ロールプレイエージェントのオーケストレーション用フレームワーク
- [**MCP**](https://github.com/contextco/mcp) - ツール使用エージェントのための Model Context Protocol

## 👥 貢献者

すべての貢献者に感謝します!

<a href="https://github.com/themanojdesai/python-a2a/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=themanojdesai/python-a2a" />
</a>

貢献したい場合は、[contributing guide](https://python-a2a.readthedocs.io/en/latest/contributing.html) を確認してください。

## 🤝 コミュニティ & サポート

- **[GitHub Issues](https://github.com/themanojdesai/python-a2a/issues)**: バグを報告または機能をリクエスト
- **[GitHub Discussions](https://github.com/themanojdesai/python-a2a/discussions)**: 質問をしたりアイデアを共有したり
- **[Contributing Guide](https://python-a2a.readthedocs.io/en/latest/contributing.html)**: プロジェクトへの貢献方法を学ぶ
- **[ReadTheDocs](https://python-a2a.readthedocs.io/en/latest/)**: ドキュメンテーションサイトを訪問

## 📝 このプロジェクトの引用

Python A2A を研究または学術的な作業で使用する場合は、以下のように引用してください:

```
@software{desai2025pythona2a,
  author = {Desai, Manoj},
  title = {Python A2A: A Comprehensive Implementation of the Agent-to-Agent Protocol},
  url = {https://github.com/themanojdesai/python-a2a},
  version = {0.5.0},
  year = {2025},
}
```

## ⭐ このリポジトリをスター

このライブラリが役に立つ場合は、GitHub でスターを付けてください! 他の人がプロジェクトを発見しやすくし、さらなる開発を促進するのに役立ちます。

[![GitHub Repo stars](https://img.shields.io/github/stars/themanojdesai/python-a2a?style=social)](https://github.com/themanojdesai/python-a2a/stargazers)

### スター履歴

[![Star History Chart](https://api.star-history.com/svg?repos=themanojdesai/python-a2a&type=Date)](https://star-history.com/#themanojdesai/python-a2a&Date)

## 🙏 謝辞

- [Google A2A チーム](https://github.com/google/A2A) が A2A プロトコルを作成してくれたこと
- [Contextual AI チーム](https://contextual.ai/) が Model Context Protocol を作成してくれたこと
- [LangChain チーム](https://github.com/langchain-ai) が強力な LLM フレームワークを作成してくれたこと
- すべての [貢献者](https://github.com/themanojdesai/python-a2a/graphs/contributors) が貴重な入力をしてくれたこと

## 👨‍💻 著者

**Manoj Desai**

- GitHub: [themanojdesai](https://github.com/themanojdesai)
- LinkedIn: [themanojdesai](https://www.linkedin.com/in/themanojdesai/)
- Medium: [@the_manoj_desai](https://medium.com/@the_manoj_desai)

## 📄 ライセンス

このプロジェクトは MIT ライセンスの下でライセンスされています - [LICENSE](LICENSE) ファイルを参照して詳細を確認してください。

---

Manoj Desai によって ❤️ で作成
