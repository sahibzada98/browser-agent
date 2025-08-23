class BrowserAgentUI {
    constructor() {
        this.recordBtn = document.getElementById('recordBtn');
        this.flowNameInput = document.getElementById('flowName');
        this.taskDescInput = document.getElementById('taskDescription');
        this.statusDiv = document.getElementById('status');
        this.flowsList = document.getElementById('flowsList');
        
        this.isRecording = false;
        this.init();
    }

    init() {
        this.recordBtn.addEventListener('click', () => this.handleRecord());
        this.loadFlows();
    }

    async handleRecord() {
        const flowName = this.flowNameInput.value.trim();
        const taskDesc = this.taskDescInput.value.trim();

        if (!flowName || !taskDesc) {
            this.showStatus('Please enter both flow name and task description', 'error');
            return;
        }

        if (this.isRecording) {
            await this.stopRecording();
        } else {
            await this.startRecording(flowName, taskDesc);
        }
    }

    async startRecording(flowName, taskDesc) {
        this.setRecordingState(true);
        this.showStatus('Starting workflow recording...', 'info');

        try {
            const response = await fetch('/api/start-recording', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    flow_name: flowName,
                    task_description: taskDesc
                })
            });

            const result = await response.json();
            
            if (response.ok) {
                this.showStatus('Recording started! Perform your actions in the browser.', 'success');
                this.pollRecordingStatus();
            } else {
                throw new Error(result.error || 'Failed to start recording');
            }
        } catch (error) {
            this.showStatus(`Error: ${error.message}`, 'error');
            this.setRecordingState(false);
        }
    }

    async stopRecording() {
        try {
            const response = await fetch('/api/stop-recording', {
                method: 'POST'
            });

            const result = await response.json();
            
            if (response.ok) {
                this.showStatus(`Recording completed! Flow saved as: ${result.flow_name}`, 'success');
                this.clearInputs();
                this.loadFlows(); // Refresh the flows list
            } else {
                throw new Error(result.error || 'Failed to stop recording');
            }
        } catch (error) {
            this.showStatus(`Error: ${error.message}`, 'error');
        } finally {
            this.setRecordingState(false);
        }
    }

    async pollRecordingStatus() {
        if (!this.isRecording) return;

        try {
            const response = await fetch('/api/recording-status');
            const result = await response.json();

            if (result.is_recording) {
                // Still recording, continue polling
                setTimeout(() => this.pollRecordingStatus(), 2000);
            } else {
                // Recording finished
                this.setRecordingState(false);
                if (result.success) {
                    this.showStatus(`Recording completed! Flow saved as: ${result.flow_name}`, 'success');
                    this.clearInputs();
                    this.loadFlows();
                } else {
                    this.showStatus(`Recording failed: ${result.error}`, 'error');
                }
            }
        } catch (error) {
            console.error('Error polling status:', error);
            setTimeout(() => this.pollRecordingStatus(), 2000);
        }
    }

    async loadFlows() {
        this.flowsList.innerHTML = '<p class="loading">Loading flows...</p>';

        try {
            const response = await fetch('/api/flows');
            const flows = await response.json();

            if (flows.length === 0) {
                this.flowsList.innerHTML = '<p class="loading">No workflows found. Record your first workflow!</p>';
                return;
            }

            this.flowsList.innerHTML = flows.map(flow => this.createFlowItem(flow)).join('');
        } catch (error) {
            this.flowsList.innerHTML = '<p class="loading">Error loading flows</p>';
            console.error('Error loading flows:', error);
        }
    }

    createFlowItem(flow) {
        const createdDate = new Date(flow.created * 1000).toLocaleDateString();
        const steps = flow.steps || 'Unknown';
        
        return `
            <div class="flow-item">
                <div class="flow-header">
                    <div>
                        <div class="flow-name">${flow.name}</div>
                        <div class="flow-meta">Created: ${createdDate} | Steps: ${steps}</div>
                    </div>
                    <div class="flow-actions">
                        <button class="btn btn-secondary" onclick="ui.replayFlow('${flow.name}')">
                            ▶️ Replay
                        </button>
                        <button class="btn btn-secondary" onclick="ui.deleteFlow('${flow.name}')" style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);">
                            🗑️ Delete
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    async replayFlow(flowName) {
        this.showStatus(`Starting replay of "${flowName}"...`, 'info');

        try {
            const response = await fetch('/api/replay-flow', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    flow_name: flowName
                })
            });

            const result = await response.json();
            
            if (response.ok) {
                this.showStatus(`Replay started for "${flowName}". Check the browser window.`, 'success');
            } else {
                throw new Error(result.error || 'Failed to start replay');
            }
        } catch (error) {
            this.showStatus(`Error: ${error.message}`, 'error');
        }
    }

    async deleteFlow(flowName) {
        if (!confirm(`Are you sure you want to delete the workflow "${flowName}"?`)) {
            return;
        }

        try {
            const response = await fetch(`/api/flows/${flowName}`, {
                method: 'DELETE'
            });

            const result = await response.json();
            
            if (response.ok) {
                this.showStatus(`Workflow "${flowName}" deleted successfully`, 'success');
                this.loadFlows();
            } else {
                throw new Error(result.error || 'Failed to delete workflow');
            }
        } catch (error) {
            this.showStatus(`Error: ${error.message}`, 'error');
        }
    }

    setRecordingState(recording) {
        this.isRecording = recording;
        
        const btnText = this.recordBtn.querySelector('.btn-text');
        const btnSpinner = this.recordBtn.querySelector('.btn-spinner');
        
        if (recording) {
            btnText.style.display = 'none';
            btnSpinner.style.display = 'inline-flex';
            this.recordBtn.disabled = false;
            this.recordBtn.innerHTML = '<span class="btn-spinner">⏹️ Stop Recording</span>';
        } else {
            this.recordBtn.disabled = false;
            this.recordBtn.innerHTML = '<span class="btn-text">🔴 Record Workflow</span>';
        }
    }

    showStatus(message, type) {
        this.statusDiv.textContent = message;
        this.statusDiv.className = `status-message status-${type}`;
        this.statusDiv.style.display = 'block';

        // Auto-hide success messages after 5 seconds
        if (type === 'success') {
            setTimeout(() => {
                this.statusDiv.style.display = 'none';
            }, 5000);
        }
    }

    clearInputs() {
        this.flowNameInput.value = '';
        this.taskDescInput.value = '';
    }
}

// Initialize the UI when the page loads
const ui = new BrowserAgentUI();