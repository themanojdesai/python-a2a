// Flow Builder - Main JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const canvas = document.getElementById('canvas');
    const configPanel = document.getElementById('config-panel');
    const newAgentModal = document.getElementById('new-agent-modal');
    const connectionTooltip = document.getElementById('connection-tooltip');
    const emptyCanvasHelp = document.getElementById('empty-canvas-help');
    
    // Global variables
    let nodeCounter = 0;
    let nodes = [];
    let connections = [];
    let draggedCard = null;
    let selectedNode = null;
    let connectionStart = null;
    let connectionEnd = null;
    let isDragging = false;
    let dragOffsetX = 0;
    let dragOffsetY = 0;
    let canvasOffset = { x: 0, y: 0 };
    let canvasScale = 1;
    
    // SVG namespace
    const svgNS = "http://www.w3.org/2000/svg";
    
    // Create a node container for proper node positioning (adding first so it's below the connection layer)
    const nodeContainer = document.createElement("div");
    nodeContainer.setAttribute("id", "node-container");
    nodeContainer.style.position = "absolute";
    nodeContainer.style.top = "0";
    nodeContainer.style.left = "0";
    nodeContainer.style.width = "100%";
    nodeContainer.style.height = "100%";
    nodeContainer.style.zIndex = "1";
    canvas.appendChild(nodeContainer);
    
    // Create SVG element for connections (adding second so it's above the node container)
    const svgContainer = document.createElementNS(svgNS, "svg");
    svgContainer.setAttribute("id", "connections-container");
    svgContainer.style.position = "absolute";
    svgContainer.style.top = "0";
    svgContainer.style.left = "0";
    svgContainer.style.width = "100%";
    svgContainer.style.height = "100%";
    svgContainer.style.pointerEvents = "none";
    svgContainer.style.zIndex = "2";
    canvas.appendChild(svgContainer);
    
    // Initialize drag and drop for agent and tool cards
    initDragAndDrop();
    
    // Initialize canvas events
    initCanvasEvents();
    
    // Initialize UI controls
    initUIControls();
    
    // Initialize zoom and pan functionality
    initZoomAndPan();
    
    /**
     * Initialize drag and drop functionality for agent, tool, and IO cards
     */
    function initDragAndDrop() {
        const agentCards = document.querySelectorAll('.agent-card');
        const toolCards = document.querySelectorAll('.tool-card');
        const ioCards = document.querySelectorAll('.io-card');
        
        // Add drag functionality to agent cards
        agentCards.forEach(card => {
            card.addEventListener('dragstart', (e) => {
                draggedCard = {
                    type: 'agent',
                    agentType: card.getAttribute('data-type'),
                    element: card
                };
                
                // Create a ghost image for dragging
                const ghostElement = card.cloneNode(true);
                ghostElement.style.position = 'absolute';
                ghostElement.style.top = '-1000px';
                document.body.appendChild(ghostElement);
                e.dataTransfer.setDragImage(ghostElement, 0, 0);
                
                setTimeout(() => {
                    document.body.removeChild(ghostElement);
                }, 0);
            });
            
            card.addEventListener('dragend', () => {
                draggedCard = null;
            });
        });
        
        // Add drag functionality to tool cards
        toolCards.forEach(card => {
            card.addEventListener('dragstart', (e) => {
                draggedCard = {
                    type: 'tool',
                    toolType: card.getAttribute('data-type'),
                    element: card
                };
                
                // Create a ghost image for dragging
                const ghostElement = card.cloneNode(true);
                ghostElement.style.position = 'absolute';
                ghostElement.style.top = '-1000px';
                document.body.appendChild(ghostElement);
                e.dataTransfer.setDragImage(ghostElement, 0, 0);
                
                setTimeout(() => {
                    document.body.removeChild(ghostElement);
                }, 0);
            });
            
            card.addEventListener('dragend', () => {
                draggedCard = null;
            });
        });
        
        // Add drag functionality to IO cards
        ioCards.forEach(card => {
            card.addEventListener('dragstart', (e) => {
                draggedCard = {
                    type: card.getAttribute('data-type'), // 'input' or 'output'
                    element: card
                };
                
                // Create a ghost image for dragging
                const ghostElement = card.cloneNode(true);
                ghostElement.style.position = 'absolute';
                ghostElement.style.top = '-1000px';
                document.body.appendChild(ghostElement);
                e.dataTransfer.setDragImage(ghostElement, 0, 0);
                
                setTimeout(() => {
                    document.body.removeChild(ghostElement);
                }, 0);
            });
            
            card.addEventListener('dragend', () => {
                draggedCard = null;
            });
        });
        
        // Add drop functionality to the canvas
        canvas.addEventListener('dragover', (e) => {
            e.preventDefault();
        });
        
        canvas.addEventListener('drop', (e) => {
            e.preventDefault();
            
            if (draggedCard) {
                // Get canvas-relative position
                const rect = canvas.getBoundingClientRect();
                const x = (e.clientX - rect.left - canvasOffset.x) / canvasScale;
                const y = (e.clientY - rect.top - canvasOffset.y) / canvasScale;
                
                // Create a new node at the drop position
                createNode(x, y, draggedCard);
                
                // Remove the help text if it's the first node
                if (nodes.length === 1) {
                    emptyCanvasHelp.style.display = 'none';
                }
            }
        });
    }
    
    /**
     * Initialize canvas events for node selection and connection creation
     */
    function initCanvasEvents() {
        // Handle canvas click to deselect nodes
        canvas.addEventListener('click', (e) => {
            // Only deselect if the canvas itself was clicked, not a node
            if (e.target === canvas || e.target === svgContainer) {
                deselectAllNodes();
                hideConfigPanel();
            }
        });
    }
    
    /**
     * Initialize UI controls like buttons and panels
     */
    function initUIControls() {
        // Config panel
        const closeConfigBtn = document.getElementById('close-config');
        const applyConfigBtn = document.getElementById('apply-config');
        const cancelConfigBtn = document.getElementById('cancel-config');
        
        closeConfigBtn.addEventListener('click', hideConfigPanel);
        cancelConfigBtn.addEventListener('click', hideConfigPanel);
        applyConfigBtn.addEventListener('click', applyNodeConfig);
        
        // New agent modal
        const createAgentBtn = document.getElementById('create-agent-btn');
        const createAgentConfirmBtn = document.getElementById('create-agent-confirm');
        const createToolBtn = document.getElementById('create-tool-btn');
        const modalCloseButtons = document.querySelectorAll('.modal-close');
        const newAgentTypeSelect = document.getElementById('new-agent-type');
        const newAgentConfigContainer = document.getElementById('new-agent-config-container');
        
        createAgentBtn.addEventListener('click', showNewAgentModal);
        createAgentConfirmBtn.addEventListener('click', createNewAgent);
        createToolBtn.addEventListener('click', () => {
            // TODO: Implement create tool functionality
            alert('Create tool functionality will be implemented in the next phase.');
        });
        
        modalCloseButtons.forEach(btn => {
            btn.addEventListener('click', hideModals);
        });
        
        // Agent type change in modal
        newAgentTypeSelect.addEventListener('change', () => {
            updateNewAgentConfigFields(newAgentTypeSelect.value);
        });
        
        // Initialize with the first option
        updateNewAgentConfigFields(newAgentTypeSelect.value);
        
        // Toolbar buttons
        document.getElementById('add-input-btn').addEventListener('click', addInputNode);
        document.getElementById('add-output-btn').addEventListener('click', addOutputNode);
        document.getElementById('undo-btn').addEventListener('click', undoAction);
        document.getElementById('redo-btn').addEventListener('click', redoAction);
        document.getElementById('zoom-in-btn').addEventListener('click', zoomIn);
        document.getElementById('zoom-out-btn').addEventListener('click', zoomOut);
        document.getElementById('zoom-reset-btn').addEventListener('click', resetZoom);
        document.getElementById('delete-btn').addEventListener('click', deleteSelected);
        
        // Utility controls
        document.getElementById('floating-zoom-reset').addEventListener('click', resetZoom);
        
        // Canvas control buttons
        document.getElementById('floating-save-btn').addEventListener('click', saveNetwork);
        document.getElementById('floating-run-btn').addEventListener('click', runNetwork);
    }
    
    /**
     * Initialize zoom and pan functionality for the canvas
     */
    function initZoomAndPan() {
        let isPanning = false;
        let startPoint = { x: 0, y: 0 };
        
        // Handle panning with middle mouse button or spacebar + left mouse button
        canvas.addEventListener('mousedown', (e) => {
            // Middle mouse button (button 1) or spacebar + left button
            if (e.button === 1 || (e.button === 0 && e.getModifierState('Space'))) {
                isPanning = true;
                startPoint = { x: e.clientX, y: e.clientY };
                canvas.style.cursor = 'grabbing';
                e.preventDefault();
            }
        });
        
        window.addEventListener('mousemove', (e) => {
            if (isPanning) {
                const dx = e.clientX - startPoint.x;
                const dy = e.clientY - startPoint.y;
                
                canvasOffset.x += dx;
                canvasOffset.y += dy;
                
                updateCanvasTransform();
                
                startPoint = { x: e.clientX, y: e.clientY };
            }
        });
        
        window.addEventListener('mouseup', () => {
            if (isPanning) {
                isPanning = false;
                canvas.style.cursor = 'default';
            }
        });
        
        // Handle zooming with mouse wheel
        canvas.addEventListener('wheel', (e) => {
            e.preventDefault();
            
            const delta = e.deltaY < 0 ? 0.1 : -0.1;
            const newScale = Math.min(Math.max(canvasScale + delta, 0.3), 2);
            
            // Calculate the position under the mouse (in canvas space)
            const rect = canvas.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;
            
            // Calculate the point in world space
            const worldX = (mouseX - canvasOffset.x) / canvasScale;
            const worldY = (mouseY - canvasOffset.y) / canvasScale;
            
            // Update the scale
            canvasScale = newScale;
            
            // Calculate the new offset to keep the point under the mouse
            canvasOffset.x = mouseX - worldX * canvasScale;
            canvasOffset.y = mouseY - worldY * canvasScale;
            
            updateCanvasTransform();
        });
    }
    
    /**
     * Update canvas transform based on offset and scale
     */
    function updateCanvasTransform() {
        // Apply transformation only to the node container and SVG container
        const nodeContainerEl = document.getElementById('node-container');
        const svgContainerEl = document.getElementById('connections-container');
        
        nodeContainerEl.style.transform = `translate(${canvasOffset.x}px, ${canvasOffset.y}px) scale(${canvasScale})`;
        svgContainerEl.style.transform = `translate(${canvasOffset.x}px, ${canvasOffset.y}px) scale(${canvasScale})`;
    }
    
    /**
     * Create a new node on the canvas
     * @param {number} x - The x position on the canvas
     * @param {number} y - The y position on the canvas
     * @param {Object} cardData - The data for the card being dropped
     */
    function createNode(x, y, cardData) {
        const nodeId = 'node-' + (++nodeCounter);
        const nodeElement = document.createElement('div');
        nodeElement.id = nodeId;
        nodeElement.classList.add('node');
        
        // Add appropriate class based on type
        if (cardData.type === 'agent') {
            nodeElement.classList.add('agent');
            
            // Get icon and type-specific data
            let icon = 'robot';
            let typeName = 'Agent';
            
            switch (cardData.agentType) {
                case 'openai':
                    typeName = 'OpenAI';
                    break;
                case 'anthropic':
                    typeName = 'Claude';
                    break;
                case 'bedrock':
                    typeName = 'Bedrock';
                    break;
                case 'custom':
                    typeName = 'Custom';
                    icon = 'code-square';
                    break;
            }
            
            nodeElement.innerHTML = `
                <div class="node-header">
                    <div class="node-title">
                        <i class="bi bi-${icon}"></i>
                        <span>${typeName} Agent</span>
                    </div>
                    <div class="node-actions">
                        <button class="node-btn configure-node" title="Configure"><i class="bi bi-gear"></i></button>
                        <button class="node-btn delete-node" title="Delete"><i class="bi bi-trash"></i></button>
                        <button class="node-btn" title="Duplicate"><i class="bi bi-copy"></i></button>
                    </div>
                </div>
                <div class="node-content">
                    <div>Configure this agent</div>
                    <div class="node-badge agent-model">Not configured</div>
                </div>
                <div class="node-ports">
                    <div class="input-port">
                        <div class="port port-left" data-port-type="input"></div>
                        <span class="port-label">Input</span>
                    </div>
                    <div class="output-port">
                        <div class="port port-right" data-port-type="output"></div>
                        <span class="port-label">Output</span>
                    </div>
                </div>
            `;
        } else if (cardData.type === 'tool') {
            nodeElement.classList.add('tool');
            
            // Get icon and type-specific data
            let icon = 'tools';
            let typeName = 'Tool';
            
            switch (cardData.toolType) {
                case 'search':
                    typeName = 'Search';
                    icon = 'search';
                    break;
                case 'calculator':
                    typeName = 'Calculator';
                    icon = 'calculator';
                    break;
                case 'database':
                    typeName = 'Database';
                    icon = 'database';
                    break;
            }
            
            nodeElement.innerHTML = `
                <div class="node-header">
                    <div class="node-title">
                        <i class="bi bi-${icon}"></i>
                        <span>${typeName} Tool</span>
                    </div>
                    <div class="node-actions">
                        <button class="node-btn configure-node" title="Configure"><i class="bi bi-gear"></i></button>
                        <button class="node-btn delete-node" title="Delete"><i class="bi bi-trash"></i></button>
                        <button class="node-btn" title="Duplicate"><i class="bi bi-copy"></i></button>
                    </div>
                </div>
                <div class="node-content">
                    <div>Configure this tool</div>
                </div>
                <div class="node-ports">
                    <div class="input-port">
                        <div class="port port-left" data-port-type="input"></div>
                        <span class="port-label">Input</span>
                    </div>
                    <div class="output-port">
                        <div class="port port-right" data-port-type="output"></div>
                        <span class="port-label">Output</span>
                    </div>
                </div>
            `;
        } else if (cardData.type === 'input') {
            nodeElement.classList.add('input');
            
            nodeElement.innerHTML = `
                <div class="node-header">
                    <div class="node-title">
                        <i class="bi bi-box-arrow-in-right"></i>
                        <span>Input</span>
                    </div>
                    <div class="node-actions">
                        <button class="node-btn configure-node" title="Configure"><i class="bi bi-gear"></i></button>
                        <button class="node-btn delete-node" title="Delete"><i class="bi bi-trash"></i></button>
                    </div>
                </div>
                <div class="node-content">
                    <div>Network input</div>
                </div>
                <div class="node-ports">
                    <div class="output-port">
                        <span class="port-label">Output</span>
                        <div class="port port-right" data-port-type="output"></div>
                    </div>
                </div>
            `;
        } else if (cardData.type === 'output') {
            nodeElement.classList.add('output');
            
            nodeElement.innerHTML = `
                <div class="node-header">
                    <div class="node-title">
                        <i class="bi bi-box-arrow-right"></i>
                        <span>Output</span>
                    </div>
                    <div class="node-actions">
                        <button class="node-btn configure-node" title="Configure"><i class="bi bi-gear"></i></button>
                        <button class="node-btn delete-node" title="Delete"><i class="bi bi-trash"></i></button>
                    </div>
                </div>
                <div class="node-content">
                    <div>Network output</div>
                </div>
                <div class="node-ports">
                    <div class="input-port">
                        <div class="port port-left" data-port-type="input"></div>
                        <span class="port-label">Input</span>
                    </div>
                </div>
            `;
        }
        
        // Position the node
        nodeElement.style.left = `${x}px`;
        nodeElement.style.top = `${y}px`;
        
        // Add the node to the node container
        nodeContainer.appendChild(nodeElement);
        
        // Store node data
        const nodeData = {
            id: nodeId,
            element: nodeElement,
            type: cardData.type,
            subType: cardData.type === 'agent' ? cardData.agentType : 
                   (cardData.type === 'tool' ? cardData.toolType : null),
            position: { x, y },
            config: {}
        };
        
        nodes.push(nodeData);
        
        // Add event listeners to the node
        initNodeEvents(nodeElement, nodeData);
        
        return nodeData;
    }
    
    /**
     * Initialize events for a node
     * @param {HTMLElement} nodeElement - The DOM element for the node
     * @param {Object} nodeData - The data object for the node
     */
    function initNodeEvents(nodeElement, nodeData) {
        // Make the node draggable with jQuery-like approach
        nodeElement.addEventListener('mousedown', (e) => {
            // Ignore if clicking on a port or button
            if (e.target.classList.contains('port') || 
                e.target.classList.contains('node-btn') ||
                e.target.parentElement.classList.contains('node-btn')) {
                return;
            }
            
            // Get node position relative to canvas
            const canvasRect = canvas.getBoundingClientRect();
            const nodeRect = nodeElement.getBoundingClientRect();
            
            dragOffsetX = e.clientX - nodeRect.left;
            dragOffsetY = e.clientY - nodeRect.top;
            
            selectedNode = nodeData;
            isDragging = true;
            
            // Add selected class
            deselectAllNodes();
            nodeElement.classList.add('selected');
            
            // Apply higher z-index when dragging to be above the connection layer
            nodeElement.style.zIndex = '10';
            
            // Add mousemove and mouseup handlers to document
            const mouseMoveHandler = (moveEvent) => {
                if (isDragging) {
                    // Calculate the new position in canvas coordinates
                    const x = (moveEvent.clientX - canvasRect.left - dragOffsetX) / canvasScale;
                    const y = (moveEvent.clientY - canvasRect.top - dragOffsetY) / canvasScale;
                    
                    // Update node position immediately
                    nodeElement.style.left = `${x}px`;
                    nodeElement.style.top = `${y}px`;
                    nodeData.position = { x, y };
                    
                    // Update connections
                    updateConnections();
                }
            };
            
            const mouseUpHandler = () => {
                isDragging = false;
                nodeElement.style.zIndex = '';
                document.removeEventListener('mousemove', mouseMoveHandler);
                document.removeEventListener('mouseup', mouseUpHandler);
            };
            
            document.addEventListener('mousemove', mouseMoveHandler);
            document.addEventListener('mouseup', mouseUpHandler);
            
            e.stopPropagation();
        });
        
        // Handle node selection
        nodeElement.addEventListener('click', (e) => {
            // Ignore if clicking on a port or button
            if (e.target.classList.contains('port') || 
                e.target.classList.contains('node-btn') ||
                e.target.parentElement.classList.contains('node-btn')) {
                return;
            }
            
            deselectAllNodes();
            nodeElement.classList.add('selected');
            selectedNode = nodeData;
            
            e.stopPropagation();
        });
        
        // Configure button
        const configureBtn = nodeElement.querySelector('.configure-node');
        if (configureBtn) {
            configureBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                deselectAllNodes();
                nodeElement.classList.add('selected');
                selectedNode = nodeData;
                
                showConfigPanel(nodeData);
            });
        }
        
        // Delete button
        const deleteBtn = nodeElement.querySelector('.delete-node');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                // Find all connections to this node
                const relatedConnections = connections.filter(conn => 
                    conn.start.nodeId === nodeData.id || conn.end.nodeId === nodeData.id
                );
                
                // Remove connections
                relatedConnections.forEach(conn => {
                    svgContainer.removeChild(conn.element);
                    connections = connections.filter(c => c.id !== conn.id);
                });
                
                // Remove node
                nodeContainer.removeChild(nodeElement);
                nodes = nodes.filter(n => n.id !== nodeData.id);
                
                // Show help text if no nodes left
                if (nodes.length === 0) {
                    emptyCanvasHelp.style.display = 'flex';
                }
            });
        }
        
        // Add port event listeners for connections
        const ports = nodeElement.querySelectorAll('.port');
        
        ports.forEach(port => {
            // Start connection
            port.addEventListener('mousedown', (e) => {
                e.stopPropagation();
                
                const portType = port.getAttribute('data-port-type');
                const portRect = port.getBoundingClientRect();
                const canvasRect = canvas.getBoundingClientRect();
                
                // Calculate port center position in canvas coordinates
                const startX = (portRect.left + portRect.width / 2 - canvasRect.left - canvasOffset.x) / canvasScale;
                const startY = (portRect.top + portRect.height / 2 - canvasRect.top - canvasOffset.y) / canvasScale;
                
                connectionStart = {
                    nodeId: nodeData.id,
                    port: portType,
                    x: startX,
                    y: startY
                };
                
                // Create temporary connection line
                const tempConnection = document.createElementNS(svgNS, 'path');
                tempConnection.setAttribute('id', 'temp-connection');
                tempConnection.setAttribute('class', 'temp-connection');
                svgContainer.appendChild(tempConnection);
                
                // Show connection tooltip
                connectionTooltip.style.opacity = '1';
                connectionTooltip.textContent = 'Click on another port to connect';
                
                e.preventDefault();
            });
            
            // End connection
            port.addEventListener('mouseup', (e) => {
                e.stopPropagation();
                
                if (connectionStart) {
                    const portType = port.getAttribute('data-port-type');
                    const portRect = port.getBoundingClientRect();
                    const canvasRect = canvas.getBoundingClientRect();
                    
                    // Calculate port center position in canvas coordinates
                    const endX = (portRect.left + portRect.width / 2 - canvasRect.left - canvasOffset.x) / canvasScale;
                    const endY = (portRect.top + portRect.height / 2 - canvasRect.top - canvasOffset.y) / canvasScale;
                    
                    connectionEnd = {
                        nodeId: nodeData.id,
                        port: portType,
                        x: endX,
                        y: endY
                    };
                    
                    // Only create connection if:
                    // 1. Not connecting to the same node
                    // 2. Connecting from output to input
                    if (connectionStart.nodeId !== connectionEnd.nodeId &&
                        ((connectionStart.port === 'output' && connectionEnd.port === 'input') ||
                         (connectionStart.port === 'input' && connectionEnd.port === 'output'))) {
                        
                        // Ensure start is always the output port
                        if (connectionStart.port === 'input') {
                            const temp = connectionStart;
                            connectionStart = connectionEnd;
                            connectionEnd = temp;
                        }
                        
                        createConnection(connectionStart, connectionEnd);
                    }
                    
                    // Remove temporary connection
                    const tempConnection = document.getElementById('temp-connection');
                    if (tempConnection) {
                        svgContainer.removeChild(tempConnection);
                    }
                    
                    // Hide tooltip
                    connectionTooltip.style.opacity = '0';
                    
                    connectionStart = null;
                    connectionEnd = null;
                }
            });
            
            // Hover effect
            port.addEventListener('mouseenter', () => {
                connectionTooltip.style.opacity = '1';
                const rect = port.getBoundingClientRect();
                
                connectionTooltip.style.left = `${rect.left + rect.width / 2}px`;
                connectionTooltip.style.top = `${rect.top - 30}px`;
                
                const portType = port.getAttribute('data-port-type');
                if (connectionStart) {
                    if ((connectionStart.port === 'output' && portType === 'input') ||
                        (connectionStart.port === 'input' && portType === 'output')) {
                        connectionTooltip.textContent = 'Click to connect';
                    } else {
                        connectionTooltip.textContent = 'Invalid connection';
                    }
                } else {
                    connectionTooltip.textContent = portType === 'input' ? 'Input port' : 'Output port';
                }
            });
            
            port.addEventListener('mouseleave', () => {
                if (!connectionStart) {
                    connectionTooltip.style.opacity = '0';
                }
            });
        });
    }
    
    /**
     * Create a connection between two nodes
     * @param {Object} start - The starting port information
     * @param {Object} end - The ending port information
     */
    function createConnection(start, end) {
        const uniqueId = Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
        const connectionId = `connection-${start.nodeId}-${end.nodeId}-${uniqueId}`;
        
        // Check if connection already exists between these exact nodes
        // We only block duplicate connections between the same exact ports/nodes
        const existingConnection = connections.find(conn => 
            (conn.start.nodeId === start.nodeId && conn.end.nodeId === end.nodeId && 
             conn.start.port === start.port && conn.end.port === end.port) || 
            (conn.start.nodeId === end.nodeId && conn.end.nodeId === start.nodeId &&
             conn.start.port === end.port && conn.end.port === start.port)
        );
        
        if (existingConnection) {
            return;
        }
        
        // Create SVG path for the connection
        const path = document.createElementNS(svgNS, 'path');
        path.setAttribute('id', connectionId);
        path.setAttribute('class', 'connection');
        
        // Calculate the path with improved bezier curve control points
        const dx = end.x - start.x;
        const dy = end.y - start.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        // Use dynamic control point distances based on connection length
        const bezierX = Math.min(Math.abs(dx) * 0.5, distance * 0.4);
        const bezierY = Math.min(Math.abs(dy) * 0.2, distance * 0.1);
        
        // Create smoother S-curved path
        const d = `M ${start.x},${start.y} 
                   C ${start.x + bezierX},${start.y + bezierY} 
                     ${end.x - bezierX},${end.y - bezierY} 
                     ${end.x},${end.y}`;
        path.setAttribute('d', d);
        
        svgContainer.appendChild(path);
        
        // Store connection data
        const connectionData = {
            id: connectionId,
            element: path,
            start: {
                nodeId: start.nodeId,
                port: start.port,
                x: start.x,
                y: start.y
            },
            end: {
                nodeId: end.nodeId,
                port: end.port,
                x: end.x,
                y: end.y
            }
        };
        
        connections.push(connectionData);
        
        // Add click event to select the connection
        path.addEventListener('click', (e) => {
            e.stopPropagation();
            deselectAllNodes();
            path.classList.add('selected');
            
            // Show button to delete connection
            const rect = path.getBoundingClientRect();
            const centerX = (rect.left + rect.right) / 2;
            const centerY = (rect.top + rect.bottom) / 2;
            
            // Create delete button for connection if it doesn't exist
            let deleteBtn = document.getElementById(`delete-${connectionId}`);
            if (!deleteBtn) {
                deleteBtn = document.createElement('button');
                deleteBtn.setAttribute('id', `delete-${connectionId}`);
                deleteBtn.classList.add('connection-delete-btn');
                deleteBtn.innerHTML = '<i class="bi bi-x-circle-fill"></i>';
                deleteBtn.style.position = 'absolute';
                deleteBtn.style.left = `${centerX}px`;
                deleteBtn.style.top = `${centerY}px`;
                deleteBtn.style.zIndex = '100';
                document.body.appendChild(deleteBtn);
                
                deleteBtn.addEventListener('click', () => {
                    // Remove connection
                    svgContainer.removeChild(path);
                    connections = connections.filter(c => c.id !== connectionId);
                    document.body.removeChild(deleteBtn);
                });
            }
            
            // Remove button when clicking elsewhere
            const removeBtn = () => {
                if (deleteBtn && document.body.contains(deleteBtn)) {
                    document.body.removeChild(deleteBtn);
                }
                canvas.removeEventListener('click', removeBtn);
            };
            
            canvas.addEventListener('click', removeBtn);
        });
        
        return connectionData;
    }
    
    /**
     * Update a temporary connection while dragging
     * @param {number} endX - The current mouse X position
     * @param {number} endY - The current mouse Y position
     */
    function updateTempConnection(endX, endY) {
        if (!connectionStart) return;
        
        const tempConnection = document.getElementById('temp-connection');
        if (!tempConnection) return;
        
        const dx = endX - connectionStart.x;
        const dy = endY - connectionStart.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        // Use dynamic control point distances based on connection length
        const bezierX = Math.min(Math.abs(dx) * 0.5, distance * 0.4);
        const bezierY = Math.min(Math.abs(dy) * 0.2, distance * 0.1);
        
        // Create smoother S-curved path
        const d = `M ${connectionStart.x},${connectionStart.y} 
                   C ${connectionStart.x + bezierX},${connectionStart.y + bezierY} 
                     ${endX - bezierX},${endY - bezierY} 
                     ${endX},${endY}`;
        tempConnection.setAttribute('d', d);
    }
    
    /**
     * Update all connection paths when nodes are moved
     */
    function updateConnections() {
        connections.forEach(conn => {
            // Get the current port positions
            const startNode = nodes.find(n => n.id === conn.start.nodeId);
            const endNode = nodes.find(n => n.id === conn.end.nodeId);
            
            if (startNode && endNode) {
                const startElement = startNode.element.querySelector(`.port[data-port-type="${conn.start.port}"]`);
                const endElement = endNode.element.querySelector(`.port[data-port-type="${conn.end.port}"]`);
                
                if (startElement && endElement) {
                    const startRect = startElement.getBoundingClientRect();
                    const endRect = endElement.getBoundingClientRect();
                    const canvasRect = canvas.getBoundingClientRect();
                    
                    const startX = (startRect.left + startRect.width / 2 - canvasRect.left - canvasOffset.x) / canvasScale;
                    const startY = (startRect.top + startRect.height / 2 - canvasRect.top - canvasOffset.y) / canvasScale;
                    const endX = (endRect.left + endRect.width / 2 - canvasRect.left - canvasOffset.x) / canvasScale;
                    const endY = (endRect.top + endRect.height / 2 - canvasRect.top - canvasOffset.y) / canvasScale;
                    
                    // Update path with improved bezier curve
                    const dx = endX - startX;
                    const dy = endY - startY;
                    const distance = Math.sqrt(dx * dx + dy * dy);
                    
                    // Use dynamic control point distances based on connection length
                    const bezierX = Math.min(Math.abs(dx) * 0.5, distance * 0.4);
                    const bezierY = Math.min(Math.abs(dy) * 0.2, distance * 0.1);
                    
                    // Create smoother S-curved path
                    const d = `M ${startX},${startY} 
                               C ${startX + bezierX},${startY + bezierY} 
                                 ${endX - bezierX},${endY - bezierY} 
                                 ${endX},${endY}`;
                    conn.element.setAttribute('d', d);
                    
                    // Update stored coordinates
                    conn.start.x = startX;
                    conn.start.y = startY;
                    conn.end.x = endX;
                    conn.end.y = endY;
                }
            }
        });
    }
    
    /**
     * Show the configuration panel for a node
     * @param {Object} nodeData - The node to configure
     */
    function showConfigPanel(nodeData) {
        const configPanel = document.getElementById('config-panel');
        const configTitle = document.getElementById('config-title');
        const nodeNameInput = document.getElementById('node-name');
        
        // Set title based on node type
        configTitle.textContent = nodeData.type === 'agent' ? 'Configure Agent' : 'Configure Tool';
        
        // Set current node name or default
        nodeNameInput.value = nodeData.config.name || '';
        
        // Hide all config sections first
        document.querySelectorAll('.agent-specific-config').forEach(section => {
            section.style.display = 'none';
        });
        
        // Show appropriate config section for agent type
        if (nodeData.type === 'agent') {
            const configSection = document.getElementById(`${nodeData.subType}-config`);
            if (configSection) {
                configSection.style.display = 'block';
            }
            
            // Fill in saved config values
            if (nodeData.subType === 'openai') {
                document.getElementById('openai-api-key').value = nodeData.config.apiKey || '';
                document.getElementById('openai-model').value = nodeData.config.model || 'gpt-4o';
                document.getElementById('openai-system-message').value = nodeData.config.systemMessage || 'You are a helpful AI assistant.';
            } else if (nodeData.subType === 'anthropic') {
                document.getElementById('anthropic-api-key').value = nodeData.config.apiKey || '';
                document.getElementById('anthropic-model').value = nodeData.config.model || 'claude-3-opus';
                document.getElementById('anthropic-system-message').value = nodeData.config.systemMessage || 'You are Claude, an AI assistant by Anthropic.';
            } else if (nodeData.subType === 'bedrock') {
                document.getElementById('aws-access-key').value = nodeData.config.accessKey || '';
                document.getElementById('aws-secret-key').value = nodeData.config.secretKey || '';
                document.getElementById('aws-region').value = nodeData.config.region || 'us-east-1';
                document.getElementById('bedrock-model').value = nodeData.config.model || 'anthropic.claude-3-sonnet-20240229-v1:0';
                document.getElementById('bedrock-system-message').value = nodeData.config.systemMessage || 'You are an AI assistant.';
            } else if (nodeData.subType === 'custom') {
                document.getElementById('agent-port').value = nodeData.config.port || '';
                document.getElementById('agent-endpoint').value = nodeData.config.endpoint || '';
                document.getElementById('agent-script').value = nodeData.config.script || '';
            }
        } else {
            // Tool configuration will be implemented in the next phase
        }
        
        // Show the panel
        configPanel.classList.add('open');
    }
    
    /**
     * Hide the configuration panel
     */
    function hideConfigPanel() {
        const configPanel = document.getElementById('config-panel');
        configPanel.classList.remove('open');
    }
    
    /**
     * Apply node configuration from the panel
     */
    function applyNodeConfig() {
        if (!selectedNode) return;
        
        // Get common config values
        const nodeName = document.getElementById('node-name').value;
        
        // Validate required fields
        let validationErrors = [];
        
        // Require a name for all nodes
        if (!nodeName || nodeName.trim() === '') {
            validationErrors.push('Node name is required');
        }
        
        // Get and validate type-specific config
        if (selectedNode.type === 'agent') {
            if (selectedNode.subType === 'openai') {
                const apiKey = document.getElementById('openai-api-key').value;
                const model = document.getElementById('openai-model').value;
                const systemMessage = document.getElementById('openai-system-message').value;
                
                if (!apiKey || apiKey.trim() === '') {
                    validationErrors.push('OpenAI API Key is required');
                }
                
                if (!model) {
                    validationErrors.push('Please select a model');
                }
                
                // Store values if validation passes
                if (validationErrors.length === 0) {
                    selectedNode.config.apiKey = apiKey;
                    selectedNode.config.model = model;
                    selectedNode.config.systemMessage = systemMessage;
                }
            } else if (selectedNode.subType === 'anthropic') {
                const apiKey = document.getElementById('anthropic-api-key').value;
                const model = document.getElementById('anthropic-model').value;
                const systemMessage = document.getElementById('anthropic-system-message').value;
                
                if (!apiKey || apiKey.trim() === '') {
                    validationErrors.push('Anthropic API Key is required');
                }
                
                if (!model) {
                    validationErrors.push('Please select a model');
                }
                
                // Store values if validation passes
                if (validationErrors.length === 0) {
                    selectedNode.config.apiKey = apiKey;
                    selectedNode.config.model = model;
                    selectedNode.config.systemMessage = systemMessage;
                }
            } else if (selectedNode.subType === 'bedrock') {
                const accessKey = document.getElementById('aws-access-key').value;
                const secretKey = document.getElementById('aws-secret-key').value;
                const region = document.getElementById('aws-region').value;
                const model = document.getElementById('bedrock-model').value;
                const systemMessage = document.getElementById('bedrock-system-message').value;
                
                if (!accessKey || accessKey.trim() === '') {
                    validationErrors.push('AWS Access Key is required');
                }
                
                if (!secretKey || secretKey.trim() === '') {
                    validationErrors.push('AWS Secret Key is required');
                }
                
                if (!region) {
                    validationErrors.push('Please select an AWS region');
                }
                
                if (!model) {
                    validationErrors.push('Please select a model');
                }
                
                // Store values if validation passes
                if (validationErrors.length === 0) {
                    selectedNode.config.accessKey = accessKey;
                    selectedNode.config.secretKey = secretKey;
                    selectedNode.config.region = region;
                    selectedNode.config.model = model;
                    selectedNode.config.systemMessage = systemMessage;
                }
            } else if (selectedNode.subType === 'custom') {
                const port = document.getElementById('agent-port').value;
                const endpoint = document.getElementById('agent-endpoint').value;
                const script = document.getElementById('agent-script').value;
                
                if ((!port || port === '') && (!endpoint || endpoint.trim() === '')) {
                    validationErrors.push('Either Port or Endpoint URL is required');
                }
                
                // Store values if validation passes
                if (validationErrors.length === 0) {
                    selectedNode.config.port = port;
                    selectedNode.config.endpoint = endpoint;
                    selectedNode.config.script = script;
                }
            }
        } else {
            // Tool-specific validations will be implemented in the next phase
        }
        
        // If validation fails, show errors and return
        if (validationErrors.length > 0) {
            validationErrors.forEach(error => {
                showNotification(error, 'error');
            });
            return;
        }
        
        // Apply common config
        selectedNode.config.name = nodeName;
        
        // Update node display with config info
        if (selectedNode.type === 'agent') {
            const nodeNameElement = selectedNode.element.querySelector('.node-title span');
            if (nodeNameElement && selectedNode.config.name) {
                nodeNameElement.textContent = selectedNode.config.name;
            }
            
            // Update model badge
            const modelBadge = selectedNode.element.querySelector('.agent-model');
            if (modelBadge) {
                let modelText = 'Not configured';
                
                if (selectedNode.subType === 'openai' && selectedNode.config.model) {
                    modelText = selectedNode.config.model;
                } else if (selectedNode.subType === 'anthropic' && selectedNode.config.model) {
                    modelText = selectedNode.config.model;
                } else if (selectedNode.subType === 'bedrock' && selectedNode.config.model) {
                    modelText = selectedNode.config.model.split('.')[1]?.split('-')[0] || selectedNode.config.model;
                } else if (selectedNode.subType === 'custom' && selectedNode.config.port) {
                    modelText = `Port: ${selectedNode.config.port}`;
                } else if (selectedNode.subType === 'custom' && selectedNode.config.endpoint) {
                    modelText = `URL: ${selectedNode.config.endpoint.substring(0, 15)}...`;
                }
                
                modelBadge.textContent = modelText;
            }
            
            // Show success notification
            showNotification(`${selectedNode.config.name} configuration updated`, 'success');
        } else {
            // Tool-specific updates will be implemented in the next phase
        }
        
        hideConfigPanel();
    }
    
    /**
     * Show the new agent modal
     */
    function showNewAgentModal() {
        newAgentModal.classList.add('open');
    }
    
    /**
     * Hide all modals
     */
    function hideModals() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.remove('open');
        });
    }
    
    /**
     * Update config fields in the new agent modal based on selected type
     * @param {string} agentType - The selected agent type
     */
    function updateNewAgentConfigFields(agentType) {
        const container = document.getElementById('new-agent-config-container');
        let configHtml = '';
        
        if (agentType === 'openai') {
            configHtml = `
                <div class="form-group">
                    <label for="new-openai-api-key">OpenAI API Key</label>
                    <input type="password" id="new-openai-api-key" class="form-control" placeholder="sk-...">
                </div>
                <div class="form-group">
                    <label for="new-openai-model">Model</label>
                    <select id="new-openai-model" class="form-control">
                        <option value="gpt-4o">GPT-4o</option>
                        <option value="gpt-4-turbo">GPT-4 Turbo</option>
                        <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                    </select>
                </div>
            `;
        } else if (agentType === 'anthropic') {
            configHtml = `
                <div class="form-group">
                    <label for="new-anthropic-api-key">Anthropic API Key</label>
                    <input type="password" id="new-anthropic-api-key" class="form-control" placeholder="sk_ant-...">
                </div>
                <div class="form-group">
                    <label for="new-anthropic-model">Model</label>
                    <select id="new-anthropic-model" class="form-control">
                        <option value="claude-3-opus">Claude 3 Opus</option>
                        <option value="claude-3-sonnet">Claude 3 Sonnet</option>
                        <option value="claude-3-haiku">Claude 3 Haiku</option>
                    </select>
                </div>
            `;
        } else if (agentType === 'bedrock') {
            configHtml = `
                <div class="form-group">
                    <label for="new-aws-access-key">AWS Access Key</label>
                    <input type="password" id="new-aws-access-key" class="form-control">
                </div>
                <div class="form-group">
                    <label for="new-aws-secret-key">AWS Secret Key</label>
                    <input type="password" id="new-aws-secret-key" class="form-control">
                </div>
                <div class="form-group">
                    <label for="new-aws-region">AWS Region</label>
                    <select id="new-aws-region" class="form-control">
                        <option value="us-east-1">US East (N. Virginia)</option>
                        <option value="us-west-2">US West (Oregon)</option>
                        <option value="eu-west-1">EU (Ireland)</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="new-bedrock-model">Model</label>
                    <select id="new-bedrock-model" class="form-control">
                        <option value="anthropic.claude-3-sonnet-20240229-v1:0">Claude 3 Sonnet</option>
                        <option value="anthropic.claude-3-haiku-20240307-v1:0">Claude 3 Haiku</option>
                        <option value="amazon.titan-text-express-v1">Titan Text</option>
                    </select>
                </div>
            `;
        } else if (agentType === 'custom') {
            configHtml = `
                <div class="form-group">
                    <label for="new-agent-port">Port</label>
                    <input type="number" id="new-agent-port" class="form-control" placeholder="8000" min="1024" max="65535">
                </div>
                <div class="form-group">
                    <label for="new-agent-endpoint">Endpoint URL (optional)</label>
                    <input type="text" id="new-agent-endpoint" class="form-control" placeholder="http://localhost:{port}">
                </div>
                <div class="form-group">
                    <label for="new-agent-script">Script Path (optional)</label>
                    <input type="text" id="new-agent-script" class="form-control" placeholder="/path/to/agent.py">
                </div>
            `;
        }
        
        container.innerHTML = configHtml;
    }
    
    /**
     * Create a new agent from the modal
     */
    function createNewAgent() {
        const agentName = document.getElementById('new-agent-name').value;
        const agentType = document.getElementById('new-agent-type').value;
        
        if (!agentName) {
            alert('Please enter a name for your agent');
            return;
        }
        
        // Get the center of the visible canvas
        const canvasRect = canvas.getBoundingClientRect();
        const x = ((canvasRect.width / 2) - canvasOffset.x) / canvasScale;
        const y = ((canvasRect.height / 2) - canvasOffset.y) / canvasScale;
        
        // Create the node
        const nodeData = createNode(x, y, { 
            type: 'agent', 
            agentType: agentType 
        });
        
        // Configure the node
        nodeData.config.name = agentName;
        
        if (agentType === 'openai') {
            nodeData.config.apiKey = document.getElementById('new-openai-api-key')?.value || '';
            nodeData.config.model = document.getElementById('new-openai-model')?.value || 'gpt-4o';
        } else if (agentType === 'anthropic') {
            nodeData.config.apiKey = document.getElementById('new-anthropic-api-key')?.value || '';
            nodeData.config.model = document.getElementById('new-anthropic-model')?.value || 'claude-3-opus';
        } else if (agentType === 'bedrock') {
            nodeData.config.accessKey = document.getElementById('new-aws-access-key')?.value || '';
            nodeData.config.secretKey = document.getElementById('new-aws-secret-key')?.value || '';
            nodeData.config.region = document.getElementById('new-aws-region')?.value || 'us-east-1';
            nodeData.config.model = document.getElementById('new-bedrock-model')?.value || 'anthropic.claude-3-sonnet-20240229-v1:0';
        } else if (agentType === 'custom') {
            nodeData.config.port = document.getElementById('new-agent-port')?.value || '';
            nodeData.config.endpoint = document.getElementById('new-agent-endpoint')?.value || '';
            nodeData.config.script = document.getElementById('new-agent-script')?.value || '';
        }
        
        // Update node display
        const nodeNameElement = nodeData.element.querySelector('.node-title span');
        if (nodeNameElement) {
            nodeNameElement.textContent = agentName;
        }
        
        // Update model badge
        const modelBadge = nodeData.element.querySelector('.agent-model');
        if (modelBadge) {
            let modelText = 'Not configured';
            
            if (agentType === 'openai' && nodeData.config.model) {
                modelText = nodeData.config.model;
            } else if (agentType === 'anthropic' && nodeData.config.model) {
                modelText = nodeData.config.model;
            } else if (agentType === 'bedrock' && nodeData.config.model) {
                modelText = nodeData.config.model.split('.')[1]?.split('-')[0] || nodeData.config.model;
            } else if (agentType === 'custom' && nodeData.config.port) {
                modelText = `Port: ${nodeData.config.port}`;
            }
            
            modelBadge.textContent = modelText;
        }
        
        // Remove the help text if it's the first node
        if (nodes.length === 1) {
            emptyCanvasHelp.style.display = 'none';
        }
        
        hideModals();
    }
    
    /**
     * Add an input node to the canvas
     */
    function addInputNode() {
        // Get the center of the visible canvas
        const canvasRect = canvas.getBoundingClientRect();
        const x = ((canvasRect.width / 3) - canvasOffset.x) / canvasScale;
        const y = ((canvasRect.height / 2) - canvasOffset.y) / canvasScale;
        
        const nodeId = 'node-' + (++nodeCounter);
        const nodeElement = document.createElement('div');
        nodeElement.id = nodeId;
        nodeElement.classList.add('node', 'input');
        
        nodeElement.innerHTML = `
            <div class="node-header">
                <div class="node-title">
                    <i class="bi bi-box-arrow-in-right"></i>
                    <span>Input</span>
                </div>
                <div class="node-actions">
                    <button class="node-btn configure-node" title="Configure"><i class="bi bi-gear"></i></button>
                </div>
            </div>
            <div class="node-content">
                <div>Network input</div>
            </div>
            <div class="node-ports">
                <div class="output-port">
                    <div class="port port-right" data-port-type="output"></div>
                    <span class="port-label">Output</span>
                </div>
            </div>
        `;
        
        // Position the node
        nodeElement.style.left = `${x}px`;
        nodeElement.style.top = `${y}px`;
        
        // Add the node to the canvas
        canvas.appendChild(nodeElement);
        
        // Store node data
        const nodeData = {
            id: nodeId,
            element: nodeElement,
            type: 'input',
            position: { x, y },
            config: {
                name: 'Input'
            }
        };
        
        nodes.push(nodeData);
        
        // Add event listeners to the node
        initNodeEvents(nodeElement, nodeData);
        
        // Remove the help text if it's the first node
        if (nodes.length === 1) {
            emptyCanvasHelp.style.display = 'none';
        }
        
        return nodeData;
    }
    
    /**
     * Add an output node to the canvas
     */
    function addOutputNode() {
        // Get the center of the visible canvas
        const canvasRect = canvas.getBoundingClientRect();
        const x = ((canvasRect.width * 2/3) - canvasOffset.x) / canvasScale;
        const y = ((canvasRect.height / 2) - canvasOffset.y) / canvasScale;
        
        const nodeId = 'node-' + (++nodeCounter);
        const nodeElement = document.createElement('div');
        nodeElement.id = nodeId;
        nodeElement.classList.add('node', 'output');
        
        nodeElement.innerHTML = `
            <div class="node-header">
                <div class="node-title">
                    <i class="bi bi-box-arrow-right"></i>
                    <span>Output</span>
                </div>
                <div class="node-actions">
                    <button class="node-btn configure-node" title="Configure"><i class="bi bi-gear"></i></button>
                </div>
            </div>
            <div class="node-content">
                <div>Network output</div>
            </div>
            <div class="node-ports">
                <div class="input-port">
                    <div class="port port-left" data-port-type="input"></div>
                    <span class="port-label">Input</span>
                </div>
            </div>
        `;
        
        // Position the node
        nodeElement.style.left = `${x}px`;
        nodeElement.style.top = `${y}px`;
        
        // Add the node to the canvas
        canvas.appendChild(nodeElement);
        
        // Store node data
        const nodeData = {
            id: nodeId,
            element: nodeElement,
            type: 'output',
            position: { x, y },
            config: {
                name: 'Output'
            }
        };
        
        nodes.push(nodeData);
        
        // Add event listeners to the node
        initNodeEvents(nodeElement, nodeData);
        
        // Remove the help text if it's the first node
        if (nodes.length === 1) {
            emptyCanvasHelp.style.display = 'none';
        }
        
        return nodeData;
    }
    
    /**
     * Deselect all nodes and connections
     */
    function deselectAllNodes() {
        nodes.forEach(nodeData => {
            nodeData.element.classList.remove('selected');
        });
        
        connections.forEach(conn => {
            conn.element.classList.remove('selected');
        });
        
        selectedNode = null;
    }
    
    /**
     * Delete selected nodes or connections
     */
    function deleteSelected() {
        if (selectedNode) {
            // Find all connections to this node
            const relatedConnections = connections.filter(conn => 
                conn.start.nodeId === selectedNode.id || conn.end.nodeId === selectedNode.id
            );
            
            // Remove connections
            relatedConnections.forEach(conn => {
                svgContainer.removeChild(conn.element);
                connections = connections.filter(c => c.id !== conn.id);
            });
            
            // Remove node
            nodeContainer.removeChild(selectedNode.element);
            nodes = nodes.filter(n => n.id !== selectedNode.id);
            selectedNode = null;
            
            // Show help text if no nodes left
            if (nodes.length === 0) {
                emptyCanvasHelp.style.display = 'flex';
            }
        } else {
            // Check for selected connection
            const selectedConn = connections.find(conn => conn.element.classList.contains('selected'));
            if (selectedConn) {
                svgContainer.removeChild(selectedConn.element);
                connections = connections.filter(c => c.id !== selectedConn.id);
            }
        }
    }
    
    /**
     * Zoom in on the canvas
     */
    function zoomIn() {
        const newScale = Math.min(canvasScale + 0.1, 2);
        if (newScale !== canvasScale) {
            // Get canvas center
            const rect = canvas.getBoundingClientRect();
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            // Calculate the point in world space
            const worldX = (centerX - canvasOffset.x) / canvasScale;
            const worldY = (centerY - canvasOffset.y) / canvasScale;
            
            // Update the scale
            canvasScale = newScale;
            
            // Calculate the new offset to keep the center point
            canvasOffset.x = centerX - worldX * canvasScale;
            canvasOffset.y = centerY - worldY * canvasScale;
            
            updateCanvasTransform();
        }
    }
    
    /**
     * Zoom out on the canvas
     */
    function zoomOut() {
        const newScale = Math.max(canvasScale - 0.1, 0.3);
        if (newScale !== canvasScale) {
            // Get canvas center
            const rect = canvas.getBoundingClientRect();
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            // Calculate the point in world space
            const worldX = (centerX - canvasOffset.x) / canvasScale;
            const worldY = (centerY - canvasOffset.y) / canvasScale;
            
            // Update the scale
            canvasScale = newScale;
            
            // Calculate the new offset to keep the center point
            canvasOffset.x = centerX - worldX * canvasScale;
            canvasOffset.y = centerY - worldY * canvasScale;
            
            updateCanvasTransform();
        }
    }
    
    /**
     * Reset zoom and pan on the canvas
     */
    function resetZoom() {
        canvasScale = 1;
        canvasOffset = { x: 0, y: 0 };
        updateCanvasTransform();
    }
    
    /**
     * Save the current network to the server
     */
    function saveNetwork() {
        const networkData = {
            name: document.getElementById('network-name').textContent,
            nodes: nodes.map(node => ({
                id: node.id,
                type: node.type,
                subType: node.subType,
                position: node.position,
                config: node.config
            })),
            connections: connections.map(conn => ({
                sourceNode: conn.start.nodeId,
                sourcePort: conn.start.port,
                targetNode: conn.end.nodeId,
                targetPort: conn.end.port
            }))
        };
        
        // TODO: Implement server-side saving
        console.log('Network data to save:', networkData);
        alert('Save functionality will be implemented in the next phase.');
    }
    
    /**
     * Run the current network on the server
     */
    function runNetwork() {
        // First, validate that the network is valid
        const validationResult = validateNetwork();
        if (!validationResult.valid) {
            // Show validation errors
            validationResult.errors.forEach(error => {
                showNotification(error, 'error');
            });
            return;
        }
        
        // Prepare network data to send to the server
        const networkData = {
            name: document.getElementById('network-name').textContent,
            nodes: nodes.map(node => ({
                id: node.id,
                type: node.type,
                subType: node.subType,
                position: node.position,
                config: node.config
            })),
            connections: connections.map(conn => ({
                sourceNode: conn.start.nodeId,
                sourcePort: conn.start.port,
                targetNode: conn.end.nodeId,
                targetPort: conn.end.port
            }))
        };
        
        // Show execution dialog for user input
        showExecutionDialog(networkData);
    }
    
    /**
     * Show the execution dialog for the user to provide input
     * @param {Object} networkData - The prepared network data
     */
    function showExecutionDialog(networkData) {
        // Check if there's already an execution dialog
        let executionDialog = document.getElementById('execution-dialog');
        
        // Create the dialog if it doesn't exist
        if (!executionDialog) {
            executionDialog = document.createElement('div');
            executionDialog.id = 'execution-dialog';
            executionDialog.className = 'modal';
            
            executionDialog.innerHTML = `
                <div class="modal-content execution-dialog-content">
                    <div class="modal-header">
                        <h2>Run Agent Network</h2>
                        <button class="close-btn modal-close"><i class="bi bi-x-lg"></i></button>
                    </div>
                    <div class="modal-body">
                        <div class="execution-tabs">
                            <button class="tab-btn active" data-tab="input">Input</button>
                            <button class="tab-btn" data-tab="execution">Execution</button>
                            <button class="tab-btn" data-tab="output">Output</button>
                        </div>
                        
                        <div class="tab-content" id="input-tab">
                            <div class="form-group">
                                <label for="user-input">Your request:</label>
                                <textarea id="user-input" class="form-control" rows="5" placeholder="Enter your request here..."></textarea>
                            </div>
                        </div>
                        
                        <div class="tab-content hidden" id="execution-tab">
                            <div class="execution-status">
                                <div class="status-header">
                                    <h3>Execution Status</h3>
                                    <span class="status-badge pending">Pending</span>
                                </div>
                                <div class="execution-log">
                                    <div class="log-container" id="execution-log-container">
                                        <div class="log-entry">Agent network ready to run...</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="tab-content hidden" id="output-tab">
                            <div class="form-group">
                                <label for="network-output">Result:</label>
                                <div class="output-container" id="network-output-container">
                                    <div class="placeholder-text">Run the network to see results...</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <div class="execution-progress">
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: 0%"></div>
                            </div>
                        </div>
                        <button class="secondary-btn modal-close">Close</button>
                        <button id="run-network-btn" class="primary-btn">Run</button>
                    </div>
                </div>
            `;
            
            document.body.appendChild(executionDialog);
            
            // Initialize tab switching
            const tabButtons = executionDialog.querySelectorAll('.tab-btn');
            const tabContents = executionDialog.querySelectorAll('.tab-content');
            
            tabButtons.forEach(button => {
                button.addEventListener('click', () => {
                    // Remove active class from all buttons
                    tabButtons.forEach(btn => btn.classList.remove('active'));
                    
                    // Hide all tab contents
                    tabContents.forEach(content => content.classList.add('hidden'));
                    
                    // Add active class to the clicked button
                    button.classList.add('active');
                    
                    // Show the corresponding tab content
                    const tabName = button.getAttribute('data-tab');
                    const tabContent = document.getElementById(`${tabName}-tab`);
                    tabContent.classList.remove('hidden');
                });
            });
            
            // Handle run button click
            const runButton = executionDialog.querySelector('#run-network-btn');
            runButton.addEventListener('click', () => {
                executeNetworkWithInput(networkData);
            });
            
            // Handle modal close
            const closeButtons = executionDialog.querySelectorAll('.modal-close');
            closeButtons.forEach(button => {
                button.addEventListener('click', () => {
                    executionDialog.classList.remove('open');
                });
            });
        }
        
        // Show the dialog
        executionDialog.classList.add('open');
    }
    
    /**
     * Execute the network with user input
     * @param {Object} networkData - The prepared network data
     */
    function executeNetworkWithInput(networkData) {
        const userInput = document.getElementById('user-input').value;
        
        if (!userInput.trim()) {
            showNotification('Please provide input for the network', 'warning');
            return;
        }
        
        // Update UI to execution tab
        const executionDialog = document.getElementById('execution-dialog');
        const tabButtons = executionDialog.querySelectorAll('.tab-btn');
        const tabContents = executionDialog.querySelectorAll('.tab-content');
        
        // Switch to execution tab
        tabButtons.forEach(btn => btn.classList.remove('active'));
        tabButtons[1].classList.add('active'); // Execution tab
        
        tabContents.forEach(content => content.classList.add('hidden'));
        document.getElementById('execution-tab').classList.remove('hidden');
        
        // Update status badge
        const statusBadge = document.querySelector('.status-badge');
        statusBadge.className = 'status-badge running';
        statusBadge.textContent = 'Running';
        
        // Update progress bar
        const progressFill = document.querySelector('.progress-fill');
        progressFill.style.width = '15%';
        
        // Add log entry
        addLogEntry('Starting network execution...');
        addLogEntry(`Processing input: "${userInput.substring(0, 40)}${userInput.length > 40 ? '...' : ''}"`);
        
        // Disable run button during execution
        const runButton = document.getElementById('run-network-btn');
        runButton.disabled = true;
        runButton.textContent = 'Running...';
        
        // Add the user input to the network data
        const executionData = {
            ...networkData,
            input: userInput
        };
        
        // Clear any previous execution highlights
        resetNodeStyles();
        
        // Send the request to the server
        fetch('/api/workflows/run-network', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(executionData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Network execution failed: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            // Store execution ID for status polling
            const executionId = data.execution_id;
            
            if (executionId) {
                // Start polling for updates
                addLogEntry(`Execution started with ID: ${executionId}`);
                pollExecutionStatus(executionId);
            } else {
                // Update progress immediately if no execution ID
                progressFill.style.width = '100%';
                
                // Update status
                statusBadge.className = 'status-badge completed';
                statusBadge.textContent = 'Completed';
                
                // Add log entries
                addLogEntry('Network execution completed successfully');
                
                showExecutionResult(data, userInput, tabButtons, tabContents, runButton);
            }
        })
        .catch(error => {
            console.error('Execution error:', error);
            
            // Update status
            statusBadge.className = 'status-badge error';
            statusBadge.textContent = 'Error';
            
            // Add error log
            addLogEntry(`Error: ${error.message}`, 'error');
            
            // For development, we'll show a simulated response anyway
            progressFill.style.width = '100%';
            
            setTimeout(() => {
                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabButtons[2].classList.add('active'); // Output tab
                
                tabContents.forEach(content => content.classList.add('hidden'));
                document.getElementById('output-tab').classList.remove('hidden');
                
                // Update output with error message
                const outputContainer = document.getElementById('network-output-container');
                outputContainer.innerHTML = '';
                
                const outputContent = document.createElement('div');
                outputContent.className = 'output-content error';
                
                // For development, we'll simulate a response
                outputContent.textContent = simulateResponse(userInput);
                
                outputContainer.appendChild(outputContent);
                
                // Re-enable run button
                runButton.disabled = false;
                runButton.textContent = 'Run Again';
            }, 1000);
        });
    }
    
    /**
     * Reset all node styles to their default state
     */
    function resetNodeStyles() {
        // Remove any execution status classes
        document.querySelectorAll('.node').forEach(nodeEl => {
            nodeEl.classList.remove('node-executing', 'node-completed', 'node-failed', 'node-pending');
        });
    }
    
    /**
     * Poll execution status and update UI
     * @param {string} executionId - The execution ID to poll
     * @param {number} interval - Polling interval in milliseconds
     */
    function pollExecutionStatus(executionId, interval = 1000) {
        let pollCount = 0;
        const maxPolls = 60; // Maximum number of times to poll (1 minute at 1-second intervals)
        let pollTimer = null;
        
        // Get UI elements once
        const statusBadge = document.querySelector('.status-badge');
        const progressFill = document.querySelector('.progress-fill');
        const runButton = document.getElementById('run-network-btn');
        const executionDialog = document.getElementById('execution-dialog');
        const tabButtons = executionDialog.querySelectorAll('.tab-btn');
        const tabContents = executionDialog.querySelectorAll('.tab-content');
        
        // Function to check status
        function checkStatus() {
            pollCount++;
            
            // Fetch status from API
            fetch(`/api/workflows/execution-status/${executionId}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`Failed to get execution status: ${response.statusText}`);
                    }
                    return response.json();
                })
                .then(data => {
                    const status = data.status;
                    const nodeStatuses = data.node_statuses || {};
                    
                    // Update node status in UI
                    updateNodeExecutionStatus(nodeStatuses);
                    
                    // Add log entry for active nodes
                    Object.values(nodeStatuses).forEach(node => {
                        if (node.status === 'RUNNING' && !node._logged) {
                            addLogEntry(`Executing node: ${node.name || node.id}`);
                            node._logged = true; // Mark as logged to avoid duplicate entries
                        }
                        else if (node.status === 'COMPLETED' && !node._completed_logged) {
                            addLogEntry(`Completed node: ${node.name || node.id}`);
                            node._completed_logged = true;
                        }
                        else if (node.status === 'FAILED' && !node._failed_logged) {
                            addLogEntry(`Failed node: ${node.name || node.id}`, 'error');
                            addLogEntry(`Error: ${node.error || 'Unknown error'}`, 'error');
                            node._failed_logged = true;
                        }
                    });
                    
                    // Update progress based on completed nodes
                    const totalNodes = Object.keys(nodeStatuses).length;
                    if (totalNodes > 0) {
                        const completedNodes = Object.values(nodeStatuses).filter(
                            n => n.status === 'COMPLETED' || n.status === 'FAILED'
                        ).length;
                        
                        const progress = Math.max(15, Math.min(90, (completedNodes / totalNodes) * 100));
                        progressFill.style.width = `${progress}%`;
                    }
                    
                    // Check if execution is complete
                    if (status === 'COMPLETED') {
                        // Update status
                        statusBadge.className = 'status-badge completed';
                        statusBadge.textContent = 'Completed';
                        
                        // Add log entry
                        addLogEntry('Network execution completed successfully');
                        
                        // Update progress to 100%
                        progressFill.style.width = '100%';
                        
                        // Get final result
                        fetchExecutionResult(executionId, data => {
                            showExecutionResult(data, document.getElementById('user-input').value, 
                                             tabButtons, tabContents, runButton);
                        });
                        
                        // Clear polling timer
                        if (pollTimer) {
                            clearTimeout(pollTimer);
                            pollTimer = null;
                        }
                    }
                    else if (status === 'FAILED') {
                        // Update status
                        statusBadge.className = 'status-badge error';
                        statusBadge.textContent = 'Failed';
                        
                        // Add log entry
                        addLogEntry('Network execution failed', 'error');
                        
                        // Update progress to 100%
                        progressFill.style.width = '100%';
                        
                        // Get final result with error
                        fetchExecutionResult(executionId, data => {
                            showExecutionResult(data, document.getElementById('user-input').value, 
                                             tabButtons, tabContents, runButton);
                        });
                        
                        // Clear polling timer
                        if (pollTimer) {
                            clearTimeout(pollTimer);
                            pollTimer = null;
                        }
                    }
                    else if (pollCount >= maxPolls) {
                        // Timeout case
                        statusBadge.className = 'status-badge warning';
                        statusBadge.textContent = 'Timeout';
                        
                        addLogEntry('Execution polling timed out', 'warning');
                        addLogEntry('The execution may still be running in the background', 'info');
                        
                        // Re-enable run button
                        runButton.disabled = false;
                        runButton.textContent = 'Run Again';
                        
                        // Clear polling timer
                        if (pollTimer) {
                            clearTimeout(pollTimer);
                            pollTimer = null;
                        }
                    }
                    else {
                        // Continue polling
                        pollTimer = setTimeout(checkStatus, interval);
                    }
                })
                .catch(error => {
                    console.error('Polling error:', error);
                    addLogEntry(`Status polling error: ${error.message}`, 'error');
                    
                    // If this was just a temporary error, keep polling
                    if (pollCount < maxPolls) {
                        pollTimer = setTimeout(checkStatus, interval);
                    } else {
                        // Re-enable run button
                        runButton.disabled = false;
                        runButton.textContent = 'Run Again';
                    }
                });
        }
        
        // Start polling
        checkStatus();
    }
    
    /**
     * Update node styles based on execution status
     * @param {Object} nodeStatuses - Map of node statuses
     */
    function updateNodeExecutionStatus(nodeStatuses) {
        // Reset non-active nodes first
        document.querySelectorAll('.node').forEach(nodeEl => {
            const nodeId = nodeEl.id;
            
            // Find matching status by UI node ID
            const matchingStatus = Object.values(nodeStatuses).find(
                s => s.ui_node_id === nodeId
            );
            
            if (!matchingStatus) {
                // No status, clear any execution classes
                nodeEl.classList.remove('node-executing', 'node-completed', 'node-failed');
            } else {
                // Update based on status
                nodeEl.classList.remove('node-executing', 'node-completed', 'node-failed', 'node-pending');
                
                if (matchingStatus.status === 'RUNNING') {
                    nodeEl.classList.add('node-executing');
                } else if (matchingStatus.status === 'COMPLETED') {
                    nodeEl.classList.add('node-completed');
                } else if (matchingStatus.status === 'FAILED') {
                    nodeEl.classList.add('node-failed');
                } else if (matchingStatus.status === 'PENDING') {
                    nodeEl.classList.add('node-pending');
                }
            }
        });
    }
    
    /**
     * Fetch the final execution result
     * @param {string} executionId - The execution ID
     * @param {Function} callback - Callback function to receive result
     */
    function fetchExecutionResult(executionId, callback) {
        fetch(`/api/workflows/execution-status/${executionId}`)
            .then(response => response.json())
            .then(data => {
                callback(data);
            })
            .catch(error => {
                console.error('Error fetching result:', error);
                callback({
                    error: `Failed to fetch execution result: ${error.message}`
                });
            });
    }
    
    /**
     * Show execution result in the output tab
     * @param {Object} data - The execution result data
     * @param {string} userInput - The user input
     * @param {NodeList} tabButtons - The tab buttons
     * @param {NodeList} tabContents - The tab contents
     * @param {HTMLButtonElement} runButton - The run button
     */
    function showExecutionResult(data, userInput, tabButtons, tabContents, runButton) {
        // Switch to output tab
        setTimeout(() => {
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabButtons[2].classList.add('active'); // Output tab
            
            tabContents.forEach(content => content.classList.add('hidden'));
            document.getElementById('output-tab').classList.remove('hidden');
            
            // Update output
            const outputContainer = document.getElementById('network-output-container');
            outputContainer.innerHTML = '';
            
            const outputContent = document.createElement('div');
            outputContent.className = 'output-content';
            
            // Handle error case first
            if (data.error) {
                outputContent.textContent = `Error: ${data.error}`;
                outputContent.classList.add('error');
                outputContainer.appendChild(outputContent);
            }
            // Check if the response has a structured result with type information
            else if (data.result !== undefined) {
                // Check if we have a structured response with type and format
                if (data.type) {
                    const resultType = data.type;
                    const resultFormat = data.format;
                    const resultContent = data.result;
                    
                    // Format based on type
                    if (resultType === 'json' || resultFormat === 'json' || typeof resultContent === 'object') {
                        // Display as formatted JSON
                        outputContent.className = 'output-content json';
                        try {
                            const formattedJson = typeof resultContent === 'string' 
                                ? JSON.stringify(JSON.parse(resultContent), null, 2)
                                : JSON.stringify(resultContent, null, 2);
                            
                            // Use a pre element for code formatting
                            const pre = document.createElement('pre');
                            pre.textContent = formattedJson;
                            outputContent.appendChild(pre);
                        } catch (e) {
                            // Fall back to string representation if JSON parsing fails
                            outputContent.textContent = typeof resultContent === 'string' 
                                ? resultContent
                                : JSON.stringify(resultContent);
                        }
                    }
                    else if (resultType === 'markdown' || resultFormat === 'markdown') {
                        // For markdown, we'd ideally use a markdown renderer
                        // For now, we'll use a simple pre element with a markdown class
                        outputContent.className = 'output-content markdown';
                        
                        // Use a pre element to preserve formatting
                        const pre = document.createElement('pre');
                        pre.textContent = resultContent;
                        outputContent.appendChild(pre);
                    }
                    else if (resultType === 'html' || resultFormat === 'html') {
                        // For HTML content, use innerHTML
                        outputContent.className = 'output-content html';
                        outputContent.innerHTML = resultContent;
                    }
                    else {
                        // Default to text
                        outputContent.className = 'output-content text';
                        
                        // Check if result is a string or object
                        if (typeof resultContent === 'string') {
                            // Replace newlines with <br> elements for better display
                            const lines = resultContent.split('\n');
                            for (let i = 0; i < lines.length; i++) {
                                const line = document.createTextNode(lines[i]);
                                outputContent.appendChild(line);
                                if (i < lines.length - 1) {
                                    outputContent.appendChild(document.createElement('br'));
                                }
                            }
                        } else {
                            // For objects, display as formatted JSON
                            const pre = document.createElement('pre');
                            try {
                                pre.textContent = JSON.stringify(resultContent, null, 2);
                            } catch (e) {
                                pre.textContent = String(resultContent);
                            }
                            outputContent.appendChild(pre);
                        }
                    }
                } else {
                    // No type information, just show the result directly
                    const resultContent = data.result;
                    
                    // Detect if the result is an object
                    if (typeof resultContent === 'object' && resultContent !== null) {
                        // Display as formatted JSON
                        outputContent.className = 'output-content json';
                        const pre = document.createElement('pre');
                        pre.textContent = JSON.stringify(resultContent, null, 2);
                        outputContent.appendChild(pre);
                    } else {
                        // Handle string with newlines properly
                        outputContent.className = 'output-content text';
                        
                        // Replace newlines with <br> elements for better display
                        const lines = String(resultContent).split('\n');
                        for (let i = 0; i < lines.length; i++) {
                            const line = document.createTextNode(lines[i]);
                            outputContent.appendChild(line);
                            if (i < lines.length - 1) {
                                outputContent.appendChild(document.createElement('br'));
                            }
                        }
                    }
                }
                
                outputContainer.appendChild(outputContent);
            } 
            // Fallback - use simulated response for development
            else {
                outputContent.textContent = simulateResponse(userInput);
                outputContainer.appendChild(outputContent);
            }
            
            // Re-enable run button
            runButton.disabled = false;
            runButton.textContent = 'Run Again';
        }, 1000);
    }
    
    /**
     * Add a log entry to the execution log
     * @param {string} message - The log message
     * @param {string} type - The type of log entry (info, warning, error)
     */
    function addLogEntry(message, type = 'info') {
        const logContainer = document.getElementById('execution-log-container');
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${type}`;
        
        const timestamp = new Date().toLocaleTimeString();
        logEntry.innerHTML = `<span class="log-time">[${timestamp}]</span> ${message}`;
        
        logContainer.appendChild(logEntry);
        logContainer.scrollTop = logContainer.scrollHeight;
        
        // Update progress bar
        const progressFill = document.querySelector('.progress-fill');
        const currentWidth = parseInt(progressFill.style.width) || 15;
        const newWidth = Math.min(currentWidth + Math.random() * 20, 90);
        progressFill.style.width = `${newWidth}%`;
    }
    
    /**
     * Show a notification message
     * @param {string} message - The notification message
     * @param {string} type - The type of notification (info, success, warning, error)
     */
    function showNotification(message, type = 'info') {
        // Check if notification container exists
        let notificationContainer = document.getElementById('notification-container');
        
        if (!notificationContainer) {
            notificationContainer = document.createElement('div');
            notificationContainer.id = 'notification-container';
            document.body.appendChild(notificationContainer);
        }
        
        // Create notification
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        const iconMap = {
            info: 'info-circle',
            success: 'check-circle',
            warning: 'exclamation-triangle',
            error: 'x-circle'
        };
        
        notification.innerHTML = `
            <div class="notification-icon">
                <i class="bi bi-${iconMap[type]}"></i>
            </div>
            <div class="notification-content">
                <p>${message}</p>
            </div>
            <button class="notification-close">
                <i class="bi bi-x"></i>
            </button>
        `;
        
        // Add to container
        notificationContainer.appendChild(notification);
        
        // Add close button functionality
        const closeButton = notification.querySelector('.notification-close');
        closeButton.addEventListener('click', () => {
            notification.classList.add('closing');
            setTimeout(() => {
                notificationContainer.removeChild(notification);
            }, 300);
        });
        
        // Auto-dismiss after a delay
        setTimeout(() => {
            if (notification.parentNode === notificationContainer) {
                notification.classList.add('closing');
                setTimeout(() => {
                    if (notification.parentNode === notificationContainer) {
                        notificationContainer.removeChild(notification);
                    }
                }, 300);
            }
        }, 5000);
    }
    
    /**
     * Validate the network before running
     * @returns {Object} - Validation result with valid flag and errors array
     */
    function validateNetwork() {
        const errors = [];
        
        // Check for input and output nodes
        const inputNodes = nodes.filter(node => node.type === 'input');
        const outputNodes = nodes.filter(node => node.type === 'output');
        
        if (inputNodes.length === 0) {
            errors.push('Please add an input node to your network');
        }
        
        if (outputNodes.length === 0) {
            errors.push('Please add an output node to your network');
        }
        
        // Check for connections between nodes
        if (connections.length === 0) {
            errors.push('Please connect nodes in your network');
        }
        
        // Validate agent configurations
        for (const node of nodes) {
            if (node.type === 'agent') {
                const agentType = node.subType;
                const config = node.config || {};
                
                // Check that the node has a name
                if (!config.name || config.name.trim() === '') {
                    errors.push(`Agent node #${node.id.split('-')[1]} needs a name`);
                }
                
                // Validate based on agent type
                if (agentType === 'openai') {
                    if (!config.apiKey || config.apiKey.trim() === '') {
                        errors.push(`OpenAI agent ${config.name || 'Unnamed'} is missing API key`);
                    }
                    if (!config.model) {
                        errors.push(`OpenAI agent ${config.name || 'Unnamed'} is missing model selection`);
                    }
                }
                else if (agentType === 'anthropic') {
                    if (!config.apiKey || config.apiKey.trim() === '') {
                        errors.push(`Claude agent ${config.name || 'Unnamed'} is missing API key`);
                    }
                    if (!config.model) {
                        errors.push(`Claude agent ${config.name || 'Unnamed'} is missing model selection`);
                    }
                }
                else if (agentType === 'bedrock') {
                    if (!config.accessKey || config.accessKey.trim() === '' || 
                        !config.secretKey || config.secretKey.trim() === '') {
                        errors.push(`Bedrock agent ${config.name || 'Unnamed'} is missing AWS credentials`);
                    }
                    if (!config.region) {
                        errors.push(`Bedrock agent ${config.name || 'Unnamed'} is missing AWS region`);
                    }
                    if (!config.model) {
                        errors.push(`Bedrock agent ${config.name || 'Unnamed'} is missing model selection`);
                    }
                }
                else if (agentType === 'custom') {
                    if ((!config.port || config.port === '') && 
                        (!config.endpoint || config.endpoint.trim() === '')) {
                        errors.push(`Custom agent ${config.name || 'Unnamed'} needs either a port or endpoint URL`);
                    }
                }
            }
        }
        
        // Check for isolated nodes (no connections)
        const connectedNodeIds = new Set();
        connections.forEach(conn => {
            connectedNodeIds.add(conn.start.nodeId);
            connectedNodeIds.add(conn.end.nodeId);
        });
        
        for (const node of nodes) {
            if (!connectedNodeIds.has(node.id)) {
                errors.push(`Node ${node.config?.name || node.type} is not connected to any other node`);
            }
        }
        
        // Check if the network forms a complete path from input to output
        // This is a simplified check - a full check would need graph traversal
        const inputNodeIds = inputNodes.map(node => node.id);
        const outputNodeIds = outputNodes.map(node => node.id);
        
        // Check if at least one input node is connected
        let inputConnected = false;
        for (const inputId of inputNodeIds) {
            if (connectedNodeIds.has(inputId)) {
                inputConnected = true;
                break;
            }
        }
        
        if (!inputConnected && inputNodeIds.length > 0) {
            errors.push('Input node is not connected to the network');
        }
        
        // Check if at least one output node is connected
        let outputConnected = false;
        for (const outputId of outputNodeIds) {
            if (connectedNodeIds.has(outputId)) {
                outputConnected = true;
                break;
            }
        }
        
        if (!outputConnected && outputNodeIds.length > 0) {
            errors.push('Output node is not connected to the network');
        }
        
        return {
            valid: errors.length === 0,
            errors: errors
        };
    }
    
    /**
     * Simulate a response for development purposes
     * @param {string} input - The user input
     * @returns {string} - The simulated response
     */
    function simulateResponse(input) {
        const responses = [
            `I've processed your request: "${input.substring(0, 30)}${input.length > 30 ? '...' : ''}"\n\nBased on my analysis, I can provide the following information:\n\n1. The request appears to be about ${input.split(' ').slice(0, 3).join(' ')}...\n2. I've identified key concepts that relate to your question\n3. My recommendation is to focus on the primary aspects mentioned in your request`,
            
            `Thank you for your query about "${input.substring(0, 20)}${input.length > 20 ? '...' : ''}"\n\nHere's what I found:\n• The main topic involves ${input.split(' ').slice(-3).join(' ')}\n• There are several factors to consider\n• Based on available information, the most effective approach would be to analyze further`,
            
            `I've analyzed your request regarding "${input.substring(0, 25)}${input.length > 25 ? '...' : ''}"\n\nMy findings:\n1. This appears to be related to ${input.split(' ')[0]} technology\n2. Current trends suggest a growing interest in this area\n3. For best results, consider exploring advanced techniques\n\nWould you like me to elaborate on any specific aspect?`
        ];
        
        // Get a "random" response based on the input length
        const index = input.length % responses.length;
        return responses[index];
    }
    
    /**
     * Undo the last action
     */
    function undoAction() {
        // TODO: Implement undo functionality
        alert('Undo functionality will be implemented in the next phase.');
    }
    
    /**
     * Redo the last undone action
     */
    function redoAction() {
        // TODO: Implement redo functionality
        alert('Redo functionality will be implemented in the next phase.');
    }
    
    // Handle window mousemove and mouseup events for connection creation only
    window.addEventListener('mousemove', (e) => {
        // Node dragging is now handled in the node-specific event handler
        
        // Handle connection creation
        if (connectionStart) {
            const canvasRect = canvas.getBoundingClientRect();
            const mouseX = (e.clientX - canvasRect.left - canvasOffset.x) / canvasScale;
            const mouseY = (e.clientY - canvasRect.top - canvasOffset.y) / canvasScale;
            
            updateTempConnection(mouseX, mouseY);
            
            // Update tooltip position
            connectionTooltip.style.left = `${e.clientX}px`;
            connectionTooltip.style.top = `${e.clientY - 30}px`;
        }
    });
    
    window.addEventListener('mouseup', () => {
        // End node dragging
        if (isDragging) {
            isDragging = false;
        }
        
        // End connection creation if not completed
        if (connectionStart && !connectionEnd) {
            const tempConnection = document.getElementById('temp-connection');
            if (tempConnection) {
                svgContainer.removeChild(tempConnection);
            }
            
            connectionStart = null;
            connectionTooltip.style.opacity = '0';
        }
    });
});