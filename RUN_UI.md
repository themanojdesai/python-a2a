# How to Run Agent Flow UI

Follow these simple steps to run the Agent Flow UI:

## Step 1: Make sure you're in the correct directory

```bash
cd /Users/manojdesai/Projects/public_profile/python-a2a/simple_a2a
```

## Step 2: Run the starter script

```bash
python start_ui.py
```

You should see output similar to:
```
Using storage directory: /Users/manojdesai/.agent_flow
Starting web server at http://localhost:8080
```

## Step 3: Open the UI in your browser

Open your web browser and navigate to:
```
http://localhost:8080
```

## Optional: Start with different options

```bash
# Run on a different port
python start_ui.py --port 3000

# Run in debug mode (enables auto-reloading)
python start_ui.py --debug

# Use a custom storage directory
python start_ui.py --storage-dir /path/to/storage
```

## Step 4: Start some agent servers for testing

In separate terminal windows, run:

```bash
# Weather agent
python -m python_a2a.examples.getting_started.simple_server --port 8001 --agent-type weather

# Travel agent
python -m python_a2a.examples.getting_started.simple_server --port 8002 --agent-type travel
```

Then in the UI, click "Discover Agents" to find these running agents.

## Troubleshooting

1. **"No module named 'agent_flow'"**: Make sure you're running the command from the correct directory.

2. **Port already in use**: Try using a different port with `--port`.

3. **UI doesn't load**: Check the console output for errors and ensure the server is running.

4. **No agents found**: Make sure you have agent servers running and click "Discover Agents".

5. **Can't run workflow**: Check that you've connected all the nodes properly and configured them in the properties panel.