// Workflow Editor - Main JavaScript File

// Global variables
let workflow = {
  id: null,
  name: "New Workflow",
  description: "",
  nodes: {},
  edges: {}
};

let canvas = null;
let selected = null;
let dragging = false;
let connecting = false;
let connectionSource = null;
let nodeIdCounter = 0;
let edgeIdCounter = 0;
let panOffset = { x: 0, y: 0 };
let scale = 1;
let agents = [];
let tools = [];

// Node type configuration for visual styling and behavior
const nodeTypes = {
  AGENT: {
    icon: '<i class="fas fa-robot"></i>',
    color: '#3498db',
    label: 'AI Agent',
    canHaveTools: true
  },
  TOOL: {
    icon: '<i class="fas fa-tools"></i>',
    color: '#2ecc71',
    label: 'Tool',
    canHaveModels: false
  },
  CONDITIONAL: {
    icon: '<i class="fas fa-code-branch"></i>',
    color: '#e74c3c',
    label: 'Condition',
    canHaveModels: false
  },
  TRANSFORM: {
    icon: '<i class="fas fa-exchange-alt"></i>',
    color: '#9b59b6',
    label: 'Transform',
    canHaveModels: false
  },
  INPUT: {
    icon: '<i class="fas fa-sign-in-alt"></i>',
    color: '#f39c12',
    label: 'Input',
    canHaveModels: false
  },
  OUTPUT: {
    icon: '<i class="fas fa-sign-out-alt"></i>',
    color: '#1abc9c',
    label: 'Output',
    canHaveModels: false
  }
};

// Initialize the workflow editor
document.addEventListener('DOMContentLoaded', function() {
  initCanvas();
  loadSidebar();
  setupEventListeners();
  
  // Check if we're editing an existing workflow
  const urlParams = new URLSearchParams(window.location.search);
  const workflowId = urlParams.get('id');
  
  if (workflowId) {
    loadWorkflow(workflowId);
  } else {
    // Create a new workflow
    createNewWorkflow();
  }
});

function initCanvas() {
  canvas = document.getElementById('workflow-canvas');
  
  // Set up canvas interactions
  canvas.addEventListener('mousedown', onCanvasMouseDown);
  canvas.addEventListener('mousemove', onCanvasMouseMove);
  canvas.addEventListener('mouseup', onCanvasMouseUp);
  canvas.addEventListener('wheel', onCanvasWheel);
  
  // Prevent context menu
  canvas.addEventListener('contextmenu', e => e.preventDefault());
}

function loadSidebar() {
  // Load agents and tools from the API
  fetchAgents();
  fetchTools();
  
  // Set up node dragging from sidebar
  const nodeItems = document.querySelectorAll('.node-item');
  nodeItems.forEach(item => {
    item.addEventListener('dragstart', event => {
      event.dataTransfer.setData('nodeType', item.dataset.type);
    });
  });
}

function setupEventListeners() {
  // Workflow actions
  document.getElementById('save-workflow').addEventListener('click', saveWorkflow);
  document.getElementById('run-workflow').addEventListener('click', runWorkflow);
  document.getElementById('clear-workflow').addEventListener('click', clearWorkflow);
  
  // Property panel close button
  document.querySelector('.close-button').addEventListener('click', hidePropertiesPanel);
  
  // Canvas drop event
  canvas.addEventListener('dragover', event => {
    event.preventDefault();
  });
  
  canvas.addEventListener('drop', event => {
    event.preventDefault();
    const nodeType = event.dataTransfer.getData('nodeType');
    if (nodeType) {
      createNode(
        nodeType, 
        event.clientX - canvas.getBoundingClientRect().left - panOffset.x, 
        event.clientY - canvas.getBoundingClientRect().top - panOffset.y
      );
    }
  });
  
  // Keyboard shortcuts
  document.addEventListener('keydown', event => {
    // Delete selected element with Delete key
    if (event.key === 'Delete' && selected) {
      if (selected.classList && selected.classList.contains('workflow-node')) {
        deleteNode(selected.dataset.id);
      } else if (selected.tagName === 'path') {
        deleteEdge(selected.dataset.id);
      }
    }
    
    // Escape to cancel connection or selection
    if (event.key === 'Escape') {
      if (connecting) {
        cancelConnection();
      } else if (selected) {
        deselectAll();
      }
    }
    
    // Ctrl+S to save
    if (event.key === 's' && (event.ctrlKey || event.metaKey)) {
      event.preventDefault();
      saveWorkflow();
    }
  });
}

// Canvas event handlers
function onCanvasMouseDown(event) {
  // Middle mouse button or Alt+Left click for panning
  if (event.button === 1 || (event.button === 0 && event.altKey)) {
    canvas.style.cursor = 'grabbing';
    const startX = event.clientX;
    const startY = event.clientY;
    const initialPanOffset = { ...panOffset };
    
    function mouseMoveHandler(e) {
      panOffset.x = initialPanOffset.x + (e.clientX - startX);
      panOffset.y = initialPanOffset.y + (e.clientY - startY);
      updateCanvasTransform();
    }
    
    function mouseUpHandler() {
      canvas.style.cursor = 'default';
      document.removeEventListener('mousemove', mouseMoveHandler);
      document.removeEventListener('mouseup', mouseUpHandler);
    }
    
    document.addEventListener('mousemove', mouseMoveHandler);
    document.addEventListener('mouseup', mouseUpHandler);
    event.preventDefault();
    return;
  }
  
  // Left click on canvas background deselects everything
  if (event.target === canvas && event.button === 0) {
    deselectAll();
  }
}

function onCanvasMouseMove(event) {
  if (connecting) {
    // Update the temporary connection line
    updateTempConnection(event.clientX, event.clientY);
  }
}

function onCanvasMouseUp(event) {
  if (connecting && event.target.classList && event.target.classList.contains('port')) {
    // Complete connection if dropped on a port
    const targetPort = event.target;
    const targetNode = findParentNode(targetPort);
    
    if (targetNode && targetNode !== findParentNode(connectionSource)) {
      createConnection(connectionSource, targetPort);
    }
    
    cancelConnection();
  }
}

function onCanvasWheel(event) {
  // Zoom with mouse wheel
  event.preventDefault();
  
  const zoom = event.deltaY < 0 ? 1.1 : 0.9;
  
  // Calculate zoom origin (mouse position)
  const rect = canvas.getBoundingClientRect();
  const mouseX = event.clientX - rect.left;
  const mouseY = event.clientY - rect.top;
  
  // Apply zoom and adjust pan offset to zoom toward mouse position
  const prevScale = scale;
  scale *= zoom;
  
  // Limit scale
  scale = Math.min(Math.max(0.25, scale), 4);
  
  // Adjust pan offset if scale changed
  if (prevScale !== scale) {
    const scaleDelta = scale / prevScale;
    panOffset.x = mouseX - (mouseX - panOffset.x) * scaleDelta;
    panOffset.y = mouseY - (mouseY - panOffset.y) * scaleDelta;
  }
  
  updateCanvasTransform();
}

// Node management
function createNode(type, x, y) {
  const id = `node_${Date.now()}_${nodeIdCounter++}`;
  let name = '';
  
  // Set default name based on type
  switch (type) {
    case 'AGENT':
      name = 'Agent';
      break;
    case 'TOOL':
      name = 'Tool';
      break;
    case 'CONDITIONAL':
      name = 'Condition';
      break;
    case 'TRANSFORM':
      name = 'Transform';
      break;
    case 'INPUT':
      name = 'Input';
      break;
    case 'OUTPUT':
      name = 'Output';
      break;
    default:
      name = 'Node';
  }
  
  // Create node data
  const node = {
    id,
    name,
    type,
    position: { x, y },
    config: {}
  };
  
  // Add to workflow
  workflow.nodes[id] = node;
  
  // Create DOM element
  renderNode(node);
  
  // Select the new node
  selectNode(document.querySelector(`[data-id="${id}"]`));
  
  return node;
}

function renderNode(node) {
  const nodeElement = document.createElement('div');
  const nodeTypeInfo = nodeTypes[node.type] || { color: '#95a5a6', icon: '', label: node.type };
  
  nodeElement.className = `workflow-node ${node.type.toLowerCase()}`;
  nodeElement.dataset.id = node.id;
  nodeElement.dataset.type = node.type;
  nodeElement.style.left = `${node.position.x}px`;
  nodeElement.style.top = `${node.position.y}px`;
  nodeElement.style.borderColor = nodeTypeInfo.color;
  
  // Node header
  const header = document.createElement('div');
  header.className = 'node-header';
  header.style.backgroundColor = nodeTypeInfo.color;
  
  const nodeIcon = nodeTypeInfo.icon || '<i class="fas fa-cube"></i>';
  const nodeLabel = node.config.nodeSubtype || nodeTypeInfo.label;
  
  header.innerHTML = `
    <div class="node-icon">${nodeIcon}</div>
    <div class="node-header-text">
      <h3 class="node-title">${node.name}</h3>
      <p class="node-type">${nodeLabel}</p>
    </div>
  `;
  
  nodeElement.appendChild(header);
  
  // Node content
  const content = document.createElement('div');
  content.className = 'node-content';
  
  // Add type-specific content
  switch (node.type) {
    case 'AGENT':
      if (node.config.agent_id) {
        const agent = agents.find(a => a.id === node.config.agent_id);
        content.innerHTML = `
          <div class="node-config-item">
            <span class="config-label">Tools Agent</span>
          </div>
        `;
        
        // Add models section if agent has models
        if (agent && agent.models && agent.models.length > 0) {
          const modelsSection = document.createElement('div');
          modelsSection.className = 'node-section';
          modelsSection.innerHTML = `<p class="section-label">Model</p>`;
          
          // Display model (just add one model for now like in the screenshot)
          const modelElement = document.createElement('div');
          modelElement.className = 'node-slot model-slot filled';
          modelElement.innerHTML = `
            <div class="slot-item">
              <div class="slot-icon"><i class="fas fa-brain"></i></div>
              <div class="slot-name">${agent.models[0]?.name || "Chat Model"}</div>
            </div>
          `;
          modelsSection.appendChild(modelElement);
          content.appendChild(modelsSection);
        }
        
        // Add tools section
        if (nodeTypes[node.type].canHaveTools) {
          const toolsSection = document.createElement('div');
          toolsSection.className = 'node-section';
          toolsSection.innerHTML = `
            <p class="section-label">Tool</p>
            <div class="add-item-button">
              <i class="fas fa-plus"></i>
            </div>
          `;
          content.appendChild(toolsSection);
        }
      } else {
        content.innerHTML = `
          <div class="empty-config">
            <p>Select an agent</p>
            <button class="mini-button">Configure</button>
          </div>
        `;
      }
      break;
      
    case 'TOOL':
      if (node.config.tool_id) {
        const tool = tools.find(t => t.id === node.config.tool_id);
        content.innerHTML = `
          <div class="node-config-item">
            <span class="config-label">${tool?.name || 'Tool'}</span>
          </div>
        `;
      } else {
        content.innerHTML = `
          <div class="empty-config">
            <p>Select a tool</p>
            <button class="mini-button">Configure</button>
          </div>
        `;
      }
      break;
      
    case 'CONDITIONAL':
      content.innerHTML = `
        <div class="node-config-item">
          <span class="config-label">${node.config.condition_type || 'Condition'}</span>
        </div>
      `;
      break;
      
    case 'INPUT':
      content.innerHTML = `
        <div class="node-config-item">
          <span class="config-label">When chat message received</span>
        </div>
      `;
      break;
      
    case 'OUTPUT':
      content.innerHTML = `
        <div class="node-config-item">
          <span class="config-label">Output: ${node.config.output_key || 'result'}</span>
        </div>
      `;
      break;
      
    case 'TRANSFORM':
      content.innerHTML = `
        <div class="node-config-item">
          <span class="config-label">${node.config.transform_type || 'Transform'}</span>
        </div>
      `;
      break;
  }
  
  nodeElement.appendChild(content);
  
  // Node ports
  const ports = document.createElement('div');
  ports.className = 'node-ports';
  
  // Input ports
  const inputPorts = document.createElement('div');
  inputPorts.className = 'port-section';
  
  const inputPort = document.createElement('div');
  inputPort.className = 'port input-port';
  inputPort.dataset.portType = 'input';
  
  // Add port label
  const inputLabel = document.createElement('span');
  inputLabel.className = 'port-label';
  inputLabel.textContent = '1 item';
  inputPorts.appendChild(inputLabel);
  inputPorts.appendChild(inputPort);
  
  // Output ports
  const outputPorts = document.createElement('div');
  outputPorts.className = 'port-section';
  
  const outputPort = document.createElement('div');
  outputPort.className = 'port output-port';
  outputPort.dataset.portType = 'output';
  
  // Add port label for output
  const outputLabel = document.createElement('span');
  outputLabel.className = 'port-label';
  outputLabel.textContent = '1 item';
  outputPorts.appendChild(outputPort);
  outputPorts.appendChild(outputLabel);
  
  // Add conditional ports if needed
  if (node.type === 'CONDITIONAL') {
    const truePort = document.createElement('div');
    truePort.className = 'port output-port true-port';
    truePort.dataset.portType = 'output-true';
    truePort.dataset.edgeType = 'CONDITION_TRUE';
    
    const trueLabel = document.createElement('span');
    trueLabel.className = 'port-label';
    trueLabel.textContent = 'True';
    
    const falsePort = document.createElement('div');
    falsePort.className = 'port output-port false-port';
    falsePort.dataset.portType = 'output-false';
    falsePort.dataset.edgeType = 'CONDITION_FALSE';
    
    const falseLabel = document.createElement('span');
    falseLabel.className = 'port-label';
    falseLabel.textContent = 'False';
    
    outputPorts.appendChild(truePort);
    outputPorts.appendChild(trueLabel);
    outputPorts.appendChild(falsePort);
    outputPorts.appendChild(falseLabel);
  }
  
  ports.appendChild(inputPorts);
  ports.appendChild(outputPorts);
  nodeElement.appendChild(ports);
  
  // Add model/tool slots
  if (node.type === 'AGENT' && node.config.agent_id) {
    // Add hooks for models and tools to be attached
    const modelSlots = document.createElement('div');
    modelSlots.className = 'model-slots';
    nodeElement.appendChild(modelSlots);
    
    const toolSlots = document.createElement('div');
    toolSlots.className = 'tool-slots';
    nodeElement.appendChild(toolSlots);
  }
  
  // Add interaction events
  nodeElement.addEventListener('mousedown', onNodeMouseDown);
  nodeElement.querySelectorAll('.port').forEach(port => {
    port.addEventListener('mousedown', onPortMouseDown);
  });
  
  // Add to canvas
  canvas.appendChild(nodeElement);
}

function onNodeMouseDown(event) {
  // Ignore if clicking on a port
  if (event.target.classList.contains('port')) return;
  
  const node = event.currentTarget;
  selectNode(node);
  
  // Start dragging
  if (event.button === 0) { // Left mouse button
    dragging = true;
    
    const startX = event.clientX;
    const startY = event.clientY;
    const startLeft = parseInt(node.style.left, 10);
    const startTop = parseInt(node.style.top, 10);
    
    function mouseMoveHandler(e) {
      if (dragging) {
        const dx = e.clientX - startX;
        const dy = e.clientY - startY;
        
        node.style.left = `${startLeft + dx}px`;
        node.style.top = `${startTop + dy}px`;
        
        // Update connections
        updateNodeConnections(node.dataset.id);
      }
    }
    
    function mouseUpHandler() {
      dragging = false;
      
      // Update node position in workflow data
      const nodeId = node.dataset.id;
      if (workflow.nodes[nodeId]) {
        workflow.nodes[nodeId].position = {
          x: parseInt(node.style.left, 10),
          y: parseInt(node.style.top, 10)
        };
      }
      
      document.removeEventListener('mousemove', mouseMoveHandler);
      document.removeEventListener('mouseup', mouseUpHandler);
    }
    
    document.addEventListener('mousemove', mouseMoveHandler);
    document.addEventListener('mouseup', mouseUpHandler);
    event.stopPropagation();
  }
}

function selectNode(node) {
  if (!node) return;
  
  deselectAll();
  
  node.classList.add('selected');
  selected = node;
  
  // Show properties panel
  showNodeProperties(node.dataset.id);
}

function deleteNode(nodeId) {
  // Remove the node element
  const nodeElement = document.querySelector(`[data-id="${nodeId}"]`);
  if (nodeElement) {
    nodeElement.remove();
  }
  
  // Remove all connections to/from this node
  Object.keys(workflow.edges).forEach(edgeId => {
    const edge = workflow.edges[edgeId];
    if (edge.source_node_id === nodeId || edge.target_node_id === nodeId) {
      const edgeElement = document.querySelector(`path[data-id="${edgeId}"]`);
      if (edgeElement) {
        edgeElement.remove();
      }
      delete workflow.edges[edgeId];
    }
  });
  
  // Remove from workflow data
  delete workflow.nodes[nodeId];
  
  // Hide properties panel
  hidePropertiesPanel();
}

// Port and connection handling
function onPortMouseDown(event) {
  event.stopPropagation();
  
  const port = event.currentTarget;
  const portType = port.dataset.portType;
  
  // Only output ports can initiate connections
  if (portType && portType.startsWith('output')) {
    startConnection(port);
  }
}

function startConnection(port) {
  connecting = true;
  connectionSource = port;
  
  // Create a temporary SVG connection
  const tempConnection = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  tempConnection.setAttribute('class', 'connection temp-connection');
  tempConnection.setAttribute('stroke', getConnectionColor(port));
  document.getElementById('connections-svg').appendChild(tempConnection);
  
  // Initial position is at the port
  const startPos = getPortPosition(port);
  updateTempConnection(startPos.x, startPos.y);
}

function updateTempConnection(x, y) {
  if (!connecting || !connectionSource) return;
  
  const tempConnection = document.querySelector('.temp-connection');
  if (!tempConnection) return;
  
  const startPos = getPortPosition(connectionSource);
  
  // Calculate path for bezier curve
  const dx = x - startPos.x;
  const dy = y - startPos.y;
  const bezierX = Math.abs(dx) * 0.5;
  
  const path = `M ${startPos.x} ${startPos.y} C ${startPos.x + bezierX} ${startPos.y}, ${x - bezierX} ${y}, ${x} ${y}`;
  tempConnection.setAttribute('d', path);
}

function cancelConnection() {
  if (!connecting) return;
  
  connecting = false;
  connectionSource = null;
  
  // Remove temporary connection
  const tempConnection = document.querySelector('.temp-connection');
  if (tempConnection) {
    tempConnection.remove();
  }
}

function createConnection(sourcePort, targetPort) {
  const sourceNode = findParentNode(sourcePort);
  const targetNode = findParentNode(targetPort);
  
  if (!sourceNode || !targetNode) return;
  
  const sourceNodeId = sourceNode.dataset.id;
  const targetNodeId = targetNode.dataset.id;
  
  // Determine edge type based on source port
  let edgeType = 'DATA';
  if (sourcePort.dataset.edgeType) {
    edgeType = sourcePort.dataset.edgeType;
  }
  
  // Create edge ID
  const edgeId = `edge_${Date.now()}_${edgeIdCounter++}`;
  
  // Create edge data
  const edge = {
    id: edgeId,
    source_node_id: sourceNodeId,
    target_node_id: targetNodeId,
    edge_type: edgeType,
    config: {}
  };
  
  // Add to workflow
  workflow.edges[edgeId] = edge;
  
  // Render connection
  renderConnection(edge);
}

function renderConnection(edge) {
  const sourceNode = document.querySelector(`[data-id="${edge.source_node_id}"]`);
  const targetNode = document.querySelector(`[data-id="${edge.target_node_id}"]`);
  
  if (!sourceNode || !targetNode) return;
  
  // Find the appropriate ports
  let sourcePort;
  
  // For conditional nodes, select the right output port
  if (edge.edge_type === 'CONDITION_TRUE') {
    sourcePort = sourceNode.querySelector('[data-port-type="output-true"]');
  } else if (edge.edge_type === 'CONDITION_FALSE') {
    sourcePort = sourceNode.querySelector('[data-port-type="output-false"]');
  } else {
    sourcePort = sourceNode.querySelector('[data-port-type="output"]');
  }
  
  const targetPort = targetNode.querySelector('[data-port-type="input"]');
  
  if (!sourcePort || !targetPort) return;
  
  const sourcePos = getPortPosition(sourcePort);
  const targetPos = getPortPosition(targetPort);
  
  // Create SVG path
  const connectionPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  connectionPath.setAttribute('class', `connection ${getConnectionClass(edge.edge_type)}`);
  connectionPath.setAttribute('data-id', edge.id);
  connectionPath.setAttribute('data-source', edge.source_node_id);
  connectionPath.setAttribute('data-target', edge.target_node_id);
  connectionPath.setAttribute('data-type', edge.edge_type);
  
  // Set stroke color based on edge type
  connectionPath.setAttribute('stroke', getEdgeTypeColor(edge.edge_type));
  
  // Set stroke dasharray for animated flow
  const length = calculateApproximatePathLength(sourcePos, targetPos);
  connectionPath.setAttribute('stroke-dasharray', `${length / 20} ${length / 30}`);
  
  // Calculate path for bezier curve
  const dx = targetPos.x - sourcePos.x;
  const dy = targetPos.y - sourcePos.y;
  const bezierX = Math.abs(dx) * 0.5;
  
  const path = `M ${sourcePos.x} ${sourcePos.y} C ${sourcePos.x + bezierX} ${sourcePos.y}, ${targetPos.x - bezierX} ${targetPos.y}, ${targetPos.x} ${targetPos.y}`;
  connectionPath.setAttribute('d', path);
  
  // Add movement marker
  const markerId = `marker-${edge.id}`;
  
  // Create marker
  const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
  marker.setAttribute('id', markerId);
  marker.setAttribute('viewBox', '0 0 10 10');
  marker.setAttribute('refX', '5');
  marker.setAttribute('refY', '5');
  marker.setAttribute('markerWidth', '4');
  marker.setAttribute('markerHeight', '4');
  marker.setAttribute('orient', 'auto');
  
  // Create marker shape
  const markerShape = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
  markerShape.setAttribute('cx', '5');
  markerShape.setAttribute('cy', '5');
  markerShape.setAttribute('r', '3');
  markerShape.setAttribute('fill', getEdgeTypeColor(edge.edge_type));
  
  marker.appendChild(markerShape);
  
  // Add marker to SVG
  const svg = document.getElementById('connections-svg');
  const defs = svg.querySelector('defs') || document.createElementNS('http://www.w3.org/2000/svg', 'defs');
  
  if (!svg.querySelector('defs')) {
    svg.appendChild(defs);
  }
  
  defs.appendChild(marker);
  
  // Set marker-end attribute
  connectionPath.setAttribute('marker-end', `url(#${markerId})`);
  
  // Add event listeners
  connectionPath.addEventListener('click', (event) => {
    event.stopPropagation();
    selectConnection(connectionPath);
  });
  
  svg.appendChild(connectionPath);
}

// Calculate approximate path length for bezier curves
function calculateApproximatePathLength(sourcePos, targetPos) {
  const dx = targetPos.x - sourcePos.x;
  const dy = targetPos.y - sourcePos.y;
  return Math.sqrt(dx * dx + dy * dy);
}

// Get connection class based on edge type
function getConnectionClass(edgeType) {
  switch (edgeType) {
    case 'CONDITION_TRUE':
      return 'condition-true';
    case 'CONDITION_FALSE':
      return 'condition-false';
    default:
      return 'data-connection';
  }
}

function updateNodeConnections(nodeId) {
  // Find all edges connected to this node
  Object.keys(workflow.edges).forEach(edgeId => {
    const edge = workflow.edges[edgeId];
    if (edge.source_node_id === nodeId || edge.target_node_id === nodeId) {
      // Re-render this connection
      const connectionPath = document.querySelector(`path[data-id="${edgeId}"]`);
      if (connectionPath) {
        connectionPath.remove();
      }
      renderConnection(edge);
    }
  });
}

function selectConnection(connectionPath) {
  deselectAll();
  
  connectionPath.classList.add('selected');
  selected = connectionPath;
  
  // Show properties panel for edge
  showEdgeProperties(connectionPath.dataset.id);
}

function deleteEdge(edgeId) {
  // Remove edge element
  const edgeElement = document.querySelector(`path[data-id="${edgeId}"]`);
  if (edgeElement) {
    edgeElement.remove();
  }
  
  // Remove from workflow data
  delete workflow.edges[edgeId];
  
  // Hide properties panel
  hidePropertiesPanel();
}

// Properties panel
function showNodeProperties(nodeId) {
  const node = workflow.nodes[nodeId];
  if (!node) return;
  
  const panel = document.getElementById('properties-panel');
  panel.innerHTML = '';
  
  // Create header
  const header = document.createElement('div');
  header.className = 'properties-header';
  header.innerHTML = `
    <h2>${node.name} Properties</h2>
    <button class="close-button">×</button>
  `;
  panel.appendChild(header);
  
  // Close button
  header.querySelector('.close-button').addEventListener('click', hidePropertiesPanel);
  
  // Create form
  const form = document.createElement('form');
  form.addEventListener('submit', (e) => e.preventDefault());
  
  // Basic properties
  addFormField(form, 'Name', 'name', node.name, 'text', (value) => {
    node.name = value;
    document.querySelector(`[data-id="${nodeId}"] .node-title`).textContent = value;
  });
  
  // Type-specific properties
  switch (node.type) {
    case 'AGENT':
      addAgentProperties(form, node);
      break;
    case 'TOOL':
      addToolProperties(form, node);
      break;
    case 'CONDITIONAL':
      addConditionalProperties(form, node);
      break;
    case 'INPUT':
      addInputProperties(form, node);
      break;
    case 'OUTPUT':
      addOutputProperties(form, node);
      break;
    case 'TRANSFORM':
      addTransformProperties(form, node);
      break;
  }
  
  panel.appendChild(form);
  panel.classList.add('visible');
}

function addAgentProperties(form, node) {
  // Agent selection dropdown
  const agentSelect = document.createElement('select');
  agentSelect.className = 'property-select';
  agentSelect.id = 'agent-select';
  
  // Add placeholder option
  const placeholder = document.createElement('option');
  placeholder.value = '';
  placeholder.textContent = 'Select an agent';
  placeholder.selected = !node.config.agent_id;
  agentSelect.appendChild(placeholder);
  
  // Add agent options
  agents.forEach(agent => {
    const option = document.createElement('option');
    option.value = agent.id;
    option.textContent = agent.name;
    option.selected = node.config.agent_id === agent.id;
    agentSelect.appendChild(option);
  });
  
  // Create form group
  const formGroup = document.createElement('div');
  formGroup.className = 'property-group';
  
  const label = document.createElement('label');
  label.className = 'property-label';
  label.textContent = 'Agent';
  label.htmlFor = 'agent-select';
  
  formGroup.appendChild(label);
  formGroup.appendChild(agentSelect);
  form.appendChild(formGroup);
  
  // Event listener
  agentSelect.addEventListener('change', () => {
    node.config.agent_id = agentSelect.value;
    
    // Update node display
    const content = document.querySelector(`[data-id="${node.id}"] .node-content`);
    content.innerHTML = `<p>${node.config.agent_id ? 'Agent connected' : 'Select an agent'}</p>`;
  });
  
  // "Discover Agents" button
  const discoverButton = document.createElement('button');
  discoverButton.className = 'button';
  discoverButton.textContent = 'Discover Agents';
  discoverButton.addEventListener('click', () => {
    discoverAgents().then(() => {
      // Refresh agent select
      const currentValue = agentSelect.value;
      agentSelect.innerHTML = '';
      
      // Re-add placeholder
      const placeholder = document.createElement('option');
      placeholder.value = '';
      placeholder.textContent = 'Select an agent';
      placeholder.selected = !currentValue;
      agentSelect.appendChild(placeholder);
      
      // Re-add agent options
      agents.forEach(agent => {
        const option = document.createElement('option');
        option.value = agent.id;
        option.textContent = agent.name;
        option.selected = currentValue === agent.id;
        agentSelect.appendChild(option);
      });
    });
  });
  
  form.appendChild(discoverButton);
}

function addToolProperties(form, node) {
  // Tool selection dropdown
  const toolSelect = document.createElement('select');
  toolSelect.className = 'property-select';
  toolSelect.id = 'tool-select';
  
  // Add placeholder option
  const placeholder = document.createElement('option');
  placeholder.value = '';
  placeholder.textContent = 'Select a tool';
  placeholder.selected = !node.config.tool_id;
  toolSelect.appendChild(placeholder);
  
  // Add tool options
  tools.forEach(tool => {
    const option = document.createElement('option');
    option.value = tool.id;
    option.textContent = tool.name;
    option.selected = node.config.tool_id === tool.id;
    toolSelect.appendChild(option);
  });
  
  // Create form group
  const formGroup = document.createElement('div');
  formGroup.className = 'property-group';
  
  const label = document.createElement('label');
  label.className = 'property-label';
  label.textContent = 'Tool';
  label.htmlFor = 'tool-select';
  
  formGroup.appendChild(label);
  formGroup.appendChild(toolSelect);
  form.appendChild(formGroup);
  
  // Event listener
  toolSelect.addEventListener('change', () => {
    node.config.tool_id = toolSelect.value;
    
    // Update node display
    const content = document.querySelector(`[data-id="${node.id}"] .node-content`);
    content.innerHTML = `<p>${node.config.tool_id ? 'Tool connected' : 'Select a tool'}</p>`;
    
    // Update tool parameters
    updateToolParameters(form, node);
  });
  
  // "Discover Tools" button
  const discoverButton = document.createElement('button');
  discoverButton.className = 'button';
  discoverButton.textContent = 'Discover Tools';
  discoverButton.addEventListener('click', () => {
    discoverTools().then(() => {
      // Refresh tool select
      const currentValue = toolSelect.value;
      toolSelect.innerHTML = '';
      
      // Re-add placeholder
      const placeholder = document.createElement('option');
      placeholder.value = '';
      placeholder.textContent = 'Select a tool';
      placeholder.selected = !currentValue;
      toolSelect.appendChild(placeholder);
      
      // Re-add tool options
      tools.forEach(tool => {
        const option = document.createElement('option');
        option.value = tool.id;
        option.textContent = tool.name;
        option.selected = currentValue === tool.id;
        toolSelect.appendChild(option);
      });
      
      // Update tool parameters
      updateToolParameters(form, node);
    });
  });
  
  form.appendChild(discoverButton);
  
  // Add tool parameters section
  const parametersDiv = document.createElement('div');
  parametersDiv.id = 'tool-parameters';
  form.appendChild(parametersDiv);
  
  // Load tool parameters if a tool is selected
  if (node.config.tool_id) {
    updateToolParameters(form, node);
  }
}

function updateToolParameters(form, node) {
  const parametersDiv = document.getElementById('tool-parameters');
  if (!parametersDiv) return;
  
  parametersDiv.innerHTML = '';
  
  if (!node.config.tool_id) return;
  
  // Find selected tool
  const tool = tools.find(t => t.id === node.config.tool_id);
  if (!tool) return;
  
  // Add parameters heading
  const heading = document.createElement('h3');
  heading.textContent = 'Tool Parameters';
  heading.style.marginTop = '20px';
  parametersDiv.appendChild(heading);
  
  // Initialize parameters in node config if not present
  if (!node.config.parameters) {
    node.config.parameters = {};
  }
  
  // Add tool parameters
  if (tool.parameters && tool.parameters.length > 0) {
    tool.parameters.forEach(param => {
      const formGroup = document.createElement('div');
      formGroup.className = 'property-group';
      
      const label = document.createElement('label');
      label.className = 'property-label';
      label.textContent = `${param.name}${param.required ? ' *' : ''}`;
      label.htmlFor = `param-${param.name}`;
      
      const input = document.createElement('input');
      input.className = 'property-input';
      input.id = `param-${param.name}`;
      input.type = param.type_name === 'number' ? 'number' : 'text';
      input.value = node.config.parameters[param.name] || '';
      input.placeholder = param.description || param.name;
      
      // Event listener
      input.addEventListener('change', () => {
        node.config.parameters[param.name] = input.type === 'number' ? parseFloat(input.value) : input.value;
      });
      
      formGroup.appendChild(label);
      formGroup.appendChild(input);
      parametersDiv.appendChild(formGroup);
    });
  } else {
    const message = document.createElement('p');
    message.textContent = 'This tool has no parameters.';
    parametersDiv.appendChild(message);
  }
}

function addConditionalProperties(form, node) {
  // Condition type dropdown
  const typeSelect = document.createElement('select');
  typeSelect.className = 'property-select';
  typeSelect.id = 'condition-type';
  
  const conditionTypes = [
    { value: 'contains', label: 'Contains Text' },
    { value: 'equals', label: 'Equals' },
    { value: 'starts_with', label: 'Starts With' },
    { value: 'ends_with', label: 'Ends With' },
    { value: 'regex', label: 'Regex Match' },
    { value: 'javascript', label: 'JavaScript Expression' }
  ];
  
  conditionTypes.forEach(type => {
    const option = document.createElement('option');
    option.value = type.value;
    option.textContent = type.label;
    option.selected = node.config.condition_type === type.value;
    typeSelect.appendChild(option);
  });
  
  // Create form group for condition type
  const typeGroup = document.createElement('div');
  typeGroup.className = 'property-group';
  
  const typeLabel = document.createElement('label');
  typeLabel.className = 'property-label';
  typeLabel.textContent = 'Condition Type';
  typeLabel.htmlFor = 'condition-type';
  
  typeGroup.appendChild(typeLabel);
  typeGroup.appendChild(typeSelect);
  form.appendChild(typeGroup);
  
  // Condition value input
  const valueGroup = document.createElement('div');
  valueGroup.className = 'property-group';
  
  const valueLabel = document.createElement('label');
  valueLabel.className = 'property-label';
  valueLabel.textContent = 'Condition Value';
  valueLabel.htmlFor = 'condition-value';
  
  const valueInput = document.createElement('input');
  valueInput.className = 'property-input';
  valueInput.id = 'condition-value';
  valueInput.type = 'text';
  valueInput.value = node.config.condition_value || '';
  
  valueGroup.appendChild(valueLabel);
  valueGroup.appendChild(valueInput);
  form.appendChild(valueGroup);
  
  // Event listeners
  typeSelect.addEventListener('change', () => {
    node.config.condition_type = typeSelect.value;
    
    // Update node display
    const content = document.querySelector(`[data-id="${node.id}"] .node-content`);
    content.innerHTML = `<p>${node.config.condition_type || 'Condition'}</p>`;
  });
  
  valueInput.addEventListener('change', () => {
    node.config.condition_value = valueInput.value;
  });
}

function addInputProperties(form, node) {
  // Input key
  const keyGroup = document.createElement('div');
  keyGroup.className = 'property-group';
  
  const keyLabel = document.createElement('label');
  keyLabel.className = 'property-label';
  keyLabel.textContent = 'Input Key';
  keyLabel.htmlFor = 'input-key';
  
  const keyInput = document.createElement('input');
  keyInput.className = 'property-input';
  keyInput.id = 'input-key';
  keyInput.type = 'text';
  keyInput.value = node.config.input_key || 'query';
  
  keyGroup.appendChild(keyLabel);
  keyGroup.appendChild(keyInput);
  form.appendChild(keyGroup);
  
  // Default value
  const defaultGroup = document.createElement('div');
  defaultGroup.className = 'property-group';
  
  const defaultLabel = document.createElement('label');
  defaultLabel.className = 'property-label';
  defaultLabel.textContent = 'Default Value';
  defaultLabel.htmlFor = 'default-value';
  
  const defaultInput = document.createElement('input');
  defaultInput.className = 'property-input';
  defaultInput.id = 'default-value';
  defaultInput.type = 'text';
  defaultInput.value = node.config.default_value || '';
  
  defaultGroup.appendChild(defaultLabel);
  defaultGroup.appendChild(defaultInput);
  form.appendChild(defaultGroup);
  
  // Event listeners
  keyInput.addEventListener('change', () => {
    node.config.input_key = keyInput.value;
    
    // Update node display
    const content = document.querySelector(`[data-id="${node.id}"] .node-content`);
    content.innerHTML = `<p>Input: ${node.config.input_key || 'query'}</p>`;
  });
  
  defaultInput.addEventListener('change', () => {
    node.config.default_value = defaultInput.value;
  });
}

function addOutputProperties(form, node) {
  // Output key
  const keyGroup = document.createElement('div');
  keyGroup.className = 'property-group';
  
  const keyLabel = document.createElement('label');
  keyLabel.className = 'property-label';
  keyLabel.textContent = 'Output Key';
  keyLabel.htmlFor = 'output-key';
  
  const keyInput = document.createElement('input');
  keyInput.className = 'property-input';
  keyInput.id = 'output-key';
  keyInput.type = 'text';
  keyInput.value = node.config.output_key || 'result';
  
  keyGroup.appendChild(keyLabel);
  keyGroup.appendChild(keyInput);
  form.appendChild(keyGroup);
  
  // Event listener
  keyInput.addEventListener('change', () => {
    node.config.output_key = keyInput.value;
    
    // Update node display
    const content = document.querySelector(`[data-id="${node.id}"] .node-content`);
    content.innerHTML = `<p>Output: ${node.config.output_key || 'result'}</p>`;
  });
}

function addTransformProperties(form, node) {
  // Transform type dropdown
  const typeSelect = document.createElement('select');
  typeSelect.className = 'property-select';
  typeSelect.id = 'transform-type';
  
  const transformTypes = [
    { value: 'passthrough', label: 'Pass Through' },
    { value: 'extract', label: 'Extract Field' },
    { value: 'template', label: 'Apply Template' },
    { value: 'json', label: 'Convert to JSON' },
    { value: 'javascript', label: 'JavaScript Transform' }
  ];
  
  transformTypes.forEach(type => {
    const option = document.createElement('option');
    option.value = type.value;
    option.textContent = type.label;
    option.selected = node.config.transform_type === type.value;
    typeSelect.appendChild(option);
  });
  
  // Create form group for transform type
  const typeGroup = document.createElement('div');
  typeGroup.className = 'property-group';
  
  const typeLabel = document.createElement('label');
  typeLabel.className = 'property-label';
  typeLabel.textContent = 'Transform Type';
  typeLabel.htmlFor = 'transform-type';
  
  typeGroup.appendChild(typeLabel);
  typeGroup.appendChild(typeSelect);
  form.appendChild(typeGroup);
  
  // Transform config container
  const configContainer = document.createElement('div');
  configContainer.id = 'transform-config';
  form.appendChild(configContainer);
  
  // Initialize config object if not present
  if (!node.config.transform_config) {
    node.config.transform_config = {};
  }
  
  // Update config UI based on selected type
  function updateTransformConfig() {
    configContainer.innerHTML = '';
    
    const type = typeSelect.value;
    switch (type) {
      case 'extract':
        // Field path
        const fieldGroup = document.createElement('div');
        fieldGroup.className = 'property-group';
        
        const fieldLabel = document.createElement('label');
        fieldLabel.className = 'property-label';
        fieldLabel.textContent = 'Field Path';
        fieldLabel.htmlFor = 'field-path';
        
        const fieldInput = document.createElement('input');
        fieldInput.className = 'property-input';
        fieldInput.id = 'field-path';
        fieldInput.type = 'text';
        fieldInput.value = node.config.transform_config.field_path || '';
        fieldInput.placeholder = 'e.g., data.results.0.value';
        
        fieldGroup.appendChild(fieldLabel);
        fieldGroup.appendChild(fieldInput);
        configContainer.appendChild(fieldGroup);
        
        // Event listener
        fieldInput.addEventListener('change', () => {
          node.config.transform_config.field_path = fieldInput.value;
        });
        break;
        
      case 'template':
        // Template
        const templateGroup = document.createElement('div');
        templateGroup.className = 'property-group';
        
        const templateLabel = document.createElement('label');
        templateLabel.className = 'property-label';
        templateLabel.textContent = 'Template';
        templateLabel.htmlFor = 'template';
        
        const templateInput = document.createElement('textarea');
        templateInput.className = 'property-input';
        templateInput.id = 'template';
        templateInput.rows = 4;
        templateInput.value = node.config.transform_config.template || '${input}';
        templateInput.placeholder = 'Use ${input} as placeholder for input value';
        
        templateGroup.appendChild(templateLabel);
        templateGroup.appendChild(templateInput);
        configContainer.appendChild(templateGroup);
        
        // Event listener
        templateInput.addEventListener('change', () => {
          node.config.transform_config.template = templateInput.value;
        });
        break;
        
      case 'javascript':
        // JavaScript code
        const codeGroup = document.createElement('div');
        codeGroup.className = 'property-group';
        
        const codeLabel = document.createElement('label');
        codeLabel.className = 'property-label';
        codeLabel.textContent = 'JavaScript Code';
        codeLabel.htmlFor = 'js-code';
        
        const codeInput = document.createElement('textarea');
        codeInput.className = 'property-input';
        codeInput.id = 'js-code';
        codeInput.rows = 6;
        codeInput.value = node.config.transform_config.code || 'return $input;';
        codeInput.placeholder = 'Access input with $input variable';
        
        codeGroup.appendChild(codeLabel);
        codeGroup.appendChild(codeInput);
        configContainer.appendChild(codeGroup);
        
        // Event listener
        codeInput.addEventListener('change', () => {
          node.config.transform_config.code = codeInput.value;
        });
        break;
        
      case 'json':
      case 'passthrough':
      default:
        // No additional config needed
        const infoText = document.createElement('p');
        infoText.textContent = `No additional configuration needed for ${type} transform.`;
        configContainer.appendChild(infoText);
        break;
    }
  }
  
  // Initialize config UI
  updateTransformConfig();
  
  // Event listener for type change
  typeSelect.addEventListener('change', () => {
    node.config.transform_type = typeSelect.value;
    updateTransformConfig();
    
    // Update node display
    const content = document.querySelector(`[data-id="${node.id}"] .node-content`);
    content.innerHTML = `<p>${node.config.transform_type || 'Transform'}</p>`;
  });
}

function showEdgeProperties(edgeId) {
  const edge = workflow.edges[edgeId];
  if (!edge) return;
  
  const panel = document.getElementById('properties-panel');
  panel.innerHTML = '';
  
  // Create header
  const header = document.createElement('div');
  header.className = 'properties-header';
  header.innerHTML = `
    <h2>Connection Properties</h2>
    <button class="close-button">×</button>
  `;
  panel.appendChild(header);
  
  // Close button
  header.querySelector('.close-button').addEventListener('click', hidePropertiesPanel);
  
  // Create form
  const form = document.createElement('form');
  form.addEventListener('submit', (e) => e.preventDefault());
  
  // Edge type dropdown
  const typeSelect = document.createElement('select');
  typeSelect.className = 'property-select';
  typeSelect.id = 'edge-type';
  
  const edgeTypes = [
    { value: 'DATA', label: 'Data Flow' },
    { value: 'SUCCESS', label: 'On Success' },
    { value: 'ERROR', label: 'On Error' },
    { value: 'CONDITION_TRUE', label: 'If Condition True' },
    { value: 'CONDITION_FALSE', label: 'If Condition False' }
  ];
  
  edgeTypes.forEach(type => {
    const option = document.createElement('option');
    option.value = type.value;
    option.textContent = type.label;
    option.selected = edge.edge_type === type.value;
    typeSelect.appendChild(option);
  });
  
  // Create form group
  const formGroup = document.createElement('div');
  formGroup.className = 'property-group';
  
  const label = document.createElement('label');
  label.className = 'property-label';
  label.textContent = 'Connection Type';
  label.htmlFor = 'edge-type';
  
  formGroup.appendChild(label);
  formGroup.appendChild(typeSelect);
  form.appendChild(formGroup);
  
  // Add source and target info
  const sourceNode = workflow.nodes[edge.source_node_id];
  const targetNode = workflow.nodes[edge.target_node_id];
  
  if (sourceNode && targetNode) {
    const infoGroup = document.createElement('div');
    infoGroup.className = 'property-group';
    infoGroup.innerHTML = `
      <p><strong>From:</strong> ${sourceNode.name}</p>
      <p><strong>To:</strong> ${targetNode.name}</p>
    `;
    form.appendChild(infoGroup);
  }
  
  // Add delete button
  const deleteButton = document.createElement('button');
  deleteButton.className = 'button danger';
  deleteButton.textContent = 'Delete Connection';
  deleteButton.addEventListener('click', () => {
    deleteEdge(edgeId);
  });
  form.appendChild(deleteButton);
  
  // Event listeners
  typeSelect.addEventListener('change', () => {
    // Get the current path element
    const path = document.querySelector(`path[data-id="${edgeId}"]`);
    if (!path) return;
    
    // Update edge type
    edge.edge_type = typeSelect.value;
    path.dataset.type = edge.edge_type;
    
    // Update color
    path.setAttribute('stroke', getEdgeTypeColor(edge.edge_type));
  });
  
  panel.appendChild(form);
  panel.classList.add('visible');
}

function hidePropertiesPanel() {
  const panel = document.getElementById('properties-panel');
  panel.classList.remove('visible');
  deselectAll();
}

// Helper functions
function addFormField(form, label, id, value, type, onChange) {
  const formGroup = document.createElement('div');
  formGroup.className = 'property-group';
  
  const labelElem = document.createElement('label');
  labelElem.className = 'property-label';
  labelElem.textContent = label;
  labelElem.htmlFor = id;
  
  const input = document.createElement('input');
  input.className = 'property-input';
  input.id = id;
  input.type = type;
  input.value = value || '';
  
  input.addEventListener('change', () => {
    onChange(input.value);
  });
  
  formGroup.appendChild(labelElem);
  formGroup.appendChild(input);
  form.appendChild(formGroup);
}

function findParentNode(element) {
  while (element && !element.classList.contains('workflow-node')) {
    element = element.parentElement;
  }
  return element;
}

function getPortPosition(port) {
  const node = findParentNode(port);
  const rect = port.getBoundingClientRect();
  const nodeRect = canvas.getBoundingClientRect();
  
  return {
    x: rect.left + rect.width / 2 - nodeRect.left,
    y: rect.top + rect.height / 2 - nodeRect.top
  };
}

function getConnectionColor(port) {
  if (port.dataset.edgeType === 'CONDITION_TRUE') {
    return '#2ecc71'; // Green
  } else if (port.dataset.edgeType === 'CONDITION_FALSE') {
    return '#e74c3c'; // Red
  } else {
    return '#95a5a6'; // Default gray
  }
}

function getEdgeTypeColor(edgeType) {
  switch (edgeType) {
    case 'CONDITION_TRUE':
      return '#2ecc71'; // Green
    case 'CONDITION_FALSE':
      return '#e74c3c'; // Red
    case 'ERROR':
      return '#e67e22'; // Orange
    case 'SUCCESS':
      return '#3498db'; // Blue
    default:
      return '#95a5a6'; // Gray
  }
}

function deselectAll() {
  const selectedNodes = document.querySelectorAll('.workflow-node.selected');
  selectedNodes.forEach(node => node.classList.remove('selected'));
  
  const selectedConnections = document.querySelectorAll('path.selected');
  selectedConnections.forEach(path => path.classList.remove('selected'));
  
  selected = null;
}

function updateCanvasTransform() {
  const canvasContent = document.getElementById('canvas-content');
  canvasContent.style.transform = `translate(${panOffset.x}px, ${panOffset.y}px) scale(${scale})`;
}

// API functions
function fetchAgents() {
  // First fetch available templates
  fetch('/api/agent_templates')
    .then(response => response.json())
    .then(templateData => {
      // Then fetch running agents
      return fetch('/api/agents')
        .then(response => response.json())
        .then(agentData => {
          // Combine template and running agent data
          agents = agentData;
          
          // Store templates for later use
          window.agentTemplates = templateData;
          
          updateAgentSidebar();
        });
    })
    .catch(error => {
      console.error('Error fetching agents:', error);
      // Show notification
      showNotification('Failed to load agents', true);
    });
}

function fetchTools() {
  fetch('/api/tools')
    .then(response => response.json())
    .then(data => {
      tools = data;
      updateToolSidebar();
    })
    .catch(error => {
      console.error('Error fetching tools:', error);
      // Show notification
      showNotification('Failed to load tools', true);
    });
}

function discoverAgents() {
  showNotification('Discovering agents...');
  
  return fetch('/api/agents/discover', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      base_url: 'http://localhost',
      port_min: 8000,
      port_max: 9000
    })
  })
    .then(response => response.json())
    .then(data => {
      // Update agents list
      agents = data.concat(agents.filter(a => 
        !data.some(d => d.id === a.id)
      ));
      
      updateAgentSidebar();
      showNotification(`Discovered ${data.length} agents`);
      return data;
    })
    .catch(error => {
      console.error('Error discovering agents:', error);
      showNotification('Failed to discover agents', true);
      return [];
    });
}

function createAgent() {
  // Show agent creation modal
  const dialog = document.createElement('div');
  dialog.className = 'modal-overlay';
  dialog.innerHTML = `
    <div class="modal">
      <div class="modal-header">
        <h2>Create Agent</h2>
        <button class="close-button">×</button>
      </div>
      <div class="modal-content">
        <div class="form-group">
          <label for="template-select">Agent Template</label>
          <select id="template-select" class="form-control">
            <option value="" selected disabled>Select a template</option>
            ${window.agentTemplates ? window.agentTemplates.map(t => 
              `<option value="${t.id}">${t.name}</option>`
            ).join('') : ''}
          </select>
        </div>
        <div class="form-group">
          <label for="agent-port">Port</label>
          <input type="number" id="agent-port" class="form-control" min="1024" max="65535" value="8500">
        </div>
        <div id="api-key-section" style="display: none;">
          <div class="form-group">
            <label for="api-key">API Key</label>
            <input type="password" id="api-key" class="form-control">
            <p class="help-text">Required for this agent type</p>
          </div>
        </div>
        <div id="custom-script-section" style="display: none;">
          <div class="form-group">
            <label for="script-path">Script Path</label>
            <input type="text" id="script-path" class="form-control">
            <p class="help-text">Full path to your custom agent script</p>
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button class="modal-button secondary">Cancel</button>
        <button class="modal-button primary">Create Agent</button>
      </div>
    </div>
  `;
  
  document.body.appendChild(dialog);
  dialog.classList.add('visible');
  
  // Add template change event
  const templateSelect = dialog.querySelector('#template-select');
  templateSelect.addEventListener('change', function() {
    const selectedId = this.value;
    const selectedTemplate = window.agentTemplates.find(t => t.id === selectedId);
    
    // Show/hide sections based on template
    const apiKeySection = dialog.querySelector('#api-key-section');
    const customScriptSection = dialog.querySelector('#custom-script-section');
    
    apiKeySection.style.display = selectedTemplate && selectedTemplate.requires_api_key ? 'block' : 'none';
    customScriptSection.style.display = selectedTemplate && selectedTemplate.id === 'custom_script' ? 'block' : 'none';
  });
  
  // Close and cancel buttons
  dialog.querySelectorAll('.close-button, .modal-button.secondary').forEach(button => {
    button.addEventListener('click', () => {
      dialog.remove();
    });
  });
  
  // Create button
  dialog.querySelector('.modal-button.primary').addEventListener('click', () => {
    const templateId = templateSelect.value;
    const port = dialog.querySelector('#agent-port').value;
    const apiKey = dialog.querySelector('#api-key').value;
    const scriptPath = dialog.querySelector('#script-path').value;
    
    if (!templateId) {
      showNotification('Please select a template', true);
      return;
    }
    
    if (!port || port < 1024 || port > 65535) {
      showNotification('Please enter a valid port (1024-65535)', true);
      return;
    }
    
    // Check if template requires API key
    const selectedTemplate = window.agentTemplates.find(t => t.id === templateId);
    if (selectedTemplate && selectedTemplate.requires_api_key && !apiKey) {
      showNotification('API key is required for this agent type', true);
      return;
    }
    
    // Check if custom script needs a path
    if (templateId === 'custom_script' && !scriptPath) {
      showNotification('Script path is required for custom script agents', true);
      return;
    }
    
    // Show loading
    const createButton = dialog.querySelector('.modal-button.primary');
    const originalText = createButton.textContent;
    createButton.textContent = 'Creating...';
    createButton.disabled = true;
    
    // Prepare data
    const data = {
      template_id: templateId,
      port: parseInt(port)
    };
    
    // Add API key if needed
    if (selectedTemplate && selectedTemplate.requires_api_key) {
      data.api_key = apiKey;
    }
    
    // Add script path if needed
    if (templateId === 'custom_script') {
      data.script_path = scriptPath;
    }
    
    // Create agent
    fetch('/api/create_agent', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    })
      .then(response => response.json())
      .then(data => {
        if (data.error) {
          showNotification(`Error: ${data.error}`, true);
        } else {
          showNotification(`Agent created successfully: ${data.name}`);
          dialog.remove();
          
          // Refresh agent list
          fetchAgents();
        }
      })
      .catch(error => {
        console.error('Error creating agent:', error);
        showNotification('Failed to create agent', true);
      })
      .finally(() => {
        // Reset button
        createButton.textContent = originalText;
        createButton.disabled = false;
      });
  });
}

function discoverTools() {
  // Show dialog to get MCP URL
  return new Promise((resolve, reject) => {
    // Create dialog
    const dialog = document.createElement('div');
    dialog.className = 'modal-overlay';
    dialog.innerHTML = `
      <div class="modal">
        <div class="modal-header">
          <h2>Discover MCP Tools</h2>
          <button class="close-button">×</button>
        </div>
        <div class="modal-content">
          <div class="form-group">
            <label for="mcp-url">MCP Server URL</label>
            <input type="text" id="mcp-url" class="form-control" value="http://localhost:8000">
          </div>
        </div>
        <div class="modal-footer">
          <button class="modal-button secondary">Cancel</button>
          <button class="modal-button primary">Discover</button>
        </div>
      </div>
    `;
    
    document.body.appendChild(dialog);
    dialog.classList.add('visible');
    
    // Close button
    dialog.querySelector('.close-button').addEventListener('click', () => {
      dialog.remove();
      reject(new Error('Canceled'));
    });
    
    // Cancel button
    dialog.querySelector('.modal-button.secondary').addEventListener('click', () => {
      dialog.remove();
      reject(new Error('Canceled'));
    });
    
    // Discover button
    dialog.querySelector('.modal-button.primary').addEventListener('click', () => {
      const mcpUrl = document.getElementById('mcp-url').value;
      dialog.remove();
      
      showNotification('Discovering tools...');
      
      fetch('/api/tools/discover', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ url: mcpUrl })
      })
        .then(response => response.json())
        .then(data => {
          // Update tools list
          tools = data.concat(tools.filter(t => 
            !data.some(d => d.id === t.id)
          ));
          
          updateToolSidebar();
          showNotification(`Discovered ${data.length} tools`);
          resolve(data);
        })
        .catch(error => {
          console.error('Error discovering tools:', error);
          showNotification('Failed to discover tools', true);
          reject(error);
        });
    });
  });
}

function updateAgentSidebar() {
  const agentList = document.getElementById('agent-list');
  if (!agentList) return;
  
  agentList.innerHTML = '';
  
  // Add create agent button first
  const createAgentItem = document.createElement('li');
  createAgentItem.className = 'node-item create-item';
  createAgentItem.innerHTML = '<i class="fas fa-plus"></i> Create New Agent';
  createAgentItem.addEventListener('click', createAgent);
  agentList.appendChild(createAgentItem);
  
  // Add agents from registry
  if (agents.length === 0) {
    const emptyItem = document.createElement('li');
    emptyItem.className = 'empty-item';
    emptyItem.textContent = 'No agents found';
    agentList.appendChild(emptyItem);
  } else {
    agents.forEach(agent => {
      // Only show connected agents
      if (agent.status === 'CONNECTED') {
        const item = document.createElement('li');
        item.className = 'node-item';
        item.draggable = true;
        item.dataset.type = 'AGENT';
        item.dataset.agentId = agent.id;
        item.textContent = agent.name;
        
        item.addEventListener('dragstart', event => {
          event.dataTransfer.setData('nodeType', 'AGENT');
          event.dataTransfer.setData('agentId', agent.id);
        });
        
        agentList.appendChild(item);
      }
    });
  }
}

function updateToolSidebar() {
  const toolList = document.getElementById('tool-list');
  if (!toolList) return;
  
  toolList.innerHTML = '';
  
  // Add create tool button first
  const createToolItem = document.createElement('li');
  createToolItem.className = 'node-item create-item';
  createToolItem.innerHTML = '<i class="fas fa-plus"></i> Add New Tool';
  createToolItem.addEventListener('click', () => {
    // Redirect to the tools page for now
    window.location.href = '/tools';
  });
  toolList.appendChild(createToolItem);
  
  // Add tools from registry
  if (tools.length === 0) {
    const emptyItem = document.createElement('li');
    emptyItem.className = 'empty-item';
    emptyItem.textContent = 'No tools found';
    toolList.appendChild(emptyItem);
  } else {
    tools.forEach(tool => {
      // Only show available tools
      if (tool.status === 'AVAILABLE') {
        const item = document.createElement('li');
        item.className = 'node-item';
        item.draggable = true;
        item.dataset.type = 'TOOL';
        item.dataset.toolId = tool.id;
        item.textContent = tool.name;
        
        item.addEventListener('dragstart', event => {
          event.dataTransfer.setData('nodeType', 'TOOL');
          event.dataTransfer.setData('toolId', tool.id);
        });
        
        toolList.appendChild(item);
      }
    });
  }
}

// Workflow management
function createNewWorkflow() {
  workflow = {
    id: null,
    name: "New Workflow",
    description: "",
    nodes: {},
    edges: {}
  };
  
  // Update title
  document.getElementById('workflow-title').textContent = workflow.name;
  
  // Clear canvas
  const canvasContent = document.getElementById('canvas-content');
  canvasContent.innerHTML = '';
  
  // Reset SVG
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.id = 'connections-svg';
  
  // Add defs for markers
  const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
  svg.appendChild(defs);
  
  document.getElementById('connections-container').innerHTML = '';
  document.getElementById('connections-container').appendChild(svg);
  
  // Create a sample workflow similar to the screenshot
  if (!agents.length && !tools.length) {
    // Mock data for demonstration purposes
    createSampleWorkflow();
  }
  
  showNotification('Created new workflow');
}

function createSampleWorkflow() {
  // Create input node (Chat trigger)
  const inputNode = createNode('INPUT', 100, 100);
  inputNode.name = "When chat message received";
  inputNode.config.input_key = "message";
  
  // Create first agent node
  const agent1 = createNode('AGENT', 300, 100);
  agent1.name = "AI Agent";
  agent1.config.agent_id = "agent1";
  agent1.config.nodeSubtype = "Tools Agent";
  
  // Create second agent node
  const agent2 = createNode('AGENT', 550, 100);
  agent2.name = "AI Agent1";
  agent2.config.agent_id = "agent2";
  agent2.config.nodeSubtype = "Tools Agent";

  // Create Chain node
  const chainNode = createNode('TOOL', 800, 100);
  chainNode.name = "Basic LLM Chain";
  chainNode.config.tool_id = "llm_chain";
  
  // Create edges to connect the nodes
  const edge1 = addEdge(inputNode.id, agent1.id);
  const edge2 = addEdge(agent1.id, agent2.id);
  const edge3 = addEdge(agent2.id, chainNode.id);
  
  // Re-render all nodes to apply correct styles
  Object.values(workflow.nodes).forEach(node => {
    const nodeElement = document.querySelector(`[data-id="${node.id}"]`);
    if (nodeElement) {
      nodeElement.remove();
    }
    renderNode(node);
  });
  
  // Re-render all edges
  Object.values(workflow.edges).forEach(edge => {
    const edgeElement = document.querySelector(`path[data-id="${edge.id}"]`);
    if (edgeElement) {
      edgeElement.remove();
    }
    renderConnection(edge);
  });
}

function addEdge(sourceNodeId, targetNodeId, edgeType = 'DATA') {
  return workflow.add_edge(sourceNodeId, targetNodeId, EdgeType[edgeType]);
}

function loadWorkflow(workflowId) {
  showNotification('Loading workflow...');
  
  fetch(`/api/workflows/${workflowId}`)
    .then(response => response.json())
    .then(data => {
      // Load workflow data
      workflow = {
        id: data.id,
        name: data.name,
        description: data.description,
        nodes: {},
        edges: {}
      };
      
      // Update title
      document.getElementById('workflow-title').textContent = workflow.name;
      
      // Clear canvas
      const canvasContent = document.getElementById('canvas-content');
      canvasContent.innerHTML = '';
      
      // Reset SVG
      const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      svg.id = 'connections-svg';
      document.getElementById('connections-container').innerHTML = '';
      document.getElementById('connections-container').appendChild(svg);
      
      // Load nodes
      if (data.nodes && Array.isArray(data.nodes)) {
        data.nodes.forEach(nodeData => {
          // Create node object
          const node = {
            id: nodeData.id,
            name: nodeData.name,
            type: nodeData.type,
            position: nodeData.position || { x: 100, y: 100 },
            config: nodeData.config || {}
          };
          
          // Add to workflow
          workflow.nodes[node.id] = node;
          
          // Render node
          renderNode(node);
        });
      }
      
      // Load edges
      if (data.edges && Array.isArray(data.edges)) {
        data.edges.forEach(edgeData => {
          // Create edge object
          const edge = {
            id: edgeData.id,
            source_node_id: edgeData.source,
            target_node_id: edgeData.target,
            edge_type: edgeData.type,
            config: edgeData.config || {}
          };
          
          // Add to workflow
          workflow.edges[edge.id] = edge;
          
          // Render connection
          renderConnection(edge);
        });
      }
      
      showNotification('Workflow loaded successfully');
    })
    .catch(error => {
      console.error('Error loading workflow:', error);
      showNotification('Failed to load workflow', true);
      
      // Create empty workflow
      createNewWorkflow();
    });
}

function saveWorkflow() {
  // Validate workflow
  if (Object.keys(workflow.nodes).length === 0) {
    showNotification('Cannot save empty workflow', true);
    return;
  }
  
  // Create serializable workflow data
  const workflowData = {
    id: workflow.id,
    name: workflow.name,
    description: workflow.description,
    nodes: Object.values(workflow.nodes),
    edges: Object.values(workflow.edges).map(edge => ({
      id: edge.id,
      source: edge.source_node_id,
      target: edge.target_node_id,
      type: edge.edge_type,
      config: edge.config
    }))
  };
  
  const method = workflow.id ? 'PUT' : 'POST';
  const url = workflow.id ? `/api/workflows/${workflow.id}` : '/api/workflows';
  
  showNotification('Saving workflow...');
  
  fetch(url, {
    method,
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(workflowData)
  })
    .then(response => response.json())
    .then(data => {
      if (data.id) {
        workflow.id = data.id;
        showNotification('Workflow saved successfully');
        
        // Update URL if new workflow
        if (method === 'POST') {
          window.history.replaceState(null, '', `?id=${workflow.id}`);
        }
      } else if (data.error) {
        showNotification(`Error: ${data.error}`, true);
      }
    })
    .catch(error => {
      console.error('Error saving workflow:', error);
      showNotification('Failed to save workflow', true);
    });
}

function runWorkflow() {
  if (!workflow.id) {
    showNotification('Please save the workflow before running it', true);
    return;
  }
  
  // Ask for input data
  const dialog = document.createElement('div');
  dialog.className = 'modal-overlay';
  dialog.innerHTML = `
    <div class="modal">
      <div class="modal-header">
        <h2>Run Workflow</h2>
        <button class="close-button">×</button>
      </div>
      <div class="modal-content">
        <div class="form-group">
          <label for="input-data">Input Data (JSON)</label>
          <textarea id="input-data" class="form-control" rows="5">{}</textarea>
        </div>
      </div>
      <div class="modal-footer">
        <button class="modal-button secondary">Cancel</button>
        <button class="modal-button primary">Run</button>
      </div>
    </div>
  `;
  
  document.body.appendChild(dialog);
  dialog.classList.add('visible');
  
  // Close button
  dialog.querySelector('.close-button').addEventListener('click', () => {
    dialog.remove();
  });
  
  // Cancel button
  dialog.querySelector('.modal-button.secondary').addEventListener('click', () => {
    dialog.remove();
  });
  
  // Run button
  dialog.querySelector('.modal-button.primary').addEventListener('click', () => {
    const inputDataStr = document.getElementById('input-data').value;
    dialog.remove();
    
    let inputData;
    try {
      inputData = JSON.parse(inputDataStr);
    } catch (e) {
      showNotification('Invalid JSON input data', true);
      return;
    }
    
    showNotification('Running workflow...');
    
    fetch(`/api/workflows/${workflow.id}/run`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(inputData)
    })
      .then(response => response.json())
      .then(data => {
        if (data.results) {
          // Show results dialog for the old API format
          const resultsDialog = document.createElement('div');
          resultsDialog.className = 'modal-overlay';
          resultsDialog.innerHTML = `
            <div class="modal">
              <div class="modal-header">
                <h2>Workflow Results</h2>
                <button class="close-button">×</button>
              </div>
              <div class="modal-content">
                <pre>${JSON.stringify(data.results, null, 2)}</pre>
              </div>
              <div class="modal-footer">
                <button class="modal-button primary">Close</button>
              </div>
            </div>
          `;
          
          document.body.appendChild(resultsDialog);
          resultsDialog.classList.add('visible');
          
          // Close buttons
          const closeButtons = resultsDialog.querySelectorAll('.close-button, .modal-button.primary');
          closeButtons.forEach(button => {
            button.addEventListener('click', () => {
              resultsDialog.remove();
            });
          });
        } else if (data.result !== undefined) {
          // New API format with improved output rendering
          let contentHtml = '';
          const result = data.result;
          const outputType = data.type || 'text';
          const outputFormat = data.format || 'text';
          
          // Render based on format
          if (outputFormat === 'markdown') {
            // For markdown, we need a markdown renderer
            // This is a simple approach, ideally use a library like marked.js
            contentHtml = `
              <div class="markdown-content">
                <pre>${result}</pre>
                <p class="output-note">Markdown content</p>
              </div>
            `;
          } else if (outputFormat === 'json') {
            // Format JSON with syntax highlighting
            contentHtml = `
              <div class="json-content">
                <pre>${JSON.stringify(result, null, 2)}</pre>
                <p class="output-note">JSON content</p>
              </div>
            `;
          } else if (outputFormat === 'image') {
            // Display image
            contentHtml = `
              <div class="image-content">
                <img src="${result}" alt="Workflow result image" style="max-width: 100%;">
                <p class="output-note">Image result</p>
              </div>
            `;
          } else if (outputFormat === 'html') {
            // Display HTML in a sandbox iframe for safety
            contentHtml = `
              <div class="html-content">
                <iframe sandbox="allow-scripts" srcdoc="${result.replace(/"/g, '&quot;')}" 
                  style="width: 100%; height: 400px; border: 1px solid #ccc;"></iframe>
                <p class="output-note">HTML content</p>
              </div>
            `;
          } else if (outputFormat === 'code') {
            // Display code with syntax highlighting
            contentHtml = `
              <div class="code-content">
                <pre class="code-block"><code>${result}</code></pre>
                <p class="output-note">Code snippet (${outputType})</p>
              </div>
            `;
          } else if (outputFormat === 'table') {
            // Handle table format - assume result is an array of objects
            try {
              const tableData = typeof result === 'string' ? JSON.parse(result) : result;
              if (Array.isArray(tableData) && tableData.length > 0) {
                // Extract column names from first row
                const columns = Object.keys(tableData[0]);
                let tableHtml = '<table class="result-table"><thead><tr>';
                
                // Add headers
                columns.forEach(col => {
                  tableHtml += `<th>${col}</th>`;
                });
                tableHtml += '</tr></thead><tbody>';
                
                // Add rows
                tableData.forEach(row => {
                  tableHtml += '<tr>';
                  columns.forEach(col => {
                    tableHtml += `<td>${row[col]}</td>`;
                  });
                  tableHtml += '</tr>';
                });
                
                tableHtml += '</tbody></table>';
                contentHtml = `
                  <div class="table-content">
                    ${tableHtml}
                    <p class="output-note">Table data</p>
                  </div>
                `;
              } else {
                throw new Error('Invalid table data');
              }
            } catch (e) {
              // Fallback to text display if table parsing fails
              contentHtml = `
                <div class="text-content">
                  <pre>${typeof result === 'string' ? result : JSON.stringify(result, null, 2)}</pre>
                  <p class="output-note">Data (could not display as table)</p>
                </div>
              `;
            }
          } else {
            // Default text display
            contentHtml = `
              <div class="text-content">
                <pre>${typeof result === 'string' ? result : JSON.stringify(result, null, 2)}</pre>
              </div>
            `;
          }
          
          // Create results dialog with the formatted content
          const resultsDialog = document.createElement('div');
          resultsDialog.className = 'modal-overlay';
          resultsDialog.innerHTML = `
            <div class="modal">
              <div class="modal-header">
                <h2>Workflow Results</h2>
                <button class="close-button">×</button>
              </div>
              <div class="modal-content">
                ${contentHtml}
              </div>
              <div class="modal-footer">
                <button class="modal-button primary">Close</button>
              </div>
            </div>
          `;
          
          document.body.appendChild(resultsDialog);
          resultsDialog.classList.add('visible');
          
          // Close buttons
          const closeButtons = resultsDialog.querySelectorAll('.close-button, .modal-button.primary');
          closeButtons.forEach(button => {
            button.addEventListener('click', () => {
              resultsDialog.remove();
            });
          });
        } else if (data.execution_id) {
          showNotification(`Workflow execution started (ID: ${data.execution_id})`);
        } else if (data.error) {
          showNotification(`Error: ${data.error}`, true);
        }
      })
      .catch(error => {
        console.error('Error running workflow:', error);
        showNotification('Failed to run workflow', true);
      });
  });
}

function clearWorkflow() {
  // Show confirmation dialog
  const dialog = document.createElement('div');
  dialog.className = 'modal-overlay';
  dialog.innerHTML = `
    <div class="modal">
      <div class="modal-header">
        <h2>Clear Workflow</h2>
        <button class="close-button">×</button>
      </div>
      <div class="modal-content">
        <p>Are you sure you want to clear the current workflow? This action cannot be undone.</p>
      </div>
      <div class="modal-footer">
        <button class="modal-button secondary">Cancel</button>
        <button class="modal-button primary danger">Clear</button>
      </div>
    </div>
  `;
  
  document.body.appendChild(dialog);
  dialog.classList.add('visible');
  
  // Close button
  dialog.querySelector('.close-button').addEventListener('click', () => {
    dialog.remove();
  });
  
  // Cancel button
  dialog.querySelector('.modal-button.secondary').addEventListener('click', () => {
    dialog.remove();
  });
  
  // Clear button
  dialog.querySelector('.modal-button.primary').addEventListener('click', () => {
    dialog.remove();
    createNewWorkflow();
  });
}

// Notifications
function showNotification(message, isError = false) {
  // Remove existing notifications
  const existingNotifications = document.querySelectorAll('.notification');
  existingNotifications.forEach(notification => {
    notification.remove();
  });
  
  // Create notification
  const notification = document.createElement('div');
  notification.className = `notification${isError ? ' error' : ''}`;
  notification.textContent = message;
  
  // Add to body
  document.body.appendChild(notification);
  
  // Auto-remove after 3 seconds
  setTimeout(() => {
    notification.remove();
  }, 3000);
}