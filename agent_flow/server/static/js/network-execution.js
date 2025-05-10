/**
 * Enhanced Network Execution Dialog Module
 * This module provides a redesigned UI for multi-network execution
 * with improved tab navigation and layout with support for both
 * sequential and parallel execution modes.
 *
 * Features:
 * - Automatic network detection and selection
 * - Conditional execution mode options (sequential/parallel)
 * - Real-time execution logging
 * - Improved results visualization with accordions
 * - Special handling for different execution modes
 * - Error reporting and visualization
 */

// Debugging helper
const DEBUG = false;
function debugLog(...args) {
    if (DEBUG) console.log('[NetworkExecution]', ...args);
}

/**
 * Shows the network execution dialog with improved UI
 * @param {Object} networkData - Current network data
 * @param {Array} detectedNetworks - Array of detected networks
 */
function showNetworkExecutionDialog(networkData, detectedNetworks) {
    // Close any existing dialog
    const existingDialog = document.getElementById('execution-dialog');
    if (existingDialog) {
        document.body.removeChild(existingDialog);
    }
    
    // Determine if we have multiple networks
    const hasMultipleNetworks = detectedNetworks && detectedNetworks.length > 0;
    
    // Create a new execution dialog
    const executionDialog = document.createElement('div');
    executionDialog.id = 'execution-dialog';
    executionDialog.className = 'modal';
    
    // Prepare network items
    const allNetworks = [];
    
    // Add detected networks (if we have actual separate networks, don't include current network)
    if (hasMultipleNetworks) {
        detectedNetworks.forEach((network, index) => {
            allNetworks.push({
                id: `network-${index}`,
                name: `Network ${index + 1}`,
                nodeCount: network.nodeCount || network.nodes.length,
                connectionCount: network.connectionCount || network.connections.length,
                selected: true
            });
        });
    } else {
        // Only add current network if there are no separate detected networks
        allNetworks.push({
            id: 'current',
            name: 'Current Network',
            nodeCount: networkData.nodes.length,
            connectionCount: networkData.connections.length,
            selected: true
        });
    }
    
    // Build the dialog HTML with tabs
    const dialogHTML = `
        <div class="modal-content execution-dialog-content">
            <div class="modal-header">
                <h2>Run Agent Network</h2>
                <button class="close-btn modal-close"><i class="bi bi-x-lg"></i></button>
            </div>
            
            <div class="execution-tabs">
                <button class="tab-btn active" data-tab="networks">Networks</button>
                <button class="tab-btn" data-tab="execution">Execution</button>
                <button class="tab-btn" data-tab="output">Output</button>
            </div>
            
            <div class="modal-body">
                <!-- Networks Tab -->
                <div class="tab-content active" id="networks-tab">
                    <div class="network-selection-panel">
                        <div class="section-header">
                            <h3>Network Selection</h3>
                            <div class="networks-count">${allNetworks.length} networks detected</div>
                        </div>
                        
                        <div class="network-list">
                            ${allNetworks.map((network, index) => `
                                <div class="network-item ${network.selected ? 'selected' : ''}" data-network-id="${network.id}">
                                    <div class="network-icon">
                                        <i class="bi bi-diagram-3"></i>
                                    </div>
                                    <div class="network-info">
                                        <div class="network-name">${network.name}</div>
                                        <div class="network-stats">
                                            <span class="stat">${network.nodeCount} nodes</span>
                                            <span class="stat">${network.connectionCount} connections</span>
                                        </div>
                                    </div>
                                    <div class="network-select">
                                        <input type="checkbox" class="network-checkbox" id="network-cb-${network.id}" ${network.selected ? 'checked' : ''}>
                                        <label for="network-cb-${network.id}">Select</label>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                        
                        <div class="input-section">
                            <label for="user-input">Input Message:</label>
                            <textarea id="user-input" class="form-control" rows="4" placeholder="Enter your request here..."></textarea>
                        </div>
                        
                        ${allNetworks.length > 1 ? `
                            <div class="execution-mode-section">
                                <div class="mode-header">
                                    <h3>Execution Mode</h3>
                                </div>
                                <div class="mode-options">
                                    <label class="mode-option selected">
                                        <input type="radio" name="execution-mode" value="sequential" checked>
                                        <div class="mode-icon"><i class="bi bi-arrow-down"></i></div>
                                        <div class="mode-content">
                                            <div class="mode-title">Sequential</div>
                                            <div class="mode-description">Networks execute one after another. Output of each network is used as input for the next.</div>
                                        </div>
                                    </label>
                                    
                                    <label class="mode-option">
                                        <input type="radio" name="execution-mode" value="parallel">
                                        <div class="mode-icon"><i class="bi bi-arrows"></i></div>
                                        <div class="mode-content">
                                            <div class="mode-title">Parallel</div>
                                            <div class="mode-description">All networks execute simultaneously with the same input. Results are returned separately.</div>
                                        </div>
                                    </label>
                                </div>
                            </div>
                        ` : ''}
                    </div>
                </div>
                
                <!-- Execution Tab -->
                <div class="tab-content" id="execution-tab">
                    <div class="execution-status-panel">
                        <div class="section-header">
                            <h3>Execution Status</h3>
                            <div class="status-badge pending">Pending</div>
                        </div>
                        
                        <div class="log-container" id="execution-log-container">
                            <div class="log-entry">Agent network ready to run...</div>
                        </div>
                    </div>
                </div>
                
                <!-- Output Tab -->
                <div class="tab-content" id="output-tab">
                    <div class="output-panel">
                        <div class="section-header">
                            <h3>Execution Results</h3>
                        </div>
                        
                        <div class="result-container" id="result-container">
                            <div class="result-placeholder">Run the network to see results...</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="modal-footer">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: 0%"></div>
                </div>
                <div class="action-buttons">
                    <button class="secondary-btn modal-close">Close</button>
                    <button id="run-network-btn" class="primary-btn">Run Networks</button>
                </div>
            </div>
        </div>
    `;
    
    executionDialog.innerHTML = dialogHTML;
    document.body.appendChild(executionDialog);
    
    // Set up event listeners
    setupEventListeners(executionDialog, networkData, detectedNetworks);
    
    // Show the dialog
    executionDialog.classList.add('open');
    
    return executionDialog;
}

/**
 * Set up all event listeners for the dialog
 * @param {HTMLElement} dialog - The dialog element
 * @param {Object} networkData - Current network data
 * @param {Array} detectedNetworks - Array of detected networks
 */
function setupEventListeners(dialog, networkData, detectedNetworks) {
    // Tab switching
    const tabButtons = dialog.querySelectorAll('.tab-btn');
    const tabContents = dialog.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Update active tab button
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Show corresponding tab content
            const tabId = button.getAttribute('data-tab');
            tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === `${tabId}-tab`) {
                    content.classList.add('active');
                }
            });
        });
    });
    
    // Network selection
    const networkItems = dialog.querySelectorAll('.network-item');
    const networkCheckboxes = dialog.querySelectorAll('.network-checkbox');
    
    // Make whole network item clickable
    networkItems.forEach(item => {
        item.addEventListener('click', (e) => {
            // Ignore if clicking on checkbox directly
            if (e.target.type === 'checkbox' || e.target.tagName === 'LABEL') {
                return;
            }
            
            // Find and toggle checkbox
            const checkbox = item.querySelector('.network-checkbox');
            if (checkbox) {
                checkbox.checked = !checkbox.checked;
                
                // Trigger change event
                const event = new Event('change');
                checkbox.dispatchEvent(event);
            }
        });
    });
    
    // Handle checkbox changes
    networkCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            const networkItem = checkbox.closest('.network-item');
            
            if (checkbox.checked) {
                networkItem.classList.add('selected');
            } else {
                networkItem.classList.remove('selected');
            }
            
            // Update execution mode visibility and run button text
            updateUIState(dialog);
        });
    });
    
    // Execution mode radio buttons
    const modeOptions = dialog.querySelectorAll('.mode-option');
    
    modeOptions.forEach(option => {
        // Handle clicks on the entire label
        option.addEventListener('click', () => {
            // Update visual selection
            modeOptions.forEach(opt => opt.classList.remove('selected'));
            option.classList.add('selected');
            
            // Check the radio button
            const radio = option.querySelector('input[type="radio"]');
            if (radio) {
                radio.checked = true;
            }
        });
        
        // Handle radio button changes
        const radio = option.querySelector('input[type="radio"]');
        if (radio) {
            radio.addEventListener('change', () => {
                if (radio.checked) {
                    modeOptions.forEach(opt => opt.classList.remove('selected'));
                    option.classList.add('selected');
                }
            });
        }
    });
    
    // Run button
    const runButton = dialog.querySelector('#run-network-btn');
    if (runButton) {
        runButton.addEventListener('click', () => {
            // Validate input
            const userInput = dialog.querySelector('#user-input').value.trim();
            if (!userInput) {
                showNotification('Please enter an input message', 'warning');
                return;
            }
            
            // Get selected networks
            const selectedNetworks = getSelectedNetworks(dialog, networkData, detectedNetworks);
            if (selectedNetworks.length === 0) {
                showNotification('Please select at least one network', 'warning');
                return;
            }
            
            // Switch to execution tab
            const executionTab = dialog.querySelector('.tab-btn[data-tab="execution"]');
            if (executionTab) {
                executionTab.click();
            }
            
            // Execute the selected networks
            executeSelectedNetworks(dialog, selectedNetworks, userInput);
        });
    }
    
    // Close buttons
    const closeButtons = dialog.querySelectorAll('.modal-close');
    closeButtons.forEach(button => {
        button.addEventListener('click', () => {
            dialog.classList.remove('open');
            setTimeout(() => {
                if (dialog.parentNode) {
                    dialog.parentNode.removeChild(dialog);
                }
            }, 300);
        });
    });
    
    // Initial UI state update
    updateUIState(dialog);
}

/**
 * Update UI state based on selections
 * @param {HTMLElement} dialog - The dialog element
 */
function updateUIState(dialog) {
    const selectedNetworks = dialog.querySelectorAll('.network-item.selected');
    const executionModeSection = dialog.querySelector('.execution-mode-section');
    const runButton = dialog.querySelector('#run-network-btn');
    
    // Update run button text
    if (runButton) {
        if (selectedNetworks.length === 0) {
            runButton.textContent = 'Select Networks';
            runButton.disabled = true;
        } else if (selectedNetworks.length === 1) {
            runButton.textContent = 'Run Network';
            runButton.disabled = false;
        } else {
            runButton.textContent = `Run ${selectedNetworks.length} Networks`;
            runButton.disabled = false;
        }
    }
    
    // Show/hide execution mode section
    if (executionModeSection) {
        executionModeSection.style.display = selectedNetworks.length > 1 ? 'block' : 'none';
    }
}

/**
 * Get selected networks for execution
 * @param {HTMLElement} dialog - The dialog element
 * @param {Object} currentNetworkData - Current network data
 * @param {Array} detectedNetworks - Array of detected networks
 * @returns {Array} Selected networks
 */
function getSelectedNetworks(dialog, currentNetworkData, detectedNetworks) {
    const selectedNetworks = [];
    const selectedItems = dialog.querySelectorAll('.network-item.selected');
    
    selectedItems.forEach(item => {
        const networkId = item.getAttribute('data-network-id');
        
        if (networkId === 'current') {
            // Current network
            selectedNetworks.push({
                id: 'current',
                name: 'Current Network',
                data: currentNetworkData
            });
        } else if (networkId && networkId.startsWith('network-')) {
            // Detected network
            const index = parseInt(networkId.split('-')[1], 10);
            if (detectedNetworks && detectedNetworks[index]) {
                selectedNetworks.push({
                    id: networkId,
                    name: `Network ${index + 1}`,
                    data: detectedNetworks[index]
                });
            }
        }
    });
    
    return selectedNetworks;
}

/**
 * Execute selected networks
 * @param {HTMLElement} dialog - The dialog element
 * @param {Array} selectedNetworks - Array of selected networks
 * @param {string} userInput - User input text
 */
function executeSelectedNetworks(dialog, selectedNetworks, userInput) {
    // Get execution mode
    const executionMode = dialog.querySelector('input[name="execution-mode"]:checked')?.value || 'sequential';
    
    // Update UI
    const statusBadge = dialog.querySelector('.status-badge');
    if (statusBadge) {
        statusBadge.className = 'status-badge running';
        statusBadge.textContent = 'Running';
    }
    
    const progressFill = dialog.querySelector('.progress-fill');
    if (progressFill) {
        progressFill.style.width = '10%';
    }
    
    const runButton = dialog.querySelector('#run-network-btn');
    if (runButton) {
        runButton.disabled = true;
        runButton.textContent = 'Running...';
    }
    
    // Add initial log entries
    addLogEntry(dialog, `Starting execution of ${selectedNetworks.length} network${selectedNetworks.length > 1 ? 's' : ''}...`);
    addLogEntry(dialog, `Input: "${userInput.length > 40 ? userInput.substring(0, 40) + '...' : userInput}"`);
    if (selectedNetworks.length > 1) {
        addLogEntry(dialog, `Execution mode: ${executionMode}`);
    }
    
    // Prepare execution data
    let executionData;
    
    if (selectedNetworks.length === 1) {
        // Single network execution
        executionData = {
            ...selectedNetworks[0].data,
            input: userInput
        };
    } else {
        // Multi-network execution
        executionData = {
            networks: selectedNetworks.map(n => ({ id: n.id, data: n.data })),
            execution_mode: executionMode,
            input: userInput
        };
    }
    
    // Log execution data for debugging
    debugLog('Executing with data:', executionData);
    addLogEntry(dialog, 'Sending execution request to server...', 'info');

    // Send the execution request
    fetch('/api/workflows/run-network', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(executionData)
    })
    .then(response => {
        if (!response.ok) {
            debugLog('Server returned error status:', response.status, response.statusText);
            throw new Error(`Network execution failed: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        debugLog('Execution completed with result:', data);

        // Handle successful execution
        if (progressFill) {
            progressFill.style.width = '100%';
        }
        
        if (statusBadge) {
            statusBadge.className = 'status-badge completed';
            statusBadge.textContent = 'Completed';
        }
        
        // Add success log entry
        if (data.type === 'multi_network_output') {
            const executionTime = data.execution_time ? data.execution_time.toFixed(2) : '?';
            addLogEntry(dialog, `Execution completed in ${executionTime} seconds`, 'success');
        } else {
            addLogEntry(dialog, 'Execution completed successfully', 'success');
        }
        
        // Show results
        showExecutionResults(dialog, data);
        
        // Switch to output tab
        const outputTab = dialog.querySelector('.tab-btn[data-tab="output"]');
        if (outputTab) {
            outputTab.click();
        }
        
        // Re-enable run button
        if (runButton) {
            runButton.disabled = false;
            runButton.textContent = 'Run Again';
        }
    })
    .catch(error => {
        // Handle error
        console.error('Execution error:', error);
        debugLog('Execution failed with error:', error);

        if (progressFill) {
            progressFill.style.width = '100%';
        }
        
        if (statusBadge) {
            statusBadge.className = 'status-badge error';
            statusBadge.textContent = 'Error';
        }
        
        addLogEntry(dialog, `Error: ${error.message}`, 'error');
        
        // Re-enable run button
        if (runButton) {
            runButton.disabled = false;
            runButton.textContent = 'Try Again';
        }
    });
}

/**
 * Add a log entry to the execution log
 * @param {HTMLElement} dialog - The dialog element
 * @param {string} message - Log message
 * @param {string} type - Log type (info, success, warning, error)
 */
function addLogEntry(dialog, message, type = 'info') {
    const logContainer = dialog.querySelector('#execution-log-container');
    if (!logContainer) return;
    
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry ${type}`;
    
    const timestamp = new Date().toLocaleTimeString();
    logEntry.innerHTML = `<span class="log-time">[${timestamp}]</span> ${message}`;
    
    logContainer.appendChild(logEntry);
    logContainer.scrollTop = logContainer.scrollHeight;
    
    // Update progress bar (simulate progress)
    const progressFill = dialog.querySelector('.progress-fill');
    if (progressFill) {
        const currentWidth = parseInt(progressFill.style.width) || 10;
        const newWidth = Math.min(currentWidth + Math.random() * 15, 90);
        progressFill.style.width = `${newWidth}%`;
    }
}

/**
 * Show execution results
 * @param {HTMLElement} dialog - The dialog element
 * @param {Object} data - Result data
 */
function showExecutionResults(dialog, data) {
    const resultContainer = dialog.querySelector('#result-container');
    if (!resultContainer) return;

    resultContainer.innerHTML = '';

    // Handle multi-network output
    if (data.type === 'multi_network_output' && data.results && Array.isArray(data.results)) {
        const resultsWrapper = document.createElement('div');
        resultsWrapper.className = 'multi-network-results';

        // Add summary
        const summaryDiv = document.createElement('div');
        summaryDiv.className = 'result-summary';
        summaryDiv.innerHTML = `
            <div class="summary-title">
                <i class="bi bi-${data.mode === 'sequential' ? 'arrow-down-circle' : 'arrows'}-fill"></i>
                ${data.mode === 'sequential' ? 'Sequential' : 'Parallel'} Execution Results
            </div>
            <div class="summary-details">
                <div class="summary-stat"><span>Networks:</span> ${data.networks_count || 0}</div>
                <div class="summary-stat"><span>Time:</span> ${data.execution_time ? data.execution_time.toFixed(2) : '?'} seconds</div>
            </div>
        `;
        resultsWrapper.appendChild(summaryDiv);

        // Sort results by index
        const sortedResults = [...data.results].sort((a, b) =>
            (a.network_index || 0) - (b.network_index || 0)
        );

        // Check if any results have errors (used for highlighting final output)
        const hasErrors = sortedResults.some(result => result.error);

        // Create an accordion container for network results
        const accordionContainer = document.createElement('div');
        accordionContainer.className = 'network-results-accordion';

        // Add individual results
        sortedResults.forEach((result, index) => {
            // Extract the actual result content from nested structure
            let resultContent;
            let resultType;

            if (result.error) {
                resultContent = result.error;
                resultType = 'error';
            } else if (result.result) {
                // The API sometimes returns a nested result structure
                if (result.result.result !== undefined) {
                    resultContent = result.result.result;
                    resultType = result.result.type || 'text';
                } else {
                    resultContent = result.result;
                    resultType = 'text';
                }
            } else {
                resultContent = 'No result data';
                resultType = 'text';
            }

            // Create accordion item
            const resultDiv = document.createElement('div');
            resultDiv.className = 'network-result-accordion-item';

            // Result header (always visible)
            const headerDiv = document.createElement('div');
            headerDiv.className = 'accordion-header';

            // Default to closed accordion (but will open the one with error or if it's the last in sequential mode)
            let isOpen = false;

            if ((data.mode === 'sequential' && index === sortedResults.length - 1) ||
                (resultType === 'error')) {
                isOpen = true;
            }

            // Create a text preview of the result
            let resultPreview = '';
            if (typeof resultContent === 'string') {
                resultPreview = resultContent.length > 40 ?
                    resultContent.substring(0, 40) + '...' :
                    resultContent;
            } else {
                try {
                    resultPreview = JSON.stringify(resultContent).substring(0, 40) + '...';
                } catch (e) {
                    resultPreview = 'Complex result data';
                }
            }

            // Format the header
            headerDiv.innerHTML = `
                <div class="header-content">
                    <div class="result-title">
                        <i class="bi bi-diagram-3"></i>
                        <span>Network ${result.network_index !== undefined ? result.network_index + 1 : index + 1}</span>
                        ${resultType === 'error' ?
                            '<span class="result-status error">Error</span>' :
                            '<span class="result-status success">Success</span>'
                        }
                    </div>
                    <div class="result-preview ${resultType === 'error' ? 'error' : ''}">
                        ${resultPreview}
                    </div>
                </div>
                <div class="header-controls">
                    ${result.execution_time ?
                        `<div class="result-time">${result.execution_time.toFixed(2)}s</div>` :
                        ''}
                    <button class="accordion-toggle">
                        <i class="bi bi-chevron-${isOpen ? 'up' : 'down'}"></i>
                    </button>
                </div>
            `;
            resultDiv.appendChild(headerDiv);

            // Result content (collapsible)
            const contentDiv = document.createElement('div');
            contentDiv.className = `accordion-content ${isOpen ? 'open' : ''}`;

            // Create the inner content based on result type
            const innerContent = document.createElement('div');

            if (resultType === 'error') {
                innerContent.className = 'result-error';
                innerContent.textContent = resultContent;
            } else {
                innerContent.className = 'result-content';

                // Format based on content type
                if (typeof resultContent === 'string') {
                    innerContent.textContent = resultContent;
                } else {
                    try {
                        const pre = document.createElement('pre');
                        pre.textContent = JSON.stringify(resultContent, null, 2);
                        innerContent.appendChild(pre);
                    } catch (e) {
                        innerContent.textContent = String(resultContent);
                    }
                }
            }

            contentDiv.appendChild(innerContent);
            resultDiv.appendChild(contentDiv);
            accordionContainer.appendChild(resultDiv);

            // Add toggle functionality
            const toggleButton = headerDiv.querySelector('.accordion-toggle');
            if (toggleButton) {
                toggleButton.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const content = contentDiv;
                    const icon = toggleButton.querySelector('i');

                    if (content.classList.contains('open')) {
                        content.classList.remove('open');
                        icon.classList.remove('bi-chevron-up');
                        icon.classList.add('bi-chevron-down');
                    } else {
                        content.classList.add('open');
                        icon.classList.remove('bi-chevron-down');
                        icon.classList.add('bi-chevron-up');
                    }
                });
            }

            // Make the whole header clickable
            headerDiv.addEventListener('click', (e) => {
                if (!e.target.closest('.accordion-toggle')) {
                    toggleButton.click();
                }
            });
        });

        resultsWrapper.appendChild(accordionContainer);

        // Add final output section based on the execution mode
        if (data.mode === 'sequential' && data.result) {
            // For sequential mode, show the final result (output of last network)
            const finalDiv = document.createElement('div');
            finalDiv.className = 'final-result';

            const finalHeader = document.createElement('div');
            finalHeader.className = 'final-header';
            finalHeader.innerHTML = `
                <i class="bi bi-flag-fill"></i>
                Final Output (Sequential Chain Result)
            `;
            finalDiv.appendChild(finalHeader);

            const finalContent = document.createElement('div');
            finalContent.className = 'final-content';

            if (typeof data.result === 'string') {
                finalContent.textContent = data.result;
            } else {
                try {
                    const pre = document.createElement('pre');
                    pre.textContent = JSON.stringify(data.result, null, 2);
                    finalContent.appendChild(pre);
                } catch (e) {
                    finalContent.textContent = String(data.result);
                }
            }

            finalDiv.appendChild(finalContent);
            resultsWrapper.appendChild(finalDiv);
        }
        else if (data.mode === 'parallel' && !hasErrors) {
            // For parallel mode, highlight the combined results
            const finalDiv = document.createElement('div');
            finalDiv.className = 'parallel-summary';

            finalDiv.innerHTML = `
                <div class="parallel-header">
                    <i class="bi bi-check-circle-fill"></i>
                    All ${data.networks_count} networks executed successfully in parallel
                </div>
                <div class="parallel-note">
                    Each network processed the same input independently.
                    Expand each network above to see individual results.
                </div>
            `;

            resultsWrapper.appendChild(finalDiv);
        }
        else if (hasErrors) {
            // Show error summary if there were any errors
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-summary';

            const errorCount = sortedResults.filter(result => result.error).length;

            errorDiv.innerHTML = `
                <div class="error-header">
                    <i class="bi bi-exclamation-triangle-fill"></i>
                    ${errorCount} of ${data.networks_count} networks encountered errors
                </div>
                <div class="error-note">
                    Check the network results above for details on the specific errors.
                </div>
            `;

            resultsWrapper.appendChild(errorDiv);
        }

        resultContainer.appendChild(resultsWrapper);
    }
    // Handle single network output
    else if (data.result !== undefined) {
        const resultsWrapper = document.createElement('div');
        resultsWrapper.className = 'single-network-result';

        // Create styled success header
        const successHeader = document.createElement('div');
        successHeader.className = 'success-header';
        successHeader.innerHTML = `
            <div class="success-icon">
                <i class="bi bi-check-circle-fill"></i>
            </div>
            <div class="success-title">Network Execution Successful</div>
        `;
        resultsWrapper.appendChild(successHeader);

        // Add content with proper styling
        const contentDiv = document.createElement('div');
        contentDiv.className = 'result-content-wrapper';

        if (data.error) {
            contentDiv.className += ' error';
            contentDiv.innerHTML = `
                <div class="error-message">
                    <i class="bi bi-exclamation-triangle-fill"></i>
                    <span>Error: ${data.error}</span>
                </div>
            `;
        } else {
            const resultContentDiv = document.createElement('div');
            resultContentDiv.className = 'result-content';

            // Format based on type
            if (typeof data.result === 'string') {
                resultContentDiv.textContent = data.result;
            } else {
                try {
                    const pre = document.createElement('pre');
                    pre.textContent = JSON.stringify(data.result, null, 2);
                    resultContentDiv.appendChild(pre);
                } catch (e) {
                    resultContentDiv.textContent = String(data.result);
                }
            }
            contentDiv.appendChild(resultContentDiv);
        }

        resultsWrapper.appendChild(contentDiv);
        resultContainer.appendChild(resultsWrapper);
    }
    // Error case
    else if (data.error) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'single-result error';
        errorDiv.innerHTML = `
            <div class="error-header">
                <i class="bi bi-exclamation-triangle-fill"></i>
                Execution Error
            </div>
            <div class="error-message">
                ${data.error}
            </div>
        `;
        resultContainer.appendChild(errorDiv);
    }
    else {
        const placeholderDiv = document.createElement('div');
        placeholderDiv.className = 'result-placeholder';
        placeholderDiv.textContent = 'No results available';
        resultContainer.appendChild(placeholderDiv);
    }
}

/**
 * Show a notification message
 * @param {string} message - Notification message
 * @param {string} type - Notification type (info, success, warning, error)
 */
function showNotification(message, type = 'info') {
    // Check if notification container exists
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        document.body.appendChild(container);
    }
    
    // Create notification
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    // Add content based on type
    const iconMap = {
        info: 'info-circle',
        success: 'check-circle',
        warning: 'exclamation-triangle',
        error: 'x-circle'
    };
    
    notification.innerHTML = `
        <div class="notification-icon">
            <i class="bi bi-${iconMap[type] || 'info-circle'}"></i>
        </div>
        <div class="notification-message">${message}</div>
        <button class="notification-close">
            <i class="bi bi-x"></i>
        </button>
    `;
    
    // Add to container
    container.appendChild(notification);
    
    // Add close button handler
    const closeButton = notification.querySelector('.notification-close');
    if (closeButton) {
        closeButton.addEventListener('click', () => {
            notification.classList.add('closing');
            setTimeout(() => {
                if (notification.parentNode === container) {
                    container.removeChild(notification);
                }
            }, 300);
        });
    }
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (notification.parentNode === container) {
            notification.classList.add('closing');
            setTimeout(() => {
                if (notification.parentNode === container) {
                    container.removeChild(notification);
                }
            }, 300);
        }
    }, 5000);
}

// Export to window object
window.showNetworkExecutionDialog = showNetworkExecutionDialog;