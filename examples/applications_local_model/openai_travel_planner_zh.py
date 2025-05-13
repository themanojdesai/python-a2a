#!/usr/bin/env python
"""
OpenAI 旅行规划助手（中文版）

一个使用 OpenAI 和 A2A 构建的完整旅行规划系统。
此示例演示了如何构建实用的旅行规划器，结合 OpenAI 的能力与专用代理。

运行方式:
    export OPENAI_API_KEY=your_api_key
    python openai_travel_planner_zh.py

依赖安装:
    pip install "python-a2a[openai,server]"
"""

import sys
import time
import argparse
import socket
import multiprocessing
import re
import json



# 检查依赖项
try:
    import python_a2a
    import openai
    import flask
except ImportError as e:
    module_name = getattr(e, 'name', str(e))
    print(f"❌ 缺少依赖: {module_name}")
    print("请安装所需的包：")
    print("    pip install \"python-a2a[openai,server]\"")
    sys.exit(1)

# 导入所有必要的 A2A 组件
# 装饰器可能在主包中
from python_a2a import A2AServer, run_server, AgentCard, AgentSkill, TaskStatus, TaskState
from python_a2a import OpenAIA2AServer, A2AClient

# 尝试从主包获取装饰器
try:
    from python_a2a import skill, agent
except ImportError:
    # 如果不可用，则定义简化版本
    print("⚠️ 无法导入 skill 和 agent 装饰器，使用简化版本")
    
    def skill(name=None, description=None, tags=None, examples=None):
        """简化版技能装饰器"""
        def decorator(func):
            func._skill_info = {
                "name": name or func.__name__,
                "description": description or func.__doc__ or "",
                "tags": tags or [],
                "examples": examples or []
            }
            return func
        return decorator
    
    def agent(name=None, description=None, version=None, url=None):
        """简化版代理装饰器"""
        def decorator(cls):
            return cls
        return decorator

def find_available_port(start_port=5000, max_tries=10):
    """从指定端口开始查找可用端口"""
    for port in range(start_port, start_port + max_tries):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('localhost', port))
            sock.close()
            return port
        except OSError:
            continue
    
    return start_port + 100  # 返回一个较高的备用端口


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="OpenAI Travel Planner Example")
    parser.add_argument(
        "--port", type=int, default=None,
        help="Port for the Travel Planner (default: auto-select)"
    )
    parser.add_argument(
        "--no-test", action="store_true",
        help="Don't run test queries automatically"
    )
    return parser.parse_args()


class TravelKnowledgeBase:
    """补充 OpenAI 知识的旅行信息知识库"""
    
    def __init__(self):
        # 主要目的地的基本签证规则
        self.visa_rules = {
            "usa": "大多数国家需要旅游签证(B-2)。签证免签计划国家需要ESTA。",
            "uk": "许多国家需要标准访客签证。脱欧前欧盟公民享有免签待遇。",
            "eu": "许多非欧盟公民需要申根签证。180天内最多停留90天。",
            "japan": "许多国家享受最长90天的免签待遇。",
            "australia": "短途访问需要eVisitor或ETA。更长时间需要正式签证。",
            "canada": "免签外国公民飞往加拿大需要eTA。其他人需要签证。",
            "china": "几乎所有外国人入境前都需要签证。",
            "thailand": "许多国家享受30天免签。更长时间需要签证。",
            "uae": "许多国籍可落地签。其他人需要预先申请签证。",
            "singapore": "许多国家享受30-90天免签入境。"
        }
        
        # 旅行健康建议
        self.health_advisories = {
            "general": "出行前确保常规疫苗接种是最新的。",
            "tropical": "前往热带地区时考虑接种甲肝、伤寒和黄热病疫苗。",
            "malaria": "前往疟疾流行地区需服用抗疟药。",
            "covid": "检查每个目的地当前的新冠要求，包括检测和疫苗接种。",
            "water": "在许多发展中国家，请只饮用瓶装水或开水，并避免食用冰块。",
            "altitude": "前往高海拔地区时，留出时间适应环境以防止高山症。",
            "insurance": "出国旅行时应始终购买全面的旅行健康保险。"
        }
        
        # 一般旅行贴士
        self.travel_tips = [
            "制作重要文件如护照和身份证的电子版和纸质副本。",
            "在目的地国家注册你所在国家的大使馆或领事馆。",
            "出发前研究当地习俗和法律。",
            "学习目的地语言的一些基本短语。",
            "告知你的银行和信用卡公司你的旅行计划。",
            "打包一个包含基本急救用品的小急救箱以备紧急情况。",
            "使用国际通用的交通应用，如 Uber 或本地等效应用。",
            "考虑在当地购买SIM卡或国际数据套餐。",
            "检查目的地是否有任何安全问题或限制区域。",
            "研究针对游客的典型骗局。"
        ]
    
    def get_visa_info(self, country):
        """获取国家签证信息"""
        country = country.lower()
        # 尝试直接匹配
        if country in self.visa_rules:
            return self.visa_rules[country]
        
        # 尝试部分匹配
        for key, value in self.visa_rules.items():
            if key in country or country in key:
                return value
        
        return "请咨询目的地国家的大使馆或领事馆了解具体签证要求。"
    
    def get_health_advisory(self, region=None):
        """获取特定地区的健康建议"""
        if region and region.lower() in self.health_advisories:
            return self.health_advisories[region.lower()]
        
        # 返回一般建议
        return self.health_advisories["general"]
    
    def get_travel_tips(self, count=3):
        """获取随机旅行贴士"""
        import random
        return random.sample(self.travel_tips, min(count, len(self.travel_tips)))


def test_client(port):
    """对旅行规划器运行测试查询"""
    # 等待服务器启动
    time.sleep(3)
    
    print("\n🧪 正在测试旅行规划器...")
    client = A2AClient(f"http://localhost:{port}")
    
    # 测试查询
    test_queries = [
        "规划一个三天的东京之旅",
        "访问法国的签证要求是什么？",
        "为家庭伦敦度假提供建议"
    ]
    
    for query in test_queries:
        try:
            print(f"\n💬 查询: {query}")
            response = client.ask(query)
            print(f"✈️ 响应: {response}")
            time.sleep(1)
        except Exception as e:
            print(f"❌ 错误: {e}")
    
    print("\n✅ 测试完成！你的旅行规划器已准备就绪。")
    print(f"💻 服务运行地址: http://localhost:{port}")
    print("📝 可尝试提问如: '规划巴黎周末游'，'泰国的最佳旅行时间'，或'海滩度假需要带什么'")
    print("🛑 在服务器终端按 Ctrl+C 停止服务。")


def main():
    # 解析命令行参数
    args = parse_arguments()
    with open("config.json") as f:
        config = json.load(f)
    model_name = config["model_name"]
    base_url = config["base_url"]
    api_key = config["api_key"]

    # 如果未指定则自动选择端口
    if args.port is None:
        port = find_available_port()
        print(f"🔍 自动选择端口: {port}")
    else:
        port = args.port
        print(f"🔍 使用指定端口: {port}")
    
    print("\n✈️ OpenAI 旅行规划器 ✈️")
    print(f"一个完整的旅行规划系统，由 OpenAI {model_name} 提供支持")
    
    # 初始化知识库
    kb = TravelKnowledgeBase()
    
    # 创建基于 OpenAI 的旅行规划器
    class TravelPlanner(A2AServer):
        """
        一个由 OpenAI 驱动的旅行规划器，用于创建行程、
        提供旅行信息以及提供推荐。
        """
        def __init__(self, knowledge_base, openai_model,base_url,api_key):
            # 使用我们的代理卡片初始化
            super().__init__(AgentCard(
                name="旅行规划师",
                description="帮助规划旅行、查找信息和提供推荐的 AI 旅行助手",
                url=f"http://localhost:{port}",
                version="1.0.0",
                skills=[
                    AgentSkill(
                        name="行程规划",
                        description="根据偏好和持续时间创建详细旅行行程",
                        examples=["规划一个三天的东京之旅", "规划一个带孩子的巴黎周末游"]
                    ),
                    AgentSkill(
                        name="旅行信息",
                        description="提供特定旅行信息如签证要求、健康建议等",
                        examples=["日本的签证要求", "泰国的健康建议"]
                    ),
                    AgentSkill(
                        name="推荐",
                        description="提供活动、住宿和餐厅的定制化推荐",
                        examples=["伦敦的事情要做", "罗马适合家庭的餐厅"]
                    )
                ]
            ))
            
            # 存储知识库
            self.kb = knowledge_base
            
            # 初始化带有旅行专用系统提示的 OpenAI 后端
            self.openai = OpenAIA2AServer(
                api_key=api_key,
                model=openai_model,
                base_url=base_url,
                temperature=0.7,
                system_prompt="""
                你是一个专业的旅行助手，专长于旅行规划、目的地信息和旅行推荐。
                你的目标是根据用户的偏好和约束，帮助他们规划愉快、安全和现实的旅行。
                
                提供信息时:
                - 建议要具体且实用
                - 考虑季节性、预算限制和旅行物流
                - 强调文化体验和真实的当地活动
                - 包括目的地相关的实用旅行小贴士
                - 适当的时候用标题和项目符号格式清晰展示信息
                
                对于行程:
                - 根据景点之间的旅行时间创建现实的每日安排
                - 平衡热门旅游景点和鲜为人知的体验
                - 包含大约的时间和实际的后勤安排
                - 建议突出当地美食的用餐选择
                - 考虑天气、当地事件和开放时间进行规划
                
                始终保持有帮助、热情但现实的语气，并在适当时候承认自己的知识有限。
                """
            )
        
        def plan_trip(self, destination, duration=3, interests=None, budget=None):
            """
            创建自定义旅行行程。
            
            参数:
                destination: 旅行目的地城市/国家
                duration: 旅行天数（默认：3天）
                interests: 旅行者兴趣列表（可选）
                budget: 预算水平（低、中、高）（可选）
                
            返回:
                详细的日程安排
            """
            # 格式化 OpenAI 查询
            if interests and budget:
                query = f"为{destination}创建一个详细的{duration}-天行程。兴趣: {interests}。预算: {budget}."
            elif interests:
                query = f"为{destination}创建一个详细的{duration}-天行程。兴趣: {interests}."
            elif budget:
                query = f"为{destination}创建一个详细的{duration}-天行程。预算: {budget}."
            else:
                query = f"为{destination}创建一个详细的{duration}-天行程。"
            
            # 获取 OpenAI 响应
            from python_a2a import Message, TextContent, MessageRole
            message = Message(content=TextContent(text=query), role=MessageRole.USER)
            response = self.openai.handle_message(message)
            
            # 添加一些来自我们知识库的旅行贴士
            tips = self.kb.get_travel_tips(3)
            tips_text = "\n\n实用旅行贴士:\n" + "\n".join(f"- {tip}" for tip in tips)
            
            return response.content.text + tips_text
        
        def get_travel_info(self, country, topic):
            """
            获取目的地的特定旅行信息。
            
            参数:
                country: 目的地国家
                topic: 信息主题（签证、健康、安全等）
                
            返回:
                相关旅行信息
            """
            # 检查签证信息
            if "visa" in topic.lower():
                kb_info = self.kb.get_visa_info(country)
                # 格式化 OpenAI 查询以扩展我们的知识
                query = f"访问{country}的签证要求是什么？添加更多关于此信息的内容: {kb_info}"
            elif "health" in topic.lower():
                kb_info = self.kb.get_health_advisory()
                query = f"访问{country}时应该知道哪些健康注意事项？参考这个建议: {kb_info}"
            else:
                # 其他主题的一般查询
                query = f"关于{topic}，去{country}旅行时我应该知道什么?"
            
            # 获取 OpenAI 响应
            from python_a2a import Message, TextContent, MessageRole
            message = Message(content=TextContent(text=query), role=MessageRole.USER)
            response = self.openai.handle_message(message)
            
            return response.content.text
        
        def get_recommendations(self, destination, category, preferences=None):
            """
            获取个性化的旅行推荐。
            
            参数:
                destination: 旅行目的地
                category: 推荐类型（活动、餐厅、酒店等）
                preferences: 更详细的偏好的可选参数
                
            返回:
                推荐列表及其描述
            """
            # 格式化 OpenAI 查询
            if preferences:
                query = f"推荐适合喜欢{preferences}的人在{destination}的{category}。"
            else:
                query = f"推荐{destination}最好的{category}。"
            
            # 获取 OpenAI 响应
            from python_a2a import Message, TextContent, MessageRole
            message = Message(content=TextContent(text=query), role=MessageRole.USER)
            response = self.openai.handle_message(message)
            
            return response.content.text
        
        def handle_task(self, task):
            """通过识别意图并路由到适当的技能来处理传入的任务"""
            try:
                # 从任务中提取消息文本
                message_data = task.message or {}
                content = message_data.get("content", {})
                text = content.get("text", "") if isinstance(content, dict) else ""
                
                # 确定消息的意图
                intent, params = self._analyze_intent(text)
                
                # 根据意图路由到合适的技能
                if intent == "trip_planning":
                    response_text = self.plan_trip(**params)
                elif intent == "travel_info":
                    response_text = self.get_travel_info(**params)
                elif intent == "recommendations":
                    response_text = self.get_recommendations(**params)
                else:
                    # 对于一般查询，直接传递给 OpenAI
                    from python_a2a import Message, TextContent, MessageRole
                    message = Message(content=TextContent(text=text), role=MessageRole.USER)
                    response = self.openai.handle_message(message)
                    response_text = response.content.text
                
                # 创建工件与响应
                task.artifacts = [{
                    "parts": [{"type": "text", "text": response_text}]
                }]
                
                # 标记为已完成
                task.status = TaskStatus(state=TaskState.COMPLETED)
                
                return task
            
            except Exception as e:
                # 处理错误
                error_message = f"抱歉，我遇到了一个错误: {str(e)}"
                task.artifacts = [{
                    "parts": [{"type": "text", "text": error_message}]
                }]
                task.status = TaskStatus(state=TaskState.FAILED)
                return task
        
        def _analyze_intent(self, text):
            """
            分析用户的消息以确定意图并提取参数。
            这里使用简单的模式匹配，在实际系统中可以增强 NLP 功能。
            """
            text_lower = text.lower()
            
            # 提取潜在的目的地
            destination_match = re.search(r"(?:in|to|for|visit(?:ing)?)(?:\\s+|\\b)([A-Z][a-zA-Z\\s]+)(?:\\.|\\?|$|\\s+)", text_lower)
            destination = destination_match.group(1).strip() if destination_match else None
            
            # 提取潜在的持续时间
            duration_match = re.search(r"(\d+)(?:-day|天)", text_lower)
            duration = int(duration_match.group(1)) if duration_match else 3
            
            # 提取潜在的兴趣
            interests_match = re.search(r"兴趣: ([^\\n]+)", text_lower)
            interests = interests_match.group(1).strip() if interests_match else None
            
            # 提取潜在的预算
            budget_match = re.search(r"预算: ([^\\n]+)", text_lower)
            budget = budget_match.group(1).strip() if budget_match else None
            
            # 提取潜在的主题
            topic_match = re.search(r"(签证|健康|安全|天气|保险|其他)", text_lower)
            topic = topic_match.group(1).strip() if topic_match else None
            
            # 提取潜在的类别
            category_match = re.search(r"(活动|餐厅|酒店|景点|娱乐)", text_lower)
            category = category_match.group(1).strip() if category_match else None
            
            # 提取潜在的偏好
            preferences_match = re.search(r"喜欢([^\\n]+)", text_lower)
            preferences = preferences_match.group(1).strip() if preferences_match else None
            
            # 确定意图
            if destination and duration:
                return "trip_planning", {
                    "destination": destination,
                    "duration": duration,
                    "interests": interests,
                    "budget": budget
                }
            elif destination and topic:
                return "travel_info", {
                    "country": destination,
                    "topic": topic
                }
            elif destination and category:
                return "recommendations", {
                    "destination": destination,
                    "category": category,
                    "preferences": preferences
                }
            # 默认为一般查询
            return "general", {}
    
    # 创建旅行规划器
    travel_planner = TravelPlanner(kb, model_name,base_url,api_key)
    
    # 打印代理信息
    print("\n=== 旅行规划器信息 ===")
    print(f"名称: {travel_planner.agent_card.name}")
    print(f"描述: {travel_planner.agent_card.description}")
    print(f"网址: {travel_planner.agent_card.url}")
    print(f"OpenAI 模型: {model_name}")
    
    print("\n=== 可用技能 ===")
    for skill in travel_planner.agent_card.skills:
        print(f"- {skill.name}: {skill.description}")
    
    # 如果启用测试，则在单独的进程中启动测试客户端
    client_process = None
    if not args.no_test:
        client_process = multiprocessing.Process(target=test_client, args=(port,))
        client_process.start()
    
    # 启动服务器
    print(f"\n🚀 在 http://localhost:{port} 上启动旅行规划器")
    print("按 Ctrl+C 停止服务器")
    
    try:
        run_server(travel_planner, host="0.0.0.0", port=port)
    except KeyboardInterrupt:
        print("\n✅ 服务器已停止")
    except Exception as e:
        print(f"\n❌ 启动服务器时出错: {e}")
        if "Address already in use" in str(e):
            print(f"\n端口 {port} 已被占用。尝试使用其他端口:")
            print(f"    python openai_travel_planner_zh.py --port {port + 1}")
        return 1
    finally:
        # 清理客户端进程
        if client_process:
            client_process.terminate()
            client_process.join()
    
    print("\n=== 下一步 ===")
    print("1. 尝试 'openai_mcp_agent.py' 示例添加工具功能")
    print("2. 尝试 'knowledge_base.py' 示例创建自己的数据系统")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n✅ 程序被用户中断")
        sys.exit(0)