// Simple Workflow Editor - Main JavaScript File

// Global variables
let workflow = {
  id: null,
  name: "New Workflow",
  description: "",
  nodes: {},
  edges: {}
};

let canvas;
let canvasContent;
let selectedNode = null;
let selectedEdge = null;
let draggingNode = false;
let draggingPort = false;
let dragOffsetX = 0;
let dragOffsetY = 0;
let sourcePort = null;
let tempConnection = null;
let nodeCounter = 0;
let edgeCounter = 0;
let agents = [];
let tools = [];

// Node and edge collections
const nodes = {};
const edges = {};

// Initialize the editor
document.addEventListener('DOMContentLoaded', () => {
  initCanvas();
  initEvents();
  loadAgents();
  loadTools();
  createSampleWorkflow();
});

// Initialize the canvas element
function initCanvas() {
  canvas = document.getElementById('workflow-canvas');
  canvasContent = document.getElementById('canvas-content');
  
  // Initialize the SVG for connections
  const svg = document.getElementById('connections-svg');
  if (!svg.querySelector('defs')) {
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    svg.appendChild(defs);
  }
}

// Initialize event listeners
function initEvents() {
  // Drag and drop from sidebar
  document.querySelectorAll('.node-item').forEach(item => {
    item.addEventListener('dragstart', onDragStart);
  });
  
  // Canvas events
  canvas.addEventListener('dragover', onDragOver);
  canvas.addEventListener('drop', onDrop);
  canvas.addEventListener('click', onCanvasClick);
  
  // Properties panel events
  document.getElementById('close-properties').addEventListener('click', hideProperties);
  document.getElementById('node-name').addEventListener('input', updateNodeName);
  
  // Toolbar events
  document.getElementById('zoom-in').addEventListener('click', zoomIn);
  document.getElementById('zoom-out').addEventListener('click', zoomOut);
  document.getElementById('reset-view').addEventListener('click', resetView);
  document.getElementById('delete-selected').addEventListener('click', deleteSelected);
  
  // Workflow actions
  document.getElementById('save-workflow').addEventListener('click', saveWorkflow);
  document.getElementById('run-workflow').addEventListener('click', runWorkflow);
  document.getElementById('clear-workflow').addEventListener('click', clearWorkflow);
}

// Drag and drop functions
function onDragStart(e) {
  e.dataTransfer.setData('nodeType', e.target.getAttribute('data-type'));
}

function onDragOver(e) {
  e.preventDefault();
}

function onDrop(e) {
  e.preventDefault();
  
  const nodeType = e.dataTransfer.getData('nodeType');
  if (nodeType) {
    // Calculate position relative to canvas
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    // Create node of the specified type
    createNode(nodeType, x, y);
  }
}

// Create a new node
function createNode(type, x, y) {
  const id = `node_${Date.now()}_${nodeCounter++}`;
  let name = '';
  
  // Set default name based on type
  switch (type) {
    case 'AGENT':
      name = 'AI Agent';
      break;
    case 'TOOL':
      name = 'Basic LLM Chain';
      break;
    case 'INPUT':
      name = 'Input';
      break;
    case 'OUTPUT':
      name = 'Output';
      break;
    default:
      name = 'Node';
      break;
  }
  
  // Create node data
  const node = {
    id,
    name,
    type,
    position: { x, y },
    config: {}
  };
  
  // Add to nodes collection
  nodes[id] = node;
  
  // Render the node on canvas
  renderNode(node);
  
  return node;
}

