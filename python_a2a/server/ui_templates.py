"""
UI templates for beautiful documentation.
"""

# HTML template for the agent card index
AGENT_INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ agent.agent_card.name }} - A2A Agent</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
        }
        .card {
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
        }
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 30px rgba(0, 0, 0, 0.15);
        }
        .header {
            background: linear-gradient(90deg, #4F46E5 0%, #7E57C2 100%);
            border-radius: 12px 12px 0 0;
            padding: 20px;
            color: white;
        }
        .content {
            padding: 24px;
        }
        .button {
            background: linear-gradient(90deg, #4F46E5 0%, #7E57C2 100%);
            color: white;
            border-radius: 8px;
            padding: 12px 24px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .button:hover {
            opacity: 0.9;
            transform: translateY(-2px);
        }
    </style>
</head>
<body class="p-6">
    <div class="max-w-4xl mx-auto">
        <div class="card">
            <div class="header">
                <h1 class="text-3xl font-bold">{{ agent.agent_card.name }}</h1>
                <p class="text-xl mt-2 opacity-90">{{ agent.agent_card.description }}</p>
            </div>
            <div class="content">
                <div class="mb-6">
                    <h2 class="text-xl font-semibold mb-3 text-gray-700">Agent Information</h2>
                    <div class="bg-gray-50 p-4 rounded-lg">
                        <p class="mb-2"><span class="font-semibold">Version:</span> {{ agent.agent_card.version }}</p>
                        <p class="mb-2"><span class="font-semibold">Protocol:</span> A2A</p>
                        <p><span class="font-semibold">Endpoint URL:</span> {{ request.host_url }}</p>
                    </div>
                </div>
                
                <div class="mb-6">
                    <h2 class="text-xl font-semibold mb-3 text-gray-700">Available Skills</h2>
                    {% if agent.agent_card.skills %}
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {% for skill in agent.agent_card.skills %}
                                <div class="bg-gray-50 p-4 rounded-lg">
                                    <h3 class="font-bold text-indigo-700">{{ skill.name }}</h3>
                                    <p class="text-gray-600 mb-2">{{ skill.description }}</p>
                                    {% if skill.tags %}
                                        <div class="flex flex-wrap gap-2 mt-2">
                                            {% for tag in skill.tags %}
                                                <span class="bg-indigo-100 text-indigo-800 text-xs px-2 py-1 rounded-full">{{ tag }}</span>
                                            {% endfor %}
                                        </div>
                                    {% endif %}
                                    {% if skill.examples %}
                                        <div class="mt-2">
                                            <p class="text-xs text-gray-500 font-medium">Examples:</p>
                                            <ul class="text-sm text-gray-600 list-disc list-inside">
                                                {% for example in skill.examples %}
                                                    <li>{{ example }}</li>
                                                {% endfor %}
                                            </ul>
                                        </div>
                                    {% endif %}
                                </div>
                            {% endfor %}
                        </div>
                    {% else %}
                        <p class="text-gray-500">No skills available.</p>
                    {% endif %}
                </div>
                
                <div class="mt-8 flex justify-between">
                    <a href="/a2a/agent.json" class="button">View Agent Card JSON</a>
                    <a href="/tasks/send" class="button bg-green-600 hover:bg-green-700">Send a Task</a>
                </div>
            </div>
        </div>
        
        <div class="mt-8 text-center text-gray-500 text-sm">
            <p>Powered by Python A2A Framework</p>
        </div>
    </div>
</body>
</html>
"""

# HTML template for pretty JSON display
JSON_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - A2A Agent</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/styles/atom-one-dark.min.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/highlight.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/languages/json.min.js"></script>
    <style>
        body {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
        }
        .card {
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        }
        .header {
            background: linear-gradient(90deg, #4F46E5 0%, #7E57C2 100%);
            border-radius: 12px 12px 0 0;
            padding: 20px;
            color: white;
        }
        .content {
            padding: 24px;
        }
        .button {
            background: linear-gradient(90deg, #4F46E5 0%, #7E57C2 100%);
            color: white;
            border-radius: 8px;
            padding: 12px 24px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .button:hover {
            opacity: 0.9;
            transform: translateY(-2px);
        }
        pre {
            border-radius: 8px;
            max-height: 70vh;
            overflow: auto;
        }
        .hljs {
            padding: 1.5rem;
            border-radius: 8px;
        }
    </style>
</head>
<body class="p-6">
    <div class="max-w-4xl mx-auto">
        <div class="card">
            <div class="header">
                <h1 class="text-3xl font-bold">{{ title }}</h1>
                <p class="text-xl mt-2 opacity-90">{{ description }}</p>
            </div>
            <div class="content">
                <pre><code class="language-json">{{ json_data }}</code></pre>
                
                <div class="mt-8 flex space-x-4">
                    <a href="/a2a" class="button">Back to Agent Info</a>
                    <button id="copyBtn" class="button bg-green-600 hover:bg-green-700">Copy JSON</button>
                </div>
            </div>
        </div>
        
        <div class="mt-8 text-center text-gray-500 text-sm">
            <p>Powered by Python A2A Framework</p>
        </div>
    </div>
    
    <script>
        // Initialize highlight.js
        document.addEventListener('DOMContentLoaded', () => {
            hljs.highlightAll();
            
            // Copy JSON button
            document.getElementById('copyBtn').addEventListener('click', () => {
                const jsonText = document.querySelector('code').textContent;
                navigator.clipboard.writeText(jsonText)
                    .then(() => {
                        const btn = document.getElementById('copyBtn');
                        btn.innerText = 'Copied!';
                        setTimeout(() => {
                            btn.innerText = 'Copy JSON';
                        }, 2000);
                    });
            });
        });
    </script>
</body>
</html>
"""