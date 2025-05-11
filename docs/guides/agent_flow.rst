Agent Flow UI
===========

The Agent Flow UI is a visual workflow editor for creating, managing, and executing A2A agent networks.
It provides a drag-and-drop interface for connecting agents and defining workflows.

.. image:: ../images/agent_flow_ui.png
   :alt: Agent Flow UI
   :align: center

Overview
--------

Agent Flow is built as an integral part of the python-a2a package, providing:

- Visual workflow builder for agent networks
- Agent management and discovery
- MCP tool integration
- Real-time workflow execution
- Workflow storage and retrieval

Starting the UI
--------------

Starting the Agent Flow UI is simple:

.. code-block:: bash

    # Start with default settings (opens browser automatically)
    a2a ui
    
    # Start with custom settings
    a2a ui --port 9000 --host 0.0.0.0 --storage-dir ~/.my_workflows --debug --no-browser

Command-line options:

- ``--port PORT``: Port to run the server on (default: 8080)
- ``--host HOST``: Host to bind the server to (default: localhost)
- ``--storage-dir DIR``: Directory to store workflow files (default: ~/.agent_flow)
- ``--debug``: Run in debug mode
- ``--no-browser``: Don't automatically open a browser
- ``--skip-port-check``: Skip checking if the port is available (advanced)

The UI will be available at http://localhost:8080 (or your custom host/port) and will open automatically in your browser.

Building Workflows
----------------

The Agent Flow UI provides a visual canvas for building agent workflows:

1. **Agents Tab**: Discover and manage available agents
2. **Tools Tab**: Find and integrate MCP tools
3. **Workflows Tab**: Build, save, and run workflows

Workflow Components
~~~~~~~~~~~~~~~~~

- **Nodes**: Represent agents, tools, or logic operations
- **Edges**: Connect nodes to define the flow of data and control
- **Properties Panel**: Configure node and edge properties

Node Types
~~~~~~~~~

- **Agent Nodes**: Connect to A2A agents
- **Tool Nodes**: Use MCP tools
- **Input Nodes**: Define entry points and initial data
- **Condition Nodes**: Implement branching logic
- **Transform Nodes**: Modify data between nodes
- **Output Nodes**: Collect and format results

Creating Your First Workflow
--------------------------

1. Open the Agent Flow UI with ``a2a ui``
2. Go to the "Agents" tab and discover or add agents
3. Go to the "Workflows" tab and click "New Workflow"
4. Drag an Input node onto the canvas
5. Drag an Agent node and connect it to the Input node
6. Configure the Agent node to use one of your discovered agents
7. Add an Output node and connect it to the Agent node
8. Save your workflow by clicking "Save" in the toolbar
9. Run your workflow by clicking "Run" and providing any required input

Advanced Features
---------------

Agent Discovery
~~~~~~~~~~~~~

Agent Flow includes automated agent discovery:

1. Go to the "Agents" tab
2. Click "Discover Agents"
3. Configure discovery settings (port range, base URL)
4. View and add discovered agents

Tool Integration
~~~~~~~~~~~~~

Connect to MCP tools:

1. Go to the "Tools" tab
2. Add an MCP server URL
3. Discover and register available tools
4. Use tools in your workflows by adding Tool nodes

Conditional Branching
~~~~~~~~~~~~~~~~~~

Create workflows with decision logic:

1. Add a Condition node to your workflow
2. Define the condition (e.g., text contains "weather")
3. Connect the True and False outputs to different paths
4. Configure subsequent nodes for each branch

Workflow Storage
~~~~~~~~~~~~~

Agent Flow automatically stores workflows:

- Default storage: ``~/.agent_flow/workflows``
- Custom storage: Specify with ``--storage-dir``
- Save/load: Use the UI toolbar or CLI commands

API Access
---------

The Agent Flow server provides a REST API:

- ``/api/agents``: Manage agent definitions
- ``/api/tools``: Manage tool definitions
- ``/api/workflows``: Manage workflows
- ``/api/executions``: Run and monitor workflow executions

For detailed API documentation, visit http://localhost:8080/api/docs when the server is running.

CLI Commands
----------

Agent Flow integrates with the A2A CLI:

.. code-block:: bash

    # Start the UI
    a2a ui
    
    # List available agents
    a2a agent list
    
    # Discover agents
    a2a agent discover
    
    # Create a workflow from a JSON definition
    a2a workflow create --file workflow.json
    
    # Run a workflow
    a2a workflow run WORKFLOW_ID --input '{"query": "What's the weather in Paris?"}'
    
    # Export a workflow
    a2a workflow export WORKFLOW_ID --output workflow.json

Programming Interface
------------------

You can also work with Agent Flow programmatically:

.. code-block:: python

    from python_a2a.agent_flow import (
        Workflow, WorkflowNode, AgentRegistry, ToolRegistry, 
        WorkflowExecutor, FileWorkflowStorage
    )
    
    # Create components
    agent_registry = AgentRegistry()
    tool_registry = ToolRegistry()
    workflow_storage = FileWorkflowStorage("~/.agent_flow/workflows")
    executor = WorkflowExecutor(agent_registry, tool_registry)
    
    # Discover agents
    agent_registry.discover_agents("http://localhost", (5000, 6000))
    
    # Create workflow
    workflow = Workflow(name="Simple Workflow")
    
    # Add nodes and edges
    # ...
    
    # Save workflow
    workflow_id = workflow_storage.save_workflow(workflow)
    
    # Execute workflow
    results = executor.execute_workflow(workflow, {"query": "Hello world"})
    
    print(results)

Customization
-----------

The Agent Flow UI can be customized by:

- Creating custom node types
- Adding custom tool adapters
- Extending the UI with plugins
- Creating specialized agent templates

For advanced customization, see the Agent Flow architecture documentation.

Conclusion
---------

Agent Flow provides a powerful visual interface for building agent networks and workflows. It integrates seamlessly with the python-a2a package and offers intuitive tools for creating complex agent interactions without writing code.

For more advanced usage, refer to the API documentation and example workflows.