// Render a node on the canvas
function renderNode(node) {
  // Create node element
  const nodeElement = document.createElement('div');
  nodeElement.className = `workflow-node ${node.type.toLowerCase()}`;
  nodeElement.id = node.id;
  nodeElement.setAttribute('data-id', node.id);
  nodeElement.setAttribute('data-type', node.type);
  nodeElement.style.left = `${node.position.x}px`;
  nodeElement.style.top = `${node.position.y}px`;
  
  // Determine node color based on type
  let headerColor = '#3498db'; // Default blue
  
  switch (node.type) {
    case 'AGENT':
      headerColor = '#3498db'; // Blue
      break;
    case 'TOOL':
      headerColor = '#2ecc71'; // Green
      break;
    case 'INPUT':
      headerColor = '#f39c12'; // Orange
      break;
    case 'OUTPUT':
      headerColor = '#1abc9c'; // Teal
      break;
  }
  
  // Create node header
  const header = document.createElement('div');
  header.className = 'node-header';
  header.style.backgroundColor = headerColor;
  header.innerHTML = `<div class="node-title">${node.name}</div>`;
  
  // Create node content
  const content = document.createElement('div');
  content.className = 'node-content';
  
  if (node.type === 'AGENT' || node.type === 'TOOL') {
    // Add configuration button for agent/tool nodes
    content.innerHTML = `
      <span>Select an agent</span>
      <button class="configure-button">Configure</button>
    `;
  } else if (node.type === 'INPUT') {
    content.innerHTML = `<span>When chat message received</span>`;
  } else {
    content.innerHTML = `<span>${node.name}</span>`;
  }
  
  // Create ports
  const ports = document.createElement('div');
  ports.className = 'node-ports';
  
  // Input port section (all nodes except INPUT have an input port)
  if (node.type !== 'INPUT') {
    const inputSection = document.createElement('div');
    inputSection.className = 'port-section';
    
    const inputPort = document.createElement('div');
    inputPort.className = 'port input-port';
    inputPort.setAttribute('data-node-id', node.id);
    inputPort.setAttribute('data-port-type', 'input');
    
    const inputLabel = document.createElement('div');
    inputLabel.className = 'port-label';
    inputLabel.textContent = '1 item';
    
    inputSection.appendChild(inputPort);
    inputSection.appendChild(inputLabel);
    
    inputPort.addEventListener('mousedown', (e) => e.stopPropagation());
    
    ports.appendChild(inputSection);
  }
  
  // Output port section (all nodes except OUTPUT have an output port)
  if (node.type !== 'OUTPUT') {
    const outputSection = document.createElement('div');
    outputSection.className = 'port-section';
    
    const outputPort = document.createElement('div');
    outputPort.className = 'port output-port';
    outputPort.setAttribute('data-node-id', node.id);
    outputPort.setAttribute('data-port-type', 'output');
    
    const outputLabel = document.createElement('div');
    outputLabel.className = 'port-label';
    outputLabel.textContent = '1 item';
    
    outputSection.appendChild(outputPort);
    outputSection.appendChild(outputLabel);
    
    outputPort.addEventListener('mousedown', startConnection);
    
    ports.appendChild(outputSection);
  }
  
  // Build node
  nodeElement.appendChild(header);
  nodeElement.appendChild(content);
  nodeElement.appendChild(ports);
  
  // Add event listeners
  nodeElement.addEventListener('mousedown', nodeMouseDown);
  nodeElement.addEventListener('click', nodeClick);
  
  // Find the configure button and add listener
  const configButton = nodeElement.querySelector('.configure-button');
  if (configButton) {
    configButton.addEventListener('click', (e) => {
      e.stopPropagation();
      showProperties(node);
    });
  }
  
  // Add node to canvas
  canvasContent.appendChild(nodeElement);
}

// Node event handlers
function nodeMouseDown(e) {
  if (e.target.classList.contains('port')) return;
  
  // Start dragging node
  const nodeElement = e.currentTarget;
  selectNode(nodeElement);
  
  draggingNode = true;
  const rect = nodeElement.getBoundingClientRect();
  dragOffsetX = e.clientX - rect.left;
  dragOffsetY = e.clientY - rect.top;
  
  // Mouse move handler for dragging
  const mouseMoveHandler = (moveEvent) => {
    if (draggingNode) {
      const canvasRect = canvas.getBoundingClientRect();
      const x = moveEvent.clientX - canvasRect.left - dragOffsetX;
      const y = moveEvent.clientY - canvasRect.top - dragOffsetY;
      
      // Update node position
      nodeElement.style.left = `${x}px`;
      nodeElement.style.top = `${y}px`;
      
      // Update node data
      const nodeId = nodeElement.getAttribute('data-id');
      if (nodes[nodeId]) {
        nodes[nodeId].position = { x, y };
      }
      
      // Update connections
      updateNodeConnections(nodeId);
    }
  };
  
  // Mouse up handler to stop dragging
  const mouseUpHandler = () => {
    draggingNode = false;
    document.removeEventListener('mousemove', mouseMoveHandler);
    document.removeEventListener('mouseup', mouseUpHandler);
  };
  
  document.addEventListener('mousemove', mouseMoveHandler);
  document.addEventListener('mouseup', mouseUpHandler);
  
  e.stopPropagation();
}

function nodeClick(e) {
  if (!e.target.classList.contains('port')) {
    selectNode(e.currentTarget);
    e.stopPropagation();
  }
}

function selectNode(nodeElement) {
  // Deselect previous selection
  if (selectedNode) {
    selectedNode.classList.remove('selected');
  }
  
  // Select new node
  selectedNode = nodeElement;
  selectedNode.classList.add('selected');
  
  // Show properties panel
  const nodeId = nodeElement.getAttribute('data-id');
  if (nodes[nodeId]) {
    showProperties(nodes[nodeId]);
  }
}

// Connection functions
function startConnection(e) {
  e.stopPropagation();
  
  sourcePort = e.target;
  draggingPort = true;
  
  // Setup temp connection path
  tempConnection = document.getElementById('temp-connection');
  
  // Calculate start position
  const portRect = sourcePort.getBoundingClientRect();
  const canvasRect = canvas.getBoundingClientRect();
  const startX = portRect.left + portRect.width / 2 - canvasRect.left;
  const startY = portRect.top + portRect.height / 2 - canvasRect.top;
  
  // Initialize connection line
  updateTempConnection(startX, startY);
  
  // Add mouse move handler
  document.addEventListener('mousemove', connectionMouseMove);
  document.addEventListener('mouseup', connectionMouseUp);
}

function connectionMouseMove(e) {
  if (!draggingPort || !sourcePort) return;
  
  const canvasRect = canvas.getBoundingClientRect();
  const x = e.clientX - canvasRect.left;
  const y = e.clientY - canvasRect.top;
  
  updateTempConnection(x, y);
}

function connectionMouseUp(e) {
  if (!draggingPort || !sourcePort) return;
  
  draggingPort = false;
  
  // Clear temp connection
  tempConnection.setAttribute('d', '');
  
  // Check if we're over a valid target port
  const targetElement = document.elementFromPoint(e.clientX, e.clientY);
  
  if (targetElement && targetElement.classList.contains('port') && 
      targetElement.getAttribute('data-port-type') === 'input') {
    
    const sourceNodeId = sourcePort.getAttribute('data-node-id');
    const targetNodeId = targetElement.getAttribute('data-node-id');
    
    // Don't connect to self
    if (sourceNodeId !== targetNodeId) {
      createConnection(sourceNodeId, targetNodeId);
    }
  }
  
  // Clean up
  document.removeEventListener('mousemove', connectionMouseMove);
  document.removeEventListener('mouseup', connectionMouseUp);
  sourcePort = null;
}

function updateTempConnection(endX, endY) {
  // Get start position (source port)
  const portRect = sourcePort.getBoundingClientRect();
  const canvasRect = canvas.getBoundingClientRect();
  const startX = portRect.left + portRect.width / 2 - canvasRect.left;
  const startY = portRect.top + portRect.height / 2 - canvasRect.top;
  
  // Create bezier curve
  const dx = endX - startX;
  const bezierX = Math.abs(dx) * 0.5;
  const path = `M ${startX} ${startY} C ${startX + bezierX} ${startY}, ${endX - bezierX} ${endY}, ${endX} ${endY}`;
  
  tempConnection.setAttribute('d', path);
}

function createConnection(sourceNodeId, targetNodeId) {
  const id = `edge_${Date.now()}_${edgeCounter++}`;
  
  // Create edge data
  const edge = {
    id,
    source: sourceNodeId,
    target: targetNodeId,
    type: 'DATA'
  };
  
  // Add to edges collection
  edges[id] = edge;
  
  // Render the edge
  renderConnection(edge);
  
  return edge;
}

function renderConnection(edge) {
  // Get source and target nodes
  const sourceNode = document.getElementById(edge.source);
  const targetNode = document.getElementById(edge.target);
  
  if (!sourceNode || !targetNode) return;
  
  // Get ports
  const sourcePort = sourceNode.querySelector('.output-port');
  const targetPort = targetNode.querySelector('.input-port');
  
  if (!sourcePort || !targetPort) return;
  
  // Calculate port positions
  const sourceRect = sourcePort.getBoundingClientRect();
  const targetRect = targetPort.getBoundingClientRect();
  const canvasRect = canvas.getBoundingClientRect();
  
  const startX = sourceRect.left + sourceRect.width / 2 - canvasRect.left;
  const startY = sourceRect.top + sourceRect.height / 2 - canvasRect.top;
  const endX = targetRect.left + targetRect.width / 2 - canvasRect.left;
  const endY = targetRect.top + targetRect.height / 2 - canvasRect.top;
  
  // Create SVG path
  const svg = document.getElementById('connections-svg');
  const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  
  path.setAttribute('id', edge.id);
  path.setAttribute('class', 'connection');
  path.setAttribute('data-source', edge.source);
  path.setAttribute('data-target', edge.target);
  
  // Create bezier curve
  const dx = endX - startX;
  const bezierX = Math.abs(dx) * 0.5;
  const pathD = `M ${startX} ${startY} C ${startX + bezierX} ${startY}, ${endX - bezierX} ${endY}, ${endX} ${endY}`;
  
  path.setAttribute('d', pathD);
  
  // Add event listener for selection
  path.addEventListener('click', (e) => {
    selectConnection(path);
    e.stopPropagation();
  });
  
  svg.appendChild(path);
}

function updateNodeConnections(nodeId) {
  // Find all edges connected to this node
  Object.values(edges).forEach(edge => {
    if (edge.source === nodeId || edge.target === nodeId) {
      // Remove and re-render the connection
      const path = document.getElementById(edge.id);
      if (path) {
        path.remove();
      }
      renderConnection(edge);
    }
  });
}

function selectConnection(pathElement) {
  // Deselect previous selection
  if (selectedNode) {
    selectedNode.classList.remove('selected');
    selectedNode = null;
  }
  
  if (selectedEdge) {
    selectedEdge.classList.remove('selected');
  }
  
  // Select new edge
  selectedEdge = pathElement;
  selectedEdge.classList.add('selected');
  
  // TODO: Show edge properties if needed
}

// Properties panel
function showProperties(node) {
  // Set properties panel title
  const title = document.getElementById('properties-title');
  title.textContent = `${node.name} Properties`;
  
  // Set node name input
  const nameInput = document.getElementById('node-name');
  nameInput.value = node.name;
  
  // Show/hide agent selector
  const agentGroup = document.getElementById('agent-selector-group');
  agentGroup.style.display = node.type === 'AGENT' ? 'block' : 'none';
  
  // Show properties panel
  const panel = document.getElementById('properties-panel');
  panel.classList.add('visible');
  
  // Store reference to current node
  panel.setAttribute('data-node-id', node.id);
}

function hideProperties() {
  const panel = document.getElementById('properties-panel');
  panel.classList.remove('visible');
}

function updateNodeName() {
  const panel = document.getElementById('properties-panel');
  const nodeId = panel.getAttribute('data-node-id');
  const nameInput = document.getElementById('node-name');
  
  if (nodeId && nodes[nodeId]) {
    const node = nodes[nodeId];
    node.name = nameInput.value;
    
    // Update node element
    const nodeElement = document.getElementById(nodeId);
    if (nodeElement) {
      const title = nodeElement.querySelector('.node-title');
      if (title) {
        title.textContent = node.name;
      }
    }
  }
}

// Canvas utility functions
function zoomIn() {
  // TODO: Implement zoom in
  showNotification('Zoom feature not implemented yet');
}

function zoomOut() {
  // TODO: Implement zoom out
  showNotification('Zoom feature not implemented yet');
}

function resetView() {
  // TODO: Implement reset view
  showNotification('Reset view feature not implemented yet');
}

function onCanvasClick() {
  // Deselect when clicking on canvas background
  if (selectedNode) {
    selectedNode.classList.remove('selected');
    selectedNode = null;
  }
  
  if (selectedEdge) {
    selectedEdge.classList.remove('selected');
    selectedEdge = null;
  }
  
  hideProperties();
}

// Workflow actions
function saveWorkflow() {
  // TODO: Implement save workflow
  showNotification('Workflow saved');
}

function runWorkflow() {
  // TODO: Implement run workflow
  showNotification('Running workflow');
}

function clearWorkflow() {
  if (confirm('Are you sure you want to clear the entire workflow?')) {
    // Clear nodes and edges
    Object.keys(nodes).forEach(nodeId => {
      const nodeElement = document.getElementById(nodeId);
      if (nodeElement) {
        nodeElement.remove();
      }
    });
    
    Object.keys(edges).forEach(edgeId => {
      const edgeElement = document.getElementById(edgeId);
      if (edgeElement) {
        edgeElement.remove();
      }
    });
    
    // Reset collections
    Object.keys(nodes).forEach(key => delete nodes[key]);
    Object.keys(edges).forEach(key => delete edges[key]);
    
    showNotification('Workflow cleared');
  }
}

function deleteSelected() {
  if (selectedNode) {
    const nodeId = selectedNode.getAttribute('data-id');
    
    // Delete connected edges
    Object.values(edges).forEach(edge => {
      if (edge.source === nodeId || edge.target === nodeId) {
        const edgeElement = document.getElementById(edge.id);
        if (edgeElement) {
          edgeElement.remove();
        }
        delete edges[edge.id];
      }
    });
    
    // Delete node
    selectedNode.remove();
    delete nodes[nodeId];
    selectedNode = null;
    
    // Hide properties panel
    hideProperties();
    
    showNotification('Node deleted');
  } else if (selectedEdge) {
    const edgeId = selectedEdge.getAttribute('id');
    
    // Delete edge
    selectedEdge.remove();
    delete edges[edgeId];
    selectedEdge = null;
    
    showNotification('Connection deleted');
  }
}

// Sample data functions
function loadAgents() {
  agents = [
    { id: 'agent1', name: 'ToolAgent', description: 'A general purpose agent' },
    { id: 'agent2', name: 'Travel Agent', description: 'Specialized in travel planning' }
  ];
}

function loadTools() {
  tools = [
    { id: 'tool1', name: 'Search Tool', description: 'Web search tool' },
    { id: 'tool2', name: 'Calculator', description: 'Math calculations' }
  ];
}

// Create a sample workflow
function createSampleWorkflow() {
  // Clear existing nodes/edges
  canvasContent.innerHTML = '';
  document.getElementById('connections-svg').innerHTML = '';
  
  const nodeSpacing = 250;
  const yPosition = 150;
  
  // Create input node
  const inputNode = createNode('INPUT', 100, yPosition);
  inputNode.name = 'When chat message received';
  
  // Create first agent node
  const agentNode1 = createNode('AGENT', 100 + nodeSpacing, yPosition);
  agentNode1.name = 'AI Agent';
  
  // Create second agent node
  const agentNode2 = createNode('AGENT', 100 + nodeSpacing * 2, yPosition);
  agentNode2.name = 'AI Agent1';
  
  // Create tool node
  const toolNode = createNode('TOOL', 100 + nodeSpacing * 3, yPosition);
  toolNode.name = 'Basic LLM Chain';
  
  // Create connections
  createConnection(inputNode.id, agentNode1.id);
  createConnection(agentNode1.id, agentNode2.id);
  createConnection(agentNode2.id, toolNode.id);
}

// Notification functions
function showNotification(message, isError = false) {
  // Remove existing notifications
  const existingNotifications = document.querySelectorAll('.notification');
  existingNotifications.forEach(note => note.remove());
  
  // Create notification
  const notification = document.createElement('div');
  notification.className = isError ? 'notification error' : 'notification';
  notification.textContent = message;
  
  document.body.appendChild(notification);
  
  // Auto-remove after 3 seconds
  setTimeout(() => notification.remove(), 3000);
}