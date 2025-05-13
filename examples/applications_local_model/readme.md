# applications_local_model_friendly_version
This is a local model friendly version of the original code. It uses the local model to generate the response instead of calling the OpenAI API.

## quickstart
1. Install the required packages:
```bash
  pip install python-a2a  # Includes LangChain, MCP, and other integrations
```
2. configure the local model,update config.json file with your local model details
```json
{
  "model_name":"Qwen/QwQ-32B",
  "api_key": "sk-xxxx",
  "base_url": "https://localhost:8000/v1"
}
```
3. Run the server:
```bash
    python openai_travel_planner.py --port 5001 --no-test
```
4. Run the client:
```bash
    python app_client.py --external http://127.0.0.1:5001
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
