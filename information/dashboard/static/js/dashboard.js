// Global variables
let currentSimulation = null;
let simulationData = null;
let currentRound = 1;
let maxRounds = 20;
let eventFilters = new Set();
let agentFilters = new Set();

// Helper function to reinitialize tooltips after dynamic content
function reinitializeTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    tooltipTriggerList.forEach(function (tooltipTriggerEl) {
        new bootstrap.Tooltip(tooltipTriggerEl)
    });
}

// Agent colors
const agentColors = {
    'agent_1': '#FF6B6B',
    'agent_2': '#4ECDC4',
    'agent_3': '#45B7D1',
    'agent_4': '#F7B731',
    'agent_5': '#5F27CD',
    'agent_6': '#00D2D3',
    'agent_7': '#FF9FF3',
    'agent_8': '#54A0FF',
    'agent_9': '#48DBFB',
    'agent_10': '#FD79A8'
};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    loadSimulations();
    
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
    
    // Set up simulation selector
    document.getElementById('simulationSelect').addEventListener('change', function(e) {
        if (e.target.value) {
            loadSimulation(e.target.value);
        }
    });
});

// Load available simulations
async function loadSimulations() {
    try {
        const response = await fetch('/api/simulations');
        const simulations = await response.json();
        
        const select = document.getElementById('simulationSelect');
        select.innerHTML = '<option value="">Select a simulation...</option>';
        
        simulations.forEach(sim => {
            const option = document.createElement('option');
            option.value = sim.id;
            option.textContent = `${sim.id} (${sim.agents} agents, ${sim.rounds} rounds)`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Failed to load simulations:', error);
    }
}

// Load specific simulation
async function loadSimulation(simId) {
    try {
        // Show loading indicator
        showLoading(true);
        
        // Fetch simulation data
        const response = await fetch(`/api/simulation/${simId}/summary`);
        simulationData = await response.json();
        
        currentSimulation = simId;
        currentRound = 1;
        maxRounds = simulationData.config.simulation.rounds;
        
        // Update UI
        updateSimulationInfo();
        setupFilters();
        updateAgentLegend();
        loadRoundData(currentRound);
        
        // Show main content
        document.getElementById('mainContent').classList.remove('d-none');
        document.getElementById('simulationInfo').classList.remove('d-none');
        
        // Initialize other views
        if (simulationData.statistics) {
            initializeCharts();
        }
        
        // Initialize quantitative analysis
        if (simulationData.performance_metrics) {
            displayQuantitativeAnalysis();
        }
        
        // Initialize task progress view
        if (simulationData.tasks) {
            displayTaskProgress();
        }
        
        // Initialize strategic analysis
        displayStrategicAnalysis();
        
        // Initialize agent network
        displayAgentNetwork();
        
        // Initialize strategic reports
        if (simulationData.strategic_reports) {
            initializeStrategicReports();
        }
        
        // Initialize cooperation analysis
        if (simulationData.cooperation_dynamics) {
            displayCooperationAnalysis();
        }
        
        // Initialize information value analysis
        if (simulationData.information_value) {
            displayInformationValueAnalysis();
        }
        
        showLoading(false);
    } catch (error) {
        console.error('Failed to load simulation:', error);
        showLoading(false);
    }
}

// Update simulation info display
function updateSimulationInfo() {
    document.getElementById('simId').textContent = currentSimulation;
    document.getElementById('numAgents').textContent = simulationData.config.simulation.agents;
    document.getElementById('numRounds').textContent = simulationData.config.simulation.rounds;
    document.getElementById('simStatus').textContent = simulationData.final_results ? 'Completed' : 'In Progress';
}

// Setup filters
function setupFilters() {
    // Event type filters
    const eventTypes = Object.keys(simulationData.statistics.event_types);
    const eventFiltersDiv = document.getElementById('eventTypeFilters');
    eventFiltersDiv.innerHTML = '';
    
    eventTypes.forEach(type => {
        const div = document.createElement('div');
        div.className = 'filter-checkbox';
        div.innerHTML = `
            <input type="checkbox" id="filter_${type}" value="${type}" checked>
            <label for="filter_${type}">${formatEventType(type)} (${simulationData.statistics.event_types[type]})</label>
        `;
        eventFiltersDiv.appendChild(div);
    });
    
    // Agent filters
    const agents = Object.keys(simulationData.agents);
    const agentFiltersDiv = document.getElementById('agentFilters');
    agentFiltersDiv.innerHTML = '';
    
    agents.forEach(agent => {
        const div = document.createElement('div');
        div.className = 'filter-checkbox';
        div.innerHTML = `
            <input type="checkbox" id="filter_${agent}" value="${agent}" checked>
            <label for="filter_${agent}">
                <span class="agent-badge agent-${agent.split('_')[1]}">${agent}</span>
            </label>
        `;
        agentFiltersDiv.appendChild(div);
    });
}

// Update agent legend
function updateAgentLegend() {
    const legendDiv = document.getElementById('agentLegend');
    legendDiv.innerHTML = '';
    
    Object.keys(simulationData.agents).forEach(agent => {
        const agentNum = agent.split('_')[1];
        const div = document.createElement('div');
        div.className = 'mb-2';
        div.innerHTML = `
            <span class="agent-badge agent-${agentNum}">${agent}</span>
            <small>Score: ${simulationData.agents[agent].score}</small>
        `;
        legendDiv.appendChild(div);
    });
}

// Load round data
async function loadRoundData(roundNum) {
    try {
        const response = await fetch(`/api/simulation/${currentSimulation}/rounds/${roundNum}`);
        const roundEvents = await response.json();
        
        displayRoundTimeline(roundEvents);
        updateRoundNavigation();
    } catch (error) {
        console.error('Failed to load round data:', error);
    }
}

// Display round timeline
function displayRoundTimeline(events) {
    const timelineDiv = document.getElementById('timelineContent');
    timelineDiv.innerHTML = '';
    
    // Group events by type for summary
    const eventSummary = {};
    events.forEach(event => {
        if (!eventSummary[event.event_type]) {
            eventSummary[event.event_type] = 0;
        }
        eventSummary[event.event_type]++;
    });
    
    // Round summary
    const summaryDiv = document.createElement('div');
    summaryDiv.className = 'alert alert-secondary mb-3';
    summaryDiv.innerHTML = `
        <h5>Round ${currentRound} Summary</h5>
        <p>${Object.entries(eventSummary).map(([type, count]) => 
            `${formatEventType(type)}: ${count}`).join(' | ')}</p>
    `;
    timelineDiv.appendChild(summaryDiv);
    
    // Display events
    events.forEach(event => {
        if (shouldDisplayEvent(event)) {
            const eventCard = createEventCard(event);
            timelineDiv.appendChild(eventCard);
        }
    });
}

// Create event card
function createEventCard(event) {
    const card = document.createElement('div');
    card.className = `card event-card ${event.event_type}`;
    
    let content = '';
    const timestamp = new Date(event.timestamp).toLocaleTimeString();
    
    switch (event.event_type) {
        case 'agent_action':
            const agentNum = event.data.agent_id.split('_')[1];
            content = `
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <span class="agent-badge agent-${agentNum}">${event.data.agent_id}</span>
                            <strong>${event.data.action.action}</strong>
                            ${event.data.action.to ? `→ <span class="agent-badge agent-${event.data.action.to.split('_')[1]}">${event.data.action.to}</span>` : ''}
                        </div>
                        <small class="text-muted">${timestamp}</small>
                    </div>
                    ${event.data.action.content ? `<p class="mt-2 mb-1">${event.data.action.content}</p>` : ''}
                    ${event.data.private_thoughts ? `<small class="private-thoughts" data-thoughts="${event.data.private_thoughts}">View thoughts</small>` : ''}
                </div>
            `;
            break;
            
        case 'message':
            const fromNum = event.data.from === 'system' ? '0' : event.data.from.split('_')[1];
            const toNum = event.data.to === 'system' ? '0' : event.data.to.split('_')[1];
            content = `
                <div class="card-body">
                    <div class="message-flow">
                        <span class="agent-badge agent-${fromNum}">${event.data.from}</span>
                        <div class="message-arrow"></div>
                        <span class="agent-badge agent-${toNum}">${event.data.to}</span>
                    </div>
                    <p class="mt-2 mb-0">${event.data.content}</p>
                    <small class="text-muted">${timestamp}</small>
                </div>
            `;
            break;
            
        case 'information_exchange':
            const fromAgentNum = event.data.from_agent.split('_')[1];
            const toAgentNum = event.data.to_agent.split('_')[1];
            content = `
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <span class="agent-badge agent-${fromAgentNum}">${event.data.from_agent}</span>
                            → 
                            <span class="agent-badge agent-${toAgentNum}">${event.data.to_agent}</span>
                            <strong>Information Transfer</strong>
                        </div>
                        <small class="text-muted">${timestamp}</small>
                    </div>
                    <ul class="mt-2 mb-0">
                        ${event.data.information.map(info => `<li>${info}</li>`).join('')}
                    </ul>
                </div>
            `;
            break;
            
        case 'task_completion':
            const completingAgentNum = event.data.agent_id.split('_')[1];
            content = `
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <span class="agent-badge agent-${completingAgentNum}">${event.data.agent_id}</span>
                            <strong>Task Completed!</strong>
                            ${event.data.task_id}
                        </div>
                        <small class="text-muted">${timestamp}</small>
                    </div>
                    <p class="mt-2 mb-0">
                        Points: ${event.data.points_awarded || 0}
                        ${event.data.first_completion_bonus ? '<span class="badge bg-success ms-2">First!</span>' : ''}
                    </p>
                </div>
            `;
            break;
            
        case 'private_thoughts':
            const thinkingAgentNum = event.data.agent_id.split('_')[1];
            content = `
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <span class="agent-badge agent-${thinkingAgentNum}">${event.data.agent_id}</span>
                            <em>Private Thoughts</em>
                        </div>
                        <small class="text-muted">${timestamp}</small>
                    </div>
                    <p class="mt-2 mb-0 text-muted">${event.data.thoughts}</p>
                </div>
            `;
            break;
            
        default:
            content = `
                <div class="card-body">
                    <strong>${formatEventType(event.event_type)}</strong>
                    <pre class="mt-2 mb-0">${JSON.stringify(event.data, null, 2)}</pre>
                    <small class="text-muted">${timestamp}</small>
                </div>
            `;
    }
    
    card.innerHTML = content;
    return card;
}

// Check if event should be displayed based on filters
function shouldDisplayEvent(event) {
    // Check event type filter
    const eventCheckbox = document.getElementById(`filter_${event.event_type}`);
    if (eventCheckbox && !eventCheckbox.checked) {
        return false;
    }
    
    // Check agent filter
    const agentId = event.data.agent_id || event.data.from_agent || event.data.from;
    if (agentId && agentId !== 'system') {
        const agentCheckbox = document.getElementById(`filter_${agentId}`);
        if (agentCheckbox && !agentCheckbox.checked) {
            return false;
        }
    }
    
    return true;
}

// Format event type for display
function formatEventType(type) {
    return type.split('_').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
}

// Navigation functions
function previousRound() {
    if (currentRound > 1) {
        currentRound--;
        loadRoundData(currentRound);
    }
}

function nextRound() {
    if (currentRound < maxRounds) {
        currentRound++;
        loadRoundData(currentRound);
    }
}

function updateRoundNavigation() {
    document.getElementById('currentRoundDisplay').textContent = `Round ${currentRound}`;
    document.querySelector('button[onclick="previousRound()"]').disabled = currentRound === 1;
    document.querySelector('button[onclick="nextRound()"]').disabled = currentRound === maxRounds;
}

// Apply filters
function applyFilters() {
    loadRoundData(currentRound);
}

// Initialize charts
function initializeCharts() {
    // Score progression chart
    const scoreCtx = document.getElementById('scoreChart').getContext('2d');
    const scoreData = prepareScoreData();
    
    new Chart(scoreCtx, {
        type: 'line',
        data: scoreData,
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Agent Score Progression'
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Round'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Score'
                    }
                }
            }
        }
    });
    
    // Display final rankings
    displayFinalRankings();
}

// Prepare score data for chart
function prepareScoreData() {
    if (!simulationData.scores_over_time) {
        console.error('No score data available');
        return { labels: [], datasets: [] };
    }
    
    const agents = Object.keys(simulationData.scores_over_time);
    const rounds = Array.from({length: maxRounds}, (_, i) => i + 1);
    
    const datasets = agents.map((agent, index) => {
        const agentNum = agent.split('_')[1];
        const scoreData = simulationData.scores_over_time[agent];
        
        return {
            label: agent,
            data: scoreData.map(item => item.score),
            borderColor: agentColors[agent],
            backgroundColor: agentColors[agent] + '20',
            tension: 0.1
        };
    });
    
    return {
        labels: rounds,
        datasets: datasets
    };
}

// Display final rankings
function displayFinalRankings() {
    const rankingsDiv = document.getElementById('finalRankings');
    const agents = Object.values(simulationData.agents)
        .sort((a, b) => b.score - a.score);
    
    rankingsDiv.innerHTML = agents.map((agent, index) => {
        const agentNum = agent.id.split('_')[1];
        return `
            <div class="d-flex justify-content-between align-items-center mb-2">
                <div>
                    <strong>${index + 1}.</strong>
                    <span class="agent-badge agent-${agentNum}">${agent.id}</span>
                </div>
                <span class="badge bg-primary">${agent.score} pts</span>
            </div>
        `;
    }).join('');
}

// Loading indicator
function showLoading(show) {
    if (show) {
        // Add loading indicator
    } else {
        // Remove loading indicator
    }
}

// Display quantitative analysis
function displayQuantitativeAnalysis() {
    const perfMetrics = simulationData.performance_metrics;
    const commMetrics = simulationData.communication_metrics;
    
    if (!perfMetrics || !commMetrics) {
        console.error('Metrics data not available');
        return;
    }
    
    // Display overall metrics
    document.getElementById('totalTasks').textContent = perfMetrics.overall.total_tasks_completed;
    document.getElementById('totalPoints').textContent = perfMetrics.overall.total_points_awarded;
    document.getElementById('avgPointsPerTask').textContent = perfMetrics.overall.average_points_per_task.toFixed(1);
    document.getElementById('firstCompletionRate').textContent = (perfMetrics.overall.first_completion_rate * 100).toFixed(1) + '%';
    
    // Display agent performance table
    displayAgentPerformanceTable(perfMetrics.by_agent);
    
    // Display communication charts
    displayCommunicationCharts(commMetrics);
    
    // Display cooperation matrix
    displayCooperationMatrix(commMetrics.info_flow_matrix);
    
    // Display message content analysis
    displayMessageAnalysis();
}

// Display agent performance table
function displayAgentPerformanceTable(agentMetrics) {
    const tbody = document.getElementById('agentPerformanceBody');
    tbody.innerHTML = '';
    
    // Sort agents by total points
    const sortedAgents = Object.entries(agentMetrics)
        .sort((a, b) => b[1].total_points - a[1].total_points);
    
    sortedAgents.forEach(([agentId, metrics]) => {
        const agentNum = agentId.split('_')[1];
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><span class="agent-badge agent-${agentNum}">${agentId}</span></td>
            <td>${metrics.tasks_completed}</td>
            <td>${metrics.total_points}</td>
            <td>${metrics.average_points_per_task.toFixed(1)}</td>
            <td>${metrics.first_completions}</td>
            <td>${metrics.messages_sent}</td>
            <td>${metrics.info_sent}</td>
            <td>${(metrics.response_rate * 100).toFixed(1)}%</td>
        `;
        tbody.appendChild(row);
    });
}

// Display communication charts
function displayCommunicationCharts(commMetrics) {
    // Communication summary
    const summaryList = document.getElementById('commSummary');
    summaryList.innerHTML = `
        <li><strong>Total Messages:</strong> ${commMetrics.summary.total_messages}</li>
        <li><strong>Direct Messages:</strong> ${commMetrics.summary.direct_messages}</li>
        <li><strong>Broadcasts:</strong> ${commMetrics.summary.broadcasts}</li>
        <li><strong>Avg Response Time:</strong> ${commMetrics.summary.avg_response_time.toFixed(1)}s</li>
    `;
    
    // Communication flow chart
    const ctx = document.getElementById('communicationChart').getContext('2d');
    const commData = prepareCommFlowData(commMetrics.communication_matrix);
    
    new Chart(ctx, {
        type: 'bar',
        data: commData,
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Message Flow Between Agents'
                }
            },
            scales: {
                x: {
                    stacked: true,
                    title: {
                        display: true,
                        text: 'From Agent'
                    }
                },
                y: {
                    stacked: true,
                    title: {
                        display: true,
                        text: 'Number of Messages'
                    }
                }
            }
        }
    });
}

// Prepare communication flow data for chart
function prepareCommFlowData(commMatrix) {
    const agents = Object.keys(simulationData.agents);
    const datasets = [];
    
    agents.forEach((toAgent, index) => {
        const agentNum = toAgent.split('_')[1];
        const data = agents.map(fromAgent => {
            return commMatrix[fromAgent] ? (commMatrix[fromAgent][toAgent] || 0) : 0;
        });
        
        datasets.push({
            label: `To ${toAgent}`,
            data: data,
            backgroundColor: agentColors[toAgent] + '80',
            borderColor: agentColors[toAgent],
            borderWidth: 1
        });
    });
    
    return {
        labels: agents,
        datasets: datasets
    };
}

// Display cooperation matrix
function displayCooperationMatrix(infoFlowMatrix) {
    const canvas = document.getElementById('cooperationMatrix');
    const ctx = canvas.getContext('2d');
    const agents = Object.keys(simulationData.agents);
    
    // Set canvas size
    canvas.width = 400;
    canvas.height = 400;
    
    const cellSize = 60;
    const padding = 80;
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw labels
    ctx.font = '12px Arial';
    ctx.fillStyle = '#333';
    
    agents.forEach((agent, i) => {
        const agentNum = agent.split('_')[1];
        
        // Row labels
        ctx.fillText(agent, 10, padding + i * cellSize + cellSize/2);
        
        // Column labels
        ctx.save();
        ctx.translate(padding + i * cellSize + cellSize/2, padding - 10);
        ctx.rotate(-Math.PI/4);
        ctx.fillText(agent, 0, 0);
        ctx.restore();
    });
    
    // Draw matrix
    agents.forEach((fromAgent, i) => {
        agents.forEach((toAgent, j) => {
            const value = infoFlowMatrix[fromAgent] ? (infoFlowMatrix[fromAgent][toAgent] || 0) : 0;
            
            // Color based on value
            const intensity = Math.min(value / 10, 1); // Normalize to 0-1
            const color = `rgba(76, 175, 80, ${intensity})`;
            
            ctx.fillStyle = color;
            ctx.fillRect(padding + j * cellSize, padding + i * cellSize, cellSize - 2, cellSize - 2);
            
            // Draw value
            if (value > 0) {
                ctx.fillStyle = intensity > 0.5 ? '#fff' : '#333';
                ctx.font = '14px Arial';
                ctx.textAlign = 'center';
                ctx.fillText(value.toString(), padding + j * cellSize + cellSize/2, padding + i * cellSize + cellSize/2 + 5);
            }
        });
    });
    
    // Add title
    ctx.fillStyle = '#333';
    ctx.font = '16px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('Information Flow Matrix (From → To)', canvas.width/2, 20);
}

// Display task progress
function displayTaskProgress() {
    const taskContainer = document.getElementById('taskProgressContent');
    const tasks = simulationData.tasks;
    
    if (!tasks || Object.keys(tasks).length === 0) {
        taskContainer.innerHTML = '<p class="text-muted">No tasks completed yet.</p>';
        return;
    }
    
    // Group tasks by agent
    const tasksByAgent = {};
    Object.entries(tasks).forEach(([taskId, task]) => {
        if (!tasksByAgent[task.completed_by]) {
            tasksByAgent[task.completed_by] = [];
        }
        tasksByAgent[task.completed_by].push(task);
    });
    
    // Create task cards
    let html = '<div class="row">';
    
    Object.entries(tasksByAgent).forEach(([agentId, agentTasks]) => {
        const agentNum = agentId.split('_')[1];
        
        html += `
            <div class="col-md-6 mb-4">
                <div class="card">
                    <div class="card-header">
                        <h5><span class="agent-badge agent-${agentNum}">${agentId}</span> Tasks (${agentTasks.length})</h5>
                    </div>
                    <div class="card-body">
                        <div class="list-group">
        `;
        
        // Sort tasks by round
        agentTasks.sort((a, b) => a.round - b.round);
        
        agentTasks.forEach(task => {
            const statusClass = task.success ? 'list-group-item-success' : 'list-group-item-danger';
            html += `
                <div class="list-group-item ${statusClass}">
                    <div class="d-flex w-100 justify-content-between">
                        <h6 class="mb-1">${task.id}</h6>
                        <small>Round ${task.round}</small>
                    </div>
                    <p class="mb-1">
                        <strong>Points:</strong> ${task.points_awarded || 0}
                        ${task.points_awarded > 10 ? '<span class="badge bg-warning ms-2">First!</span>' : ''}
                    </p>
                    <small class="text-muted">${new Date(task.timestamp).toLocaleTimeString()}</small>
                </div>
            `;
        });
        
        html += `
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    
    // Add summary statistics
    const totalTasks = Object.keys(tasks).length;
    const totalPoints = Object.values(tasks).reduce((sum, task) => sum + (task.points_awarded || 0), 0);
    const avgPoints = (totalPoints / totalTasks).toFixed(1);
    
    html = `
        <div class="alert alert-info mb-4">
            <h5>Task Summary</h5>
            <p class="mb-0">
                <strong>Total Tasks Completed:</strong> ${totalTasks} | 
                <strong>Total Points Awarded:</strong> ${totalPoints} | 
                <strong>Average Points per Task:</strong> ${avgPoints}
            </p>
        </div>
    ` + html;
    
    taskContainer.innerHTML = html;
}

// Display strategic analysis
function displayStrategicAnalysis() {
    const analysisContainer = document.getElementById('analysisContent');
    
    // Use the enhanced strategic analysis from backend if available
    if (simulationData.strategic_analysis) {
        displayEnhancedStrategicAnalysis(simulationData.strategic_analysis);
        return;
    }
    
    // Fallback to client-side analysis
    if (!simulationData.private_thoughts || simulationData.private_thoughts.length === 0) {
        analysisContainer.innerHTML = '<p class="text-muted">No strategic analysis data available.</p>';
        return;
    }
    
    let html = '<div class="container-fluid">';
    
    // Strategic Keywords Analysis
    html += `
        <div class="row mb-4">
            <div class="col-12">
                <h4>Strategic Behavior Analysis</h4>
                <p class="text-muted">Analysis of agent strategies based on their private thoughts</p>
            </div>
        </div>
    `;
    
    // Analyze private thoughts for strategic patterns
    const thoughtAnalysis = analyzePrivateThoughts(simulationData.private_thoughts);
    
    // Display agent strategy cards
    html += '<div class="row">';
    
    Object.entries(thoughtAnalysis.byAgent).forEach(([agentId, analysis]) => {
        const agentNum = agentId.split('_')[1];
        const dominantStrategy = getDominantStrategy(analysis);
        
        html += `
            <div class="col-md-6 mb-4">
                <div class="card">
                    <div class="card-header">
                        <h5><span class="agent-badge agent-${agentNum}">${agentId}</span> Strategic Profile</h5>
                    </div>
                    <div class="card-body">
                        <h6>Dominant Strategy: <span class="badge bg-${dominantStrategy.color}">${dominantStrategy.name}</span></h6>
                        <div class="mt-3">
                            <h6>Behavioral Indicators:</h6>
                            <ul class="list-unstyled">
                                <li><i class="bi bi-handshake"></i> Cooperation: ${analysis.cooperation}</li>
                                <li><i class="bi bi-trophy"></i> Competition: ${analysis.competition}</li>
                                <li><i class="bi bi-shield-lock"></i> Information Hoarding: ${analysis.hoarding}</li>
                                <li><i class="bi bi-arrow-left-right"></i> Reciprocity: ${analysis.reciprocity}</li>
                                <li><i class="bi bi-exclamation-triangle"></i> Deception: ${analysis.deception}</li>
                            </ul>
                        </div>
                        <div class="mt-3">
                            <h6>Key Phrases:</h6>
                            <div class="text-muted small">
                                ${analysis.keyPhrases.slice(0, 3).map(phrase => 
                                    `<span class="badge bg-light text-dark me-1">${phrase}</span>`
                                ).join('')}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    
    // Overall patterns
    html += `
        <div class="row mt-4">
            <div class="col-12">
                <h4>Simulation-Wide Patterns</h4>
            </div>
            <div class="col-md-4">
                <div class="card text-center">
                    <div class="card-body">
                        <h5>Cooperation Level</h5>
                        <h2 class="text-success">${thoughtAnalysis.overall.cooperationScore.toFixed(1)}%</h2>
                        <small class="text-muted">Based on cooperative language</small>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card text-center">
                    <div class="card-body">
                        <h5>Competition Level</h5>
                        <h2 class="text-warning">${thoughtAnalysis.overall.competitionScore.toFixed(1)}%</h2>
                        <small class="text-muted">Based on competitive language</small>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card text-center">
                    <div class="card-body">
                        <h5>Deception Attempts</h5>
                        <h2 class="text-danger">${thoughtAnalysis.overall.deceptionCount}</h2>
                        <small class="text-muted">Mentions of misleading/withholding</small>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    html += '</div>';
    analysisContainer.innerHTML = html;
}

// Analyze private thoughts for strategic patterns
function analyzePrivateThoughts(thoughts) {
    const analysis = {
        byAgent: {},
        overall: {
            cooperationScore: 0,
            competitionScore: 0,
            deceptionCount: 0
        }
    };
    
    // Keywords for different strategies
    const keywords = {
        cooperation: ['cooperat', 'help', 'share', 'assist', 'support', 'goodwill', 'trust', 'reciproc'],
        competition: ['compet', 'win', 'beat', 'rank', 'lead', 'advantage', 'strategic', 'edge'],
        hoarding: ['hoard', 'keep', 'withhold', 'protect', 'careful', 'selective', 'cautious'],
        reciprocity: ['reciproc', 'exchange', 'trade', 'return', 'quid pro quo', 'mutual'],
        deception: ['decei', 'lie', 'mislead', 'false', 'trick', 'manipulat', 'pretend']
    };
    
    // Initialize agent analysis
    const agents = new Set();
    thoughts.forEach(thought => agents.add(thought.agent_id));
    
    agents.forEach(agentId => {
        analysis.byAgent[agentId] = {
            cooperation: 0,
            competition: 0,
            hoarding: 0,
            reciprocity: 0,
            deception: 0,
            keyPhrases: [],
            thoughtCount: 0
        };
    });
    
    // Analyze each thought
    thoughts.forEach(thought => {
        const agentId = thought.agent_id;
        const text = thought.thoughts.toLowerCase();
        
        analysis.byAgent[agentId].thoughtCount++;
        
        // Count keyword occurrences
        Object.entries(keywords).forEach(([strategy, words]) => {
            words.forEach(word => {
                if (text.includes(word)) {
                    analysis.byAgent[agentId][strategy]++;
                }
            });
        });
        
        // Extract key phrases (simple approach - sentences with strategic keywords)
        const sentences = thought.thoughts.split(/[.!?]+/);
        sentences.forEach(sentence => {
            if (sentence.length > 20 && sentence.length < 100) {
                for (const [strategy, words] of Object.entries(keywords)) {
                    if (words.some(word => sentence.toLowerCase().includes(word))) {
                        analysis.byAgent[agentId].keyPhrases.push(sentence.trim());
                        break;
                    }
                }
            }
        });
    });
    
    // Calculate overall scores
    let totalCooperation = 0;
    let totalCompetition = 0;
    let totalDeception = 0;
    let totalThoughts = 0;
    
    Object.values(analysis.byAgent).forEach(agentAnalysis => {
        totalCooperation += agentAnalysis.cooperation;
        totalCompetition += agentAnalysis.competition;
        totalDeception += agentAnalysis.deception;
        totalThoughts += agentAnalysis.thoughtCount;
    });
    
    if (totalThoughts > 0) {
        analysis.overall.cooperationScore = (totalCooperation / totalThoughts) * 100;
        analysis.overall.competitionScore = (totalCompetition / totalThoughts) * 100;
        analysis.overall.deceptionCount = totalDeception;
    }
    
    return analysis;
}

// Determine dominant strategy
function getDominantStrategy(agentAnalysis) {
    const strategies = {
        cooperation: { name: 'Cooperative', color: 'success', score: agentAnalysis.cooperation },
        competition: { name: 'Competitive', color: 'warning', score: agentAnalysis.competition },
        hoarding: { name: 'Information Hoarder', color: 'info', score: agentAnalysis.hoarding },
        reciprocity: { name: 'Reciprocal', color: 'primary', score: agentAnalysis.reciprocity },
        deception: { name: 'Deceptive', color: 'danger', score: agentAnalysis.deception }
    };
    
    let dominant = { name: 'Balanced', color: 'secondary', score: 0 };
    
    Object.values(strategies).forEach(strategy => {
        if (strategy.score > dominant.score) {
            dominant = strategy;
        }
    });
    
    return dominant;
}

// Display message content analysis
function displayMessageAnalysis() {
    if (!simulationData.messages || simulationData.messages.length === 0) {
        return;
    }
    
    // Analyze messages for patterns
    const messageAnalysis = analyzeMessagePatterns(simulationData.messages);
    
    // Display message pattern chart
    const ctx = document.getElementById('messagePatternChart').getContext('2d');
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Requests', 'Offers', 'Confirmations', 'Refusals', 'Strategic', 'Other'],
            datasets: [{
                data: [
                    messageAnalysis.patterns.requests,
                    messageAnalysis.patterns.offers,
                    messageAnalysis.patterns.confirmations,
                    messageAnalysis.patterns.refusals,
                    messageAnalysis.patterns.strategic,
                    messageAnalysis.patterns.other
                ],
                backgroundColor: [
                    '#FF6B6B',
                    '#4ECDC4',
                    '#45B7D1',
                    '#F7B731',
                    '#5F27CD',
                    '#95A5A6'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Message Types Distribution'
                },
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
    
    // Display deception analysis
    const deceptionDiv = document.getElementById('deceptionAnalysis');
    let deceptionHtml = `
        <div class="card">
            <div class="card-header">
                <h5>Strategic Communication Analysis</h5>
            </div>
            <div class="card-body">
                <h6>Deception Indicators</h6>
                <p class="text-muted small">Based on discrepancies between messages and private thoughts</p>
    `;
    
    if (messageAnalysis.deception.instances.length > 0) {
        deceptionHtml += '<div class="list-group">';
        messageAnalysis.deception.instances.slice(0, 5).forEach(instance => {
            const agentNum = instance.agent.split('_')[1];
            deceptionHtml += `
                <div class="list-group-item">
                    <div class="d-flex w-100 justify-content-between">
                        <h6 class="mb-1">
                            <span class="agent-badge agent-${agentNum}">${instance.agent}</span>
                            <span class="badge bg-warning">Potential Deception</span>
                        </h6>
                        <small>Round ${instance.round}</small>
                    </div>
                    <p class="mb-1 small">Message: "${instance.message}"</p>
                    <p class="mb-0 text-muted small">Thought: "${instance.thought}"</p>
                </div>
            `;
        });
        deceptionHtml += '</div>';
    } else {
        deceptionHtml += '<p class="text-muted">No clear deception patterns detected</p>';
    }
    
    deceptionHtml += `
                <div class="mt-3">
                    <h6>Communication Patterns</h6>
                    <ul class="list-unstyled">
                        <li><strong>Promise/Delivery Rate:</strong> ${(messageAnalysis.trustMetrics.promiseDeliveryRate * 100).toFixed(1)}%</li>
                        <li><strong>Request Success Rate:</strong> ${(messageAnalysis.trustMetrics.requestSuccessRate * 100).toFixed(1)}%</li>
                        <li><strong>Information Accuracy:</strong> ${(messageAnalysis.trustMetrics.informationAccuracy * 100).toFixed(1)}%</li>
                    </ul>
                </div>
            </div>
        </div>
    `;
    
    deceptionDiv.innerHTML = deceptionHtml;
}

// Analyze message patterns
function analyzeMessagePatterns(messages) {
    const analysis = {
        patterns: {
            requests: 0,
            offers: 0,
            confirmations: 0,
            refusals: 0,
            strategic: 0,
            other: 0
        },
        deception: {
            instances: []
        },
        trustMetrics: {
            promiseDeliveryRate: 0,
            requestSuccessRate: 0,
            informationAccuracy: 1.0
        }
    };
    
    // Pattern keywords
    const patterns = {
        requests: ['need', 'require', 'could you', 'please share', 'can you', 'would you'],
        offers: ['i can', 'i will', 'here is', 'sending', 'sharing', 'providing'],
        confirmations: ['received', 'thank', 'got it', 'confirmed', 'acknowledged'],
        refusals: ['cannot', 'unable', 'sorry', 'no', 'refuse', 'decline'],
        strategic: ['strategic', 'careful', 'consider', 'think', 'plan', 'competitive']
    };
    
    // Track promises and deliveries
    const promises = [];
    const deliveries = [];
    const requests = [];
    const responses = [];
    
    messages.forEach(message => {
        if (message.from === 'system' || !message.content) return;
        
        const content = message.content.toLowerCase();
        let categorized = false;
        
        // Categorize message
        for (const [pattern, keywords] of Object.entries(patterns)) {
            if (keywords.some(keyword => content.includes(keyword))) {
                analysis.patterns[pattern]++;
                categorized = true;
                
                // Track specific patterns
                if (pattern === 'requests') {
                    requests.push(message);
                } else if (pattern === 'offers') {
                    promises.push(message);
                }
                break;
            }
        }
        
        if (!categorized) {
            analysis.patterns.other++;
        }
    });
    
    // Detect potential deception by comparing messages with private thoughts
    if (simulationData.private_thoughts) {
        const thoughtsByAgent = {};
        simulationData.private_thoughts.forEach(thought => {
            if (!thoughtsByAgent[thought.agent_id]) {
                thoughtsByAgent[thought.agent_id] = [];
            }
            thoughtsByAgent[thought.agent_id].push(thought);
        });
        
        messages.forEach(message => {
            if (message.from === 'system') return;
            
            // Find corresponding thoughts near this message timestamp
            const agentThoughts = thoughtsByAgent[message.from] || [];
            const messageTime = new Date(message.timestamp || message.event_timestamp);
            
            agentThoughts.forEach(thought => {
                const thoughtTime = new Date(thought.timestamp);
                const timeDiff = Math.abs(messageTime - thoughtTime) / 1000; // seconds
                
                // If thought is within 30 seconds of message
                if (timeDiff < 30) {
                    const messageContent = message.content.toLowerCase();
                    const thoughtContent = thought.thoughts.toLowerCase();
                    
                    // Look for contradictions
                    if ((messageContent.includes('will share') && thoughtContent.includes('withhold')) ||
                        (messageContent.includes('happy to') && thoughtContent.includes('reluctant')) ||
                        (messageContent.includes('cooperat') && thoughtContent.includes('compet')) ||
                        (thoughtContent.includes('mislead') || thoughtContent.includes('trick'))) {
                        
                        analysis.deception.instances.push({
                            agent: message.from,
                            round: thought.round || 0,
                            message: message.content.substring(0, 100),
                            thought: thought.thoughts.substring(0, 100)
                        });
                    }
                }
            });
        });
    }
    
    // Calculate trust metrics
    if (requests.length > 0) {
        // Simple heuristic: if a request is followed by an information exchange, consider it successful
        const successfulRequests = requests.filter(request => {
            // Check if there's a subsequent info exchange to the requester
            return simulationData.information_flows.some(flow => 
                flow.to === request.from && 
                new Date(flow.timestamp) > new Date(request.timestamp || request.event_timestamp)
            );
        });
        analysis.trustMetrics.requestSuccessRate = successfulRequests.length / requests.length;
    }
    
    // All information exchanges are considered accurate in this simulation
    analysis.trustMetrics.informationAccuracy = 1.0;
    
    // Promise delivery rate (simplified)
    analysis.trustMetrics.promiseDeliveryRate = promises.length > 0 ? 0.8 : 0; // Placeholder
    
    return analysis;
}

// Display agent network visualization with quantitative metrics
function displayAgentNetwork() {
    if (!simulationData.communication_metrics || !simulationData.agents) {
        console.log('No network data available');
        return;
    }
    
    // Calculate all network metrics first
    const networkMetrics = calculateNetworkMetrics();
    
    // Display each visualization
    displayCommunicationHeatmap(networkMetrics.commMatrix);
    displayResponseRateHeatmap(networkMetrics.responseMatrix);
    displayInfoFlowBalance(networkMetrics.infoBalance);
    displayCommunicationEfficiency(networkMetrics.efficiency);
    displayCentralityMetrics(networkMetrics.centrality);
    displayNetworkEvolution(networkMetrics.evolution);
    displayNetworkInsights(networkMetrics);
}

// Calculate comprehensive network metrics
function calculateNetworkMetrics() {
    const agents = Object.keys(simulationData.agents);
    const commMatrix = simulationData.communication_metrics.communication_matrix;
    const infoFlows = simulationData.information_flows || [];
    const messages = simulationData.messages || [];
    
    // Initialize metrics
    const metrics = {
        commMatrix: commMatrix,
        responseMatrix: {},
        infoBalance: {},
        efficiency: {},
        centrality: {
            degree: {},
            betweenness: {},
            infoBrokerage: {}
        },
        evolution: {
            rounds: [],
            activeConnections: [],
            messageVolume: [],
            networkDensity: []
        }
    };
    
    // Calculate response rates
    const requests = {};
    const responses = {};
    
    agents.forEach(from => {
        requests[from] = {};
        responses[from] = {};
        agents.forEach(to => {
            if (from !== to) {
                requests[from][to] = 0;
                responses[from][to] = 0;
            }
        });
    });
    
    // Analyze messages for requests and responses
    messages.forEach(msg => {
        if (msg.from !== 'system' && msg.to !== 'system') {
            const content = (msg.content || '').toLowerCase();
            if (content.includes('need') || content.includes('require') || content.includes('please share')) {
                requests[msg.from][msg.to] = (requests[msg.from][msg.to] || 0) + 1;
            }
        }
    });
    
    // Count information exchanges as responses
    infoFlows.forEach(flow => {
        if (flow.from !== flow.to) {
            responses[flow.from][flow.to] = (responses[flow.from][flow.to] || 0) + flow.information.length;
        }
    });
    
    // Calculate response rate matrix
    metrics.responseMatrix = {};
    agents.forEach(requester => {
        metrics.responseMatrix[requester] = {};
        agents.forEach(responder => {
            if (requester !== responder && requests[requester][responder] > 0) {
                metrics.responseMatrix[requester][responder] = 
                    (responses[responder][requester] / requests[requester][responder]) * 100;
            } else {
                metrics.responseMatrix[requester][responder] = 0;
            }
        });
    });
    
    // Calculate information flow balance
    agents.forEach(agent => {
        const agentData = simulationData.agents[agent];
        metrics.infoBalance[agent] = {
            shared: agentData.information_sent || 0,
            received: agentData.information_received || 0,
            netFlow: (agentData.information_received || 0) - (agentData.information_sent || 0)
        };
    });
    
    // Calculate communication efficiency
    agents.forEach(agent => {
        const sent = simulationData.agents[agent].messages_sent || 0;
        const received = simulationData.agents[agent].information_received || 0;
        metrics.efficiency[agent] = sent > 0 ? received / sent : 0;
    });
    
    // Calculate centrality metrics
    agents.forEach(agent => {
        // Degree centrality: number of unique agents communicated with
        const connections = new Set();
        Object.entries(commMatrix[agent] || {}).forEach(([to, count]) => {
            if (count > 0) connections.add(to);
        });
        Object.entries(commMatrix).forEach(([from, toAgents]) => {
            if (from !== agent && toAgents[agent] > 0) connections.add(from);
        });
        metrics.centrality.degree[agent] = connections.size;
        
        // Simplified betweenness: how often agent appears in communication chains
        metrics.centrality.betweenness[agent] = 0;
        
        // Information brokerage: unique info pieces shared
        const uniqueShared = new Set();
        infoFlows.forEach(flow => {
            if (flow.from === agent) {
                flow.information.forEach(info => uniqueShared.add(info));
            }
        });
        metrics.centrality.infoBrokerage[agent] = uniqueShared.size;
    });
    
    // Calculate network evolution (simplified for now)
    const roundData = simulationData.rounds || {};
    Object.keys(roundData).forEach(round => {
        const roundNum = parseInt(round);
        const roundEvents = roundData[round];
        
        let messageCount = 0;
        let activeConnections = new Set();
        
        roundEvents.forEach(event => {
            if (event.event_type === 'message' && event.data.from !== 'system') {
                messageCount++;
                activeConnections.add(`${event.data.from}-${event.data.to}`);
            }
        });
        
        metrics.evolution.rounds.push(roundNum);
        metrics.evolution.messageVolume.push(messageCount);
        metrics.evolution.activeConnections.push(activeConnections.size);
        metrics.evolution.networkDensity.push(activeConnections.size / (agents.length * (agents.length - 1)));
    });
    
    return metrics;
}

// Display communication volume heatmap
function displayCommunicationHeatmap(commMatrix) {
    const canvas = document.getElementById('communicationHeatmap');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const agents = Object.keys(simulationData.agents).sort();
    
    // Create heatmap data
    const data = [];
    const labels = [];
    
    agents.forEach((fromAgent, i) => {
        agents.forEach((toAgent, j) => {
            if (fromAgent !== toAgent) {
                const value = commMatrix[fromAgent]?.[toAgent] || 0;
                data.push({
                    x: j,
                    y: i,
                    v: value
                });
            }
        });
        labels.push(fromAgent.replace('agent_', 'A'));
    });
    
    // Create Chart.js heatmap using scatter plot with color coding
    new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Messages',
                data: data,
                backgroundColor: function(context) {
                    const value = context.parsed.v || 0;
                    const max = Math.max(...data.map(d => d.v));
                    const intensity = value / max;
                    return `rgba(13, 110, 253, ${intensity})`;
                },
                pointRadius: 15
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                x: {
                    type: 'linear',
                    position: 'bottom',
                    ticks: {
                        callback: function(value) {
                            return labels[value] || '';
                        }
                    },
                    title: {
                        display: true,
                        text: 'To Agent'
                    }
                },
                y: {
                    type: 'linear',
                    ticks: {
                        callback: function(value) {
                            return labels[value] || '';
                        }
                    },
                    title: {
                        display: true,
                        text: 'From Agent'
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const from = labels[context.parsed.y];
                            const to = labels[context.parsed.x];
                            return `${from} → ${to}: ${context.parsed.v} messages`;
                        }
                    }
                }
            }
        }
    });
}

// Display response rate heatmap
function displayResponseRateHeatmap(responseMatrix) {
    const canvas = document.getElementById('responseRateHeatmap');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const agents = Object.keys(simulationData.agents).sort();
    
    // Create heatmap data
    const data = [];
    const labels = [];
    
    agents.forEach((requester, i) => {
        agents.forEach((responder, j) => {
            if (requester !== responder) {
                const value = responseMatrix[requester]?.[responder] || 0;
                data.push({
                    x: j,
                    y: i,
                    v: value
                });
            }
        });
        labels.push(requester.replace('agent_', 'A'));
    });
    
    // Create heatmap
    new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Response Rate %',
                data: data,
                backgroundColor: function(context) {
                    const value = context.parsed.v || 0;
                    // Color scale: red (0%) to yellow (50%) to green (100%)
                    if (value < 50) {
                        const intensity = value / 50;
                        return `rgba(255, ${Math.floor(255 * intensity)}, 0, 0.8)`;
                    } else {
                        const intensity = (value - 50) / 50;
                        return `rgba(${Math.floor(255 * (1 - intensity))}, 255, 0, 0.8)`;
                    }
                },
                pointRadius: 15
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                x: {
                    type: 'linear',
                    position: 'bottom',
                    ticks: {
                        callback: function(value) {
                            return labels[value] || '';
                        }
                    },
                    title: {
                        display: true,
                        text: 'Responder'
                    }
                },
                y: {
                    type: 'linear',
                    ticks: {
                        callback: function(value) {
                            return labels[value] || '';
                        }
                    },
                    title: {
                        display: true,
                        text: 'Requester'
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const requester = labels[context.parsed.y];
                            const responder = labels[context.parsed.x];
                            return `${requester} → ${responder}: ${context.parsed.v.toFixed(0)}% response rate`;
                        }
                    }
                }
            }
        }
    });
}

// Display information flow balance
function displayInfoFlowBalance(infoBalance) {
    const canvas = document.getElementById('infoFlowBalance');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const agents = Object.keys(infoBalance).sort();
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: agents.map(a => a.replace('agent_', 'Agent ')),
            datasets: [
                {
                    label: 'Information Shared',
                    data: agents.map(a => -infoBalance[a].shared),
                    backgroundColor: 'rgba(220, 53, 69, 0.8)',
                    stack: 'Stack 0'
                },
                {
                    label: 'Information Received',
                    data: agents.map(a => infoBalance[a].received),
                    backgroundColor: 'rgba(40, 167, 69, 0.8)',
                    stack: 'Stack 0'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Information Flow Balance by Agent'
                },
                tooltip: {
                    callbacks: {
                        afterLabel: function(context) {
                            const agent = agents[context.dataIndex];
                            const net = infoBalance[agent].netFlow;
                            return `Net flow: ${net > 0 ? '+' : ''}${net}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    stacked: true,
                    title: {
                        display: true,
                        text: 'Information Pieces'
                    }
                }
            }
        }
    });
}

// Display communication efficiency
function displayCommunicationEfficiency(efficiency) {
    const canvas = document.getElementById('commEfficiencyChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const agents = Object.keys(efficiency).sort();
    
    // Create scatter plot data
    const data = agents.map(agent => ({
        x: simulationData.agents[agent].messages_sent || 0,
        y: simulationData.agents[agent].information_received || 0,
        agent: agent
    }));
    
    new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Communication Efficiency',
                data: data,
                backgroundColor: agents.map(a => agentColors[a] + '80'),
                borderColor: agents.map(a => agentColors[a]),
                borderWidth: 2,
                pointRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Messages Sent vs Information Received'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const agent = data[context.dataIndex].agent;
                            const eff = efficiency[agent];
                            return [
                                `${agent}`,
                                `Messages sent: ${context.parsed.x}`,
                                `Info received: ${context.parsed.y}`,
                                `Efficiency: ${eff.toFixed(2)} info/msg`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Messages Sent'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Information Pieces Received'
                    }
                }
            }
        }
    });
}

// Display centrality metrics
function displayCentralityMetrics(centrality) {
    // Degree centrality
    const degreeCanvas = document.getElementById('degreeCentrality');
    if (degreeCanvas) {
        const agents = Object.keys(centrality.degree).sort((a, b) => 
            centrality.degree[b] - centrality.degree[a]
        );
        
        new Chart(degreeCanvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: agents.map(a => a.replace('agent_', 'A')),
                datasets: [{
                    label: 'Unique Connections',
                    data: agents.map(a => centrality.degree[a]),
                    backgroundColor: 'rgba(13, 110, 253, 0.8)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Connections'
                        }
                    }
                }
            }
        });
    }
    
    // Information brokerage
    const brokerCanvas = document.getElementById('infoBrokerage');
    if (brokerCanvas) {
        const agents = Object.keys(centrality.infoBrokerage).sort((a, b) => 
            centrality.infoBrokerage[b] - centrality.infoBrokerage[a]
        );
        
        new Chart(brokerCanvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: agents.map(a => a.replace('agent_', 'A')),
                datasets: [{
                    label: 'Unique Info Shared',
                    data: agents.map(a => centrality.infoBrokerage[a]),
                    backgroundColor: 'rgba(40, 167, 69, 0.8)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Unique Pieces'
                        }
                    }
                }
            }
        });
    }
    
    // Placeholder for betweenness centrality
    const betweennessCanvas = document.getElementById('betweennessCentrality');
    if (betweennessCanvas) {
        const ctx = betweennessCanvas.getContext('2d');
        ctx.fillStyle = '#666';
        ctx.font = '14px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('Betweenness calculation pending', betweennessCanvas.width/2, betweennessCanvas.height/2);
    }
}

// Display network evolution
function displayNetworkEvolution(evolution) {
    const canvas = document.getElementById('networkEvolution');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: evolution.rounds,
            datasets: [
                {
                    label: 'Message Volume',
                    data: evolution.messageVolume,
                    borderColor: 'rgba(13, 110, 253, 1)',
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    yAxisID: 'y'
                },
                {
                    label: 'Active Connections',
                    data: evolution.activeConnections,
                    borderColor: 'rgba(220, 53, 69, 1)',
                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                    yAxisID: 'y'
                },
                {
                    label: 'Network Density',
                    data: evolution.networkDensity.map(d => d * 100),
                    borderColor: 'rgba(40, 167, 69, 1)',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Network Activity Over Time'
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Round'
                    }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Count'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Network Density %'
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                }
            }
        }
    });
}

// Display network insights
function displayNetworkInsights(metrics) {
    const insightsDiv = document.getElementById('networkInsights');
    if (!insightsDiv) return;
    
    let insights = [];
    
    // Find most connected agents
    const degreeScores = Object.entries(metrics.centrality.degree)
        .sort((a, b) => b[1] - a[1]);
    if (degreeScores.length > 0) {
        insights.push(`<strong>Most Connected:</strong> ${degreeScores[0][0]} with ${degreeScores[0][1]} unique connections`);
    }
    
    // Find information brokers
    const brokerScores = Object.entries(metrics.centrality.infoBrokerage)
        .sort((a, b) => b[1] - a[1]);
    if (brokerScores.length > 0 && brokerScores[0][1] > 0) {
        insights.push(`<strong>Top Information Broker:</strong> ${brokerScores[0][0]} shared ${brokerScores[0][1]} unique pieces`);
    }
    
    // Find most efficient communicator
    const efficiencyScores = Object.entries(metrics.efficiency)
        .sort((a, b) => b[1] - a[1]);
    if (efficiencyScores.length > 0 && efficiencyScores[0][1] > 0) {
        insights.push(`<strong>Most Efficient:</strong> ${efficiencyScores[0][0]} with ${efficiencyScores[0][1].toFixed(2)} info pieces per message`);
    }
    
    // Find information hoarders vs sharers
    const netFlows = Object.entries(metrics.infoBalance)
        .sort((a, b) => b[1].netFlow - a[1].netFlow);
    if (netFlows.length > 0) {
        const topReceiver = netFlows[0];
        const topSharer = netFlows[netFlows.length - 1];
        if (topReceiver[1].netFlow > 0) {
            insights.push(`<strong>Top Net Receiver:</strong> ${topReceiver[0]} (+${topReceiver[1].netFlow} net pieces)`);
        }
        if (topSharer[1].netFlow < 0) {
            insights.push(`<strong>Top Net Contributor:</strong> ${topSharer[0]} (${topSharer[1].netFlow} net pieces)`);
        }
    }
    
    // Network density insight
    if (metrics.evolution.networkDensity.length > 0) {
        const avgDensity = metrics.evolution.networkDensity.reduce((a, b) => a + b) / metrics.evolution.networkDensity.length;
        insights.push(`<strong>Average Network Density:</strong> ${(avgDensity * 100).toFixed(1)}% of possible connections`);
    }
    
    insightsDiv.innerHTML = insights.length > 0 ? 
        '<ul class="mb-0">' + insights.map(i => `<li>${i}</li>`).join('') + '</ul>' :
        '<p class="mb-0">No significant network patterns detected.</p>';
}

// Helper function to draw arrows
function drawArrow(ctx, fromX, fromY, toX, toY, thickness, color) {
    const headlen = 10;
    const angle = Math.atan2(toY - fromY, toX - fromX);
    
    // Adjust start and end points to not overlap with nodes
    const nodeRadius = 40;
    const startX = fromX + nodeRadius * Math.cos(angle);
    const startY = fromY + nodeRadius * Math.sin(angle);
    const endX = toX - nodeRadius * Math.cos(angle);
    const endY = toY - nodeRadius * Math.sin(angle);
    
    // Draw line
    ctx.beginPath();
    ctx.moveTo(startX, startY);
    ctx.lineTo(endX, endY);
    ctx.strokeStyle = color;
    ctx.lineWidth = thickness;
    ctx.stroke();
    
    // Draw arrowhead
    ctx.beginPath();
    ctx.moveTo(endX, endY);
    ctx.lineTo(endX - headlen * Math.cos(angle - Math.PI / 6), endY - headlen * Math.sin(angle - Math.PI / 6));
    ctx.moveTo(endX, endY);
    ctx.lineTo(endX - headlen * Math.cos(angle + Math.PI / 6), endY - headlen * Math.sin(angle + Math.PI / 6));
    ctx.stroke();
}

// Display enhanced strategic analysis using backend data
function displayEnhancedStrategicAnalysis(strategicData) {
    const analysisContainer = document.getElementById('analysisContent');
    let html = '<div class="container-fluid">';
    
    html += `
        <div class="row mb-4">
            <div class="col-12">
                <h4>Enhanced Strategic Behavior Analysis</h4>
                <p class="text-muted">Advanced analysis using multi-level keyword detection and behavioral patterns</p>
            </div>
        </div>
    `;
    
    // Display agent strategy cards with enhanced metrics
    html += '<div class="row">';
    
    Object.entries(strategicData).forEach(([agentId, data]) => {
        const agentNum = agentId.split('_')[1];
        const dominantStrategy = getEnhancedDominantStrategy(data);
        
        html += `
            <div class="col-md-6 mb-4">
                <div class="card">
                    <div class="card-header">
                        <h5><span class="agent-badge agent-${agentNum}">${agentId}</span> Enhanced Profile</h5>
                    </div>
                    <div class="card-body">
                        <h6>Dominant Strategy: <span class="badge bg-${dominantStrategy.color}">${dominantStrategy.name}</span></h6>
                        <div class="progress mb-3">
                            <div class="progress-bar bg-${dominantStrategy.color}" style="width: ${dominantStrategy.confidence}%">
                                ${dominantStrategy.confidence.toFixed(0)}% confidence
                            </div>
                        </div>
                        
                        <div class="mt-3">
                            <h6>Strategic Scores:</h6>
                            <ul class="list-unstyled">
                                ${Object.entries(data.strategic_keywords || {}).map(([strategy, score]) => `
                                    <li class="mb-2">
                                        <div class="d-flex justify-content-between align-items-center">
                                            <span>${formatStrategyName(strategy)}:</span>
                                            <div style="width: 100px;">
                                                <div class="progress" style="height: 10px;">
                                                    <div class="progress-bar ${getStrategyColor(strategy)}" 
                                                         style="width: ${Math.min(score * 10, 100)}%"></div>
                                                </div>
                                            </div>
                                        </div>
                                    </li>
                                `).join('')}
                            </ul>
                        </div>
                        
                        <div class="mt-3">
                            <h6>Behavioral Patterns:</h6>
                            <div class="row">
                                <div class="col-6">
                                    <small class="text-muted">Urgency: ${data.behavioral_patterns?.urgency || 0}</small>
                                </div>
                                <div class="col-6">
                                    <small class="text-muted">Patience: ${data.behavioral_patterns?.patience || 0}</small>
                                </div>
                                <div class="col-6">
                                    <small class="text-muted">Persistence: ${data.behavioral_patterns?.persistence || 0}</small>
                                </div>
                                <div class="col-6">
                                    <small class="text-muted">Politeness: ${data.trust_indicators?.politeness || 0}</small>
                                </div>
                            </div>
                        </div>
                        
                        <div class="mt-3">
                            <h6>Communication Metrics:</h6>
                            <small class="text-muted">
                                Response Rate: ${(data.response_rate * 100).toFixed(1)}% | 
                                Efficiency: ${(data.communication_efficiency * 100).toFixed(1)}%
                            </small>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div></div>';
    analysisContainer.innerHTML = html;
}

// Get enhanced dominant strategy with confidence
function getEnhancedDominantStrategy(agentData) {
    const strategies = agentData.strategic_keywords || {};
    let maxStrategy = { name: 'Balanced', score: 0, color: 'secondary' };
    
    const strategyMeta = {
        cooperation: { name: 'Cooperative', color: 'success' },
        competition: { name: 'Competitive', color: 'warning' },
        hoarding: { name: 'Information Hoarder', color: 'info' },
        reciprocity: { name: 'Reciprocal', color: 'primary' },
        deception: { name: 'Deceptive', color: 'danger' },
        strategic_thinking: { name: 'Strategic Thinker', color: 'purple' }
    };
    
    Object.entries(strategies).forEach(([strategy, score]) => {
        if (score > maxStrategy.score) {
            maxStrategy = {
                name: strategyMeta[strategy]?.name || strategy,
                score: score,
                color: strategyMeta[strategy]?.color || 'secondary'
            };
        }
    });
    
    // Calculate confidence based on how much the dominant strategy stands out
    const totalScore = Object.values(strategies).reduce((sum, s) => sum + s, 0);
    const confidence = totalScore > 0 ? (maxStrategy.score / totalScore) * 100 : 0;
    
    return {
        name: maxStrategy.name,
        color: maxStrategy.color,
        confidence: confidence
    };
}

// Format strategy name for display
function formatStrategyName(strategy) {
    return strategy.split('_').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
}

// Get strategy color
function getStrategyColor(strategy) {
    const colors = {
        cooperation: 'bg-success',
        competition: 'bg-warning',
        hoarding: 'bg-info',
        reciprocity: 'bg-primary',
        deception: 'bg-danger',
        strategic_thinking: 'bg-secondary'
    };
    return colors[strategy] || 'bg-secondary';
}

// Display communication effectiveness analysis
function displayCommunicationEffectiveness() {
    if (!simulationData.communication_correlation) return;
    
    const effectivenessDiv = document.getElementById('communicationEffectiveness');
    let html = '<div class="row">';
    
    Object.entries(simulationData.communication_correlation).forEach(([agentId, data]) => {
        const agentNum = agentId.split('_')[1];
        
        html += `
            <div class="col-md-6 mb-4">
                <div class="card">
                    <div class="card-header">
                        <h6><span class="agent-badge agent-${agentNum}">${agentId}</span> Communication Analysis</h6>
                    </div>
                    <div class="card-body">
        `;
        
        // Show ignored by list
        if (data.ignored_by && data.ignored_by.length > 0) {
            html += `
                <div class="alert alert-warning small">
                    <strong>Being ignored by:</strong> ${data.ignored_by.map(a => 
                        `<span class="agent-badge agent-${a.split('_')[1]}">${a}</span>`
                    ).join(', ')}
                    <br><small>Sent multiple messages but received no information</small>
                </div>
            `;
        }
        
        // Show communication effectiveness
        html += '<h6 class="mt-3">Communication Effectiveness:</h6>';
        html += '<div class="small">';
        
        Object.entries(data.communication_effectiveness || {}).forEach(([targetAgent, effectiveness]) => {
            const targetNum = targetAgent.split('_')[1];
            const badgeColor = effectiveness.effectiveness_score > 0.5 ? 'success' : 
                               effectiveness.effectiveness_score > 0 ? 'warning' : 'danger';
            
            html += `
                <div class="mb-2">
                    <span class="agent-badge agent-${targetNum}">${targetAgent}</span>
                    <span class="badge bg-${badgeColor} ms-2">${effectiveness.interpretation}</span>
                    <br>
                    <small class="text-muted">
                        ${effectiveness.messages_sent} messages → ${effectiveness.info_received} info pieces
                        (${(effectiveness.effectiveness_score * 100).toFixed(0)}% effective)
                    </small>
                </div>
            `;
        });
        
        html += '</div>';
        
        // Messages required per info
        if (Object.keys(data.messages_required_per_info || {}).length > 0) {
            html += '<h6 class="mt-3">Average Messages per Info Piece:</h6>';
            html += '<ul class="list-unstyled small">';
            
            Object.entries(data.messages_required_per_info).forEach(([agent, ratio]) => {
                const num = agent.split('_')[1];
                html += `
                    <li>
                        <span class="agent-badge agent-${num}">${agent}</span>: 
                        ${ratio.toFixed(1)} messages/info
                    </li>
                `;
            });
            
            html += '</ul>';
        }
        
        html += '</div></div></div>';
    });
    
    html += '</div>';
    effectivenessDiv.innerHTML = html;
}

// Initialize strategic reports
function initializeStrategicReports() {
    const reportSelect = document.getElementById('reportAgentSelect');
    
    // Populate agent selector
    reportSelect.innerHTML = '<option value="">Select an agent...</option>';
    Object.keys(simulationData.strategic_reports).forEach(agentId => {
        const option = document.createElement('option');
        option.value = agentId;
        option.textContent = agentId;
        reportSelect.appendChild(option);
    });
    
    // Set up event listener
    reportSelect.addEventListener('change', function(e) {
        if (e.target.value) {
            displayAgentStrategicReports(e.target.value);
        } else {
            document.getElementById('strategicReportsContent').innerHTML = 
                '<p class="text-muted">Select an agent to view their strategic reports throughout the simulation.</p>';
        }
    });
}

// Display strategic reports for selected agent
function displayAgentStrategicReports(agentId) {
    const reports = simulationData.strategic_reports[agentId];
    const agentData = simulationData.agents[agentId];
    const agentNum = agentId.split('_')[1];
    
    // Update agent info
    const infoDiv = document.getElementById('reportAgentInfo');
    infoDiv.innerHTML = `
        <div class="card">
            <div class="card-body">
                <h6><span class="agent-badge agent-${agentNum}">${agentId}</span></h6>
                <p class="mb-1"><strong>Final Score:</strong> ${agentData.score}</p>
                <p class="mb-1"><strong>Tasks Completed:</strong> ${agentData.tasks_completed}</p>
                <p class="mb-0"><strong>Messages Sent:</strong> ${agentData.messages_sent}</p>
            </div>
        </div>
    `;
    
    // Display reports
    const contentDiv = document.getElementById('strategicReportsContent');
    let html = '<div class="accordion" id="reportsAccordion">';
    
    reports.forEach((report, index) => {
        const collapseId = `collapse_${agentId}_${index}`;
        const isFirst = index === 0;
        
        html += `
            <div class="accordion-item">
                <h2 class="accordion-header">
                    <button class="accordion-button ${!isFirst ? 'collapsed' : ''}" type="button" 
                            data-bs-toggle="collapse" data-bs-target="#${collapseId}">
                        Round ${report.round} Strategic Report
                        <small class="ms-auto me-2 text-muted">${new Date(report.timestamp).toLocaleTimeString()}</small>
                    </button>
                </h2>
                <div id="${collapseId}" class="accordion-collapse collapse ${isFirst ? 'show' : ''}" 
                     data-bs-parent="#reportsAccordion">
                    <div class="accordion-body">
        `;
        
        const strategicReport = report.strategic_report;
        
        // Check if new format with confidential_assessment
        if (strategicReport.confidential_assessment) {
            html += `
                <h6>Confidential Strategic Assessment</h6>
                <div class="strategic-narrative">
                    ${strategicReport.confidential_assessment.split('\n\n').map(paragraph => 
                        `<p class="small">${paragraph}</p>`
                    ).join('')}
                </div>
            `;
        } else {
            // Legacy format support
            html += `
                <h6>Environmental Analysis</h6>
                <p class="small">${strategicReport.environmental_analysis || 'No analysis available'}</p>
                
                <h6>Interaction Dynamics</h6>
                <p class="small">${strategicReport.interaction_dynamics || 'No analysis available'}</p>
                
                <h6>Strategic Observations</h6>
                <p class="small">${strategicReport.strategic_observations || 'No analysis available'}</p>
                
                <h6>Predictions</h6>
                <p class="small">${strategicReport.predictions || 'No predictions available'}</p>
            `;
        }
        
        // Cooperation Scores
        if (report.cooperation_scores) {
            html += '<h6 class="mt-3">Cooperation Scores Given</h6>';
            html += '<div class="row">';
            
            Object.entries(report.cooperation_scores).forEach(([targetAgent, score]) => {
                if (targetAgent !== 'self') {
                    const targetNum = targetAgent.split('_')[1];
                    html += `
                        <div class="col-6 mb-2">
                            <span class="agent-badge agent-${targetNum}">${targetAgent}</span>
                            <span class="badge bg-primary ms-2">${score}/10</span>
                        </div>
                    `;
                }
            });
            
            html += '</div>';
        }
        
        html += '</div></div></div>';
    });
    
    html += '</div>';
    contentDiv.innerHTML = html;
}

// Update quantitative analysis to include communication effectiveness
function displayQuantitativeAnalysis() {
    const perfMetrics = simulationData.performance_metrics;
    const commMetrics = simulationData.communication_metrics;
    
    if (!perfMetrics || !commMetrics) {
        console.error('Metrics data not available');
        return;
    }
    
    // Display overall metrics
    document.getElementById('totalTasks').textContent = perfMetrics.overall.total_tasks_completed;
    document.getElementById('totalPoints').textContent = perfMetrics.overall.total_points_awarded;
    document.getElementById('avgPointsPerTask').textContent = perfMetrics.overall.average_points_per_task.toFixed(1);
    document.getElementById('firstCompletionRate').textContent = (perfMetrics.overall.first_completion_rate * 100).toFixed(1) + '%';
    
    // Display agent performance table
    displayAgentPerformanceTable(perfMetrics.by_agent);
    
    // Display communication charts
    displayCommunicationCharts(commMetrics);
    
    // Display cooperation matrix
    displayCooperationMatrix(commMetrics.info_flow_matrix);
    
    // Display message content analysis
    displayMessageAnalysis();
    
    // Display communication effectiveness
    displayCommunicationEffectiveness();
}

// Display cooperation analysis
function displayCooperationAnalysis() {
    const coopData = simulationData.cooperation_dynamics;
    if (!coopData) return;
    
    // Display insights
    displayCooperationInsights(coopData.insights);
    
    // Display correlation charts
    displayCooperationCorrelations(coopData.correlations);
    
    // Display misperception analysis
    displayMisperceptionAnalysis(coopData.strategic_misperception);
    
    // Display cooperation networks
    displayCooperationNetworks(coopData.cooperation_networks);
    
    // Display reciprocity analysis
    displayReciprocityAnalysis(coopData.reciprocity_analysis);
    
    // Display performance table
    displayCooperationPerformanceTable(coopData.agent_performance, coopData.info_hoarding);
    
    // Display temporal cooperation evolution
    if (simulationData.temporal_cooperation) {
        displayTemporalCooperationEvolution(simulationData.temporal_cooperation);
    }
}

// Display cooperation insights
function displayCooperationInsights(insights) {
    const insightsDiv = document.getElementById('cooperationInsights');
    if (!insights || insights.length === 0) {
        insightsDiv.innerHTML = '<p>No insights available.</p>';
        return;
    }
    
    let html = '<ul class="mb-0">';
    insights.forEach(insight => {
        html += `<li>${insight}</li>`;
    });
    html += '</ul>';
    
    insightsDiv.innerHTML = html;
}

// Display cooperation correlation charts
function displayCooperationCorrelations(correlations) {
    if (!correlations || !correlations.raw_data) return;
    
    // Cooperation vs Performance chart
    const perfData = correlations.raw_data.cooperation_vs_performance;
    if (perfData && perfData.length > 0) {
        const ctx1 = document.getElementById('cooperationPerformanceChart').getContext('2d');
        new Chart(ctx1, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Cooperation Score vs Points',
                    data: perfData.map(d => ({
                        x: d.avg_cooperation_received,
                        y: d.total_points,
                        agent: d.agent
                    })),
                    backgroundColor: 'rgba(75, 192, 192, 0.6)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    pointRadius: 8,
                    pointHoverRadius: 10
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: `Cooperation Perception vs Performance (r = ${correlations.cooperation_received_vs_points.toFixed(2)})`
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.raw.agent}: Coop ${context.parsed.x.toFixed(1)}, Points ${context.parsed.y}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Average Cooperation Score Received'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Total Points'
                        }
                    }
                }
            }
        });
    }
    
    // Perception vs Reality chart
    const realityData = correlations.raw_data.perception_vs_reality;
    if (realityData && realityData.length > 0) {
        const ctx2 = document.getElementById('perceptionRealityChart').getContext('2d');
        new Chart(ctx2, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Perceived vs Actual Cooperation',
                    data: realityData.map(d => ({
                        x: d.avg_perceived_cooperation,
                        y: d.actual_info_shared,
                        agent: d.agent
                    })),
                    backgroundColor: 'rgba(255, 159, 64, 0.6)',
                    borderColor: 'rgba(255, 159, 64, 1)',
                    pointRadius: 8,
                    pointHoverRadius: 10
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Perception vs Reality: How Cooperation Scores Match Actual Behavior'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.raw.agent}: Perceived ${context.parsed.x.toFixed(1)}, Actual ${context.parsed.y} pieces`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Average Perceived Cooperation (by others)'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Actual Information Pieces Shared'
                        }
                    }
                }
            }
        });
    }
}

// Display misperception analysis
function displayMisperceptionAnalysis(misperception) {
    if (!misperception) return;
    
    // False cooperators
    const falseDiv = document.getElementById('falseCooperators');
    if (misperception.false_cooperators && misperception.false_cooperators.length > 0) {
        let html = '<div class="card">';
        html += '<div class="card-header bg-danger text-white"><h6 class="mb-0">False Cooperators</h6></div>';
        html += '<div class="card-body">';
        html += '<p class="small text-muted">Agents perceived as cooperative but actually hoarding information</p>';
        
        misperception.false_cooperators.forEach(agent => {
            const agentNum = agent.agent.split('_')[1];
            html += `
                <div class="mb-2">
                    <span class="agent-badge agent-${agentNum}">${agent.agent}</span>
                    <div class="small">
                        Perceived: ${agent.avg_perceived_cooperation.toFixed(1)}/10 | 
                        Actual sharing: ${(agent.actual_sharing_rate * 100).toFixed(0)}%
                        <div class="progress" style="height: 10px;">
                            <div class="progress-bar bg-danger" style="width: ${agent.severity * 10}%"></div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div></div>';
        falseDiv.innerHTML = html;
    } else {
        falseDiv.innerHTML = '<p class="text-muted">No false cooperators detected.</p>';
    }
    
    // Undervalued cooperators
    const undervaluedDiv = document.getElementById('undervaluedCooperators');
    if (misperception.undervalued_cooperators && misperception.undervalued_cooperators.length > 0) {
        let html = '<div class="card">';
        html += '<div class="card-header bg-success text-white"><h6 class="mb-0">Undervalued Cooperators</h6></div>';
        html += '<div class="card-body">';
        html += '<p class="small text-muted">Agents who share freely but aren\'t recognized</p>';
        
        misperception.undervalued_cooperators.forEach(agent => {
            const agentNum = agent.agent.split('_')[1];
            html += `
                <div class="mb-2">
                    <span class="agent-badge agent-${agentNum}">${agent.agent}</span>
                    <div class="small">
                        Perceived: ${agent.avg_perceived_cooperation.toFixed(1)}/10 | 
                        Actual sharing: ${(agent.actual_sharing_rate * 100).toFixed(0)}%
                        <div class="progress" style="height: 10px;">
                            <div class="progress-bar bg-success" style="width: ${agent.severity * 10}%"></div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div></div>';
        undervaluedDiv.innerHTML = html;
    } else {
        undervaluedDiv.innerHTML = '<p class="text-muted">No undervalued cooperators detected.</p>';
    }
}

// Display cooperation networks
function displayCooperationNetworks(networks) {
    if (!networks) return;
    
    // Network visualization
    const canvas = document.getElementById('cooperationNetworkViz');
    const ctx = canvas.getContext('2d');
    
    // Set canvas size
    canvas.width = 600;
    canvas.height = 400;
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw title
    ctx.fillStyle = '#333';
    ctx.font = '16px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('Cooperation Networks', canvas.width/2, 20);
    
    // Draw cooperative pairs as connections
    if (networks.cooperative_pairs && networks.cooperative_pairs.length > 0) {
        const agents = new Set();
        networks.cooperative_pairs.forEach(pair => {
            agents.add(pair[0]);
            agents.add(pair[1]);
        });
        
        const agentList = Array.from(agents);
        const positions = {};
        
        // Position agents in a circle
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        const radius = Math.min(centerX, centerY) - 60;
        
        agentList.forEach((agent, index) => {
            const angle = (2 * Math.PI / agentList.length) * index;
            positions[agent] = {
                x: centerX + radius * Math.cos(angle),
                y: centerY + radius * Math.sin(angle)
            };
        });
        
        // Draw connections
        ctx.strokeStyle = 'rgba(76, 175, 80, 0.5)';
        ctx.lineWidth = 2;
        
        networks.cooperative_pairs.forEach(pair => {
            const pos1 = positions[pair[0]];
            const pos2 = positions[pair[1]];
            
            ctx.beginPath();
            ctx.moveTo(pos1.x, pos1.y);
            ctx.lineTo(pos2.x, pos2.y);
            ctx.stroke();
        });
        
        // Highlight cliques
        if (networks.cooperation_cliques) {
            ctx.strokeStyle = 'rgba(255, 193, 7, 0.8)';
            ctx.lineWidth = 4;
            
            networks.cooperation_cliques.forEach(clique => {
                // Draw triangle for 3-agent cliques
                if (clique.length === 3) {
                    ctx.beginPath();
                    ctx.moveTo(positions[clique[0]].x, positions[clique[0]].y);
                    ctx.lineTo(positions[clique[1]].x, positions[clique[1]].y);
                    ctx.lineTo(positions[clique[2]].x, positions[clique[2]].y);
                    ctx.closePath();
                    ctx.stroke();
                }
            });
        }
        
        // Draw nodes
        agentList.forEach(agent => {
            const pos = positions[agent];
            const agentNum = agent.split('_')[1];
            const isIsolated = networks.isolated_agents && networks.isolated_agents.includes(agent);
            
            // Node circle
            ctx.beginPath();
            ctx.arc(pos.x, pos.y, 20, 0, 2 * Math.PI);
            ctx.fillStyle = isIsolated ? '#dc3545' : agentColors[agent] || '#6c757d';
            ctx.fill();
            ctx.strokeStyle = '#333';
            ctx.lineWidth = 2;
            ctx.stroke();
            
            // Agent label
            ctx.fillStyle = '#fff';
            ctx.font = 'bold 14px Arial';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(agent, pos.x, pos.y);
        });
        
        // Legend
        ctx.font = '12px Arial';
        ctx.textAlign = 'left';
        ctx.fillStyle = '#333';
        ctx.fillText('Green lines: Mutual cooperation (≥7/10)', 10, canvas.height - 30);
        ctx.fillText('Yellow triangles: Cooperation cliques', 10, canvas.height - 10);
    }
    
    // Network performance stats
    const perfDiv = document.getElementById('networkPerformance');
    let html = '<div class="card">';
    html += '<div class="card-header"><h6 class="mb-0">Network Performance</h6></div>';
    html += '<div class="card-body">';
    
    if (networks.network_performance && Object.keys(networks.network_performance).length > 0) {
        html += '<div class="list-group">';
        
        Object.entries(networks.network_performance)
            .sort((a, b) => b[1].avg_points - a[1].avg_points)
            .forEach(([key, network]) => {
                html += `
                    <div class="list-group-item">
                        <strong>Clique: ${network.members.join(', ')}</strong><br>
                        <small>
                            Total: ${network.total_points} pts | 
                            Avg: ${network.avg_points.toFixed(1)} pts
                        </small>
                    </div>
                `;
            });
        
        html += '</div>';
    } else {
        html += '<p class="text-muted small">No cooperation cliques found.</p>';
    }
    
    if (networks.isolated_agents && networks.isolated_agents.length > 0) {
        html += '<div class="mt-3">';
        html += '<strong>Isolated Agents:</strong><br>';
        html += '<small class="text-danger">' + networks.isolated_agents.join(', ') + '</small>';
        html += '</div>';
    }
    
    html += '</div></div>';
    perfDiv.innerHTML = html;
}

// Display reciprocity analysis
function displayReciprocityAnalysis(reciprocity) {
    if (!reciprocity) return;
    
    const recipDiv = document.getElementById('reciprocityAnalysis');
    let html = '<div class="row">';
    
    // Reciprocal pairs
    html += '<div class="col-md-6">';
    html += '<div class="card">';
    html += '<div class="card-header"><h6 class="mb-0">Reciprocal Cooperation Pairs</h6></div>';
    html += '<div class="card-body">';
    
    if (reciprocity.reciprocal_pairs && reciprocity.reciprocal_pairs.length > 0) {
        html += '<div class="list-group">';
        
        reciprocity.reciprocal_pair_performance.forEach(pairPerf => {
            const pair = pairPerf.pair;
            const pairData = reciprocity.reciprocal_pairs.find(p => 
                p.pair[0] === pair[0] && p.pair[1] === pair[1]
            );
            
            html += `
                <div class="list-group-item">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong>${pair[0]} ↔ ${pair[1]}</strong><br>
                            <small>
                                Scores: ${pairData.scores[0].toFixed(1)} ↔ ${pairData.scores[1].toFixed(1)} | 
                                Actual: ${pairData.actual[0]} ↔ ${pairData.actual[1]} pieces
                            </small>
                        </div>
                        <div class="text-end">
                            <span class="badge bg-primary">${pairPerf.combined_points} pts</span>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
    } else {
        html += '<p class="text-muted">No reciprocal pairs found.</p>';
    }
    
    html += '</div></div></div>';
    
    // Reciprocity metrics
    html += '<div class="col-md-6">';
    html += '<div class="card">';
    html += '<div class="card-header"><h6 class="mb-0">Reciprocity Metrics</h6></div>';
    html += '<div class="card-body">';
    html += `
        <p><strong>Average Reciprocity Score:</strong> ${(reciprocity.avg_reciprocity_score * 100).toFixed(1)}%</p>
        <p><strong>Number of Reciprocal Pairs:</strong> ${reciprocity.reciprocal_pairs ? reciprocity.reciprocal_pairs.length : 0}</p>
    `;
    
    if (reciprocity.reciprocal_pair_performance && reciprocity.reciprocal_pair_performance.length > 0) {
        const totalRecipPoints = reciprocity.reciprocal_pair_performance.reduce((sum, p) => sum + p.combined_points, 0);
        const avgRecipPoints = totalRecipPoints / (reciprocity.reciprocal_pair_performance.length * 2);
        html += `<p><strong>Avg Points for Reciprocal Agents:</strong> ${avgRecipPoints.toFixed(1)}</p>`;
    }
    
    html += '</div></div></div>';
    
    html += '</div>';
    recipDiv.innerHTML = html;
}

// Display cooperation performance table
function displayCooperationPerformanceTable(agentPerformance, infoHoarding) {
    const tbody = document.getElementById('cooperationPerformanceBody');
    tbody.innerHTML = '';
    
    // Sort by rank
    const sortedAgents = Object.entries(agentPerformance)
        .sort((a, b) => a[1].final_rank - b[1].final_rank);
    
    sortedAgents.forEach(([agentId, perf]) => {
        const agentNum = agentId.split('_')[1];
        const hoarding = infoHoarding[agentId] || {};
        
        const row = document.createElement('tr');
        const hoardingRatePercent = (hoarding.hoarding_rate * 100).toFixed(0);
        const hoardingTooltip = `Shared ${perf.info_shared} out of ${hoarding.requests_received || 0} requests (${100 - hoardingRatePercent}% response rate)`;
        
        row.innerHTML = `
            <td><span class="agent-badge agent-${agentNum}">${agentId}</span></td>
            <td>${perf.final_rank}</td>
            <td>${perf.total_points}</td>
            <td>${perf.avg_cooperation_given.toFixed(1)}</td>
            <td>${perf.avg_cooperation_received.toFixed(1)}</td>
            <td>${perf.info_shared}</td>
            <td><span data-bs-toggle="tooltip" title="${hoardingTooltip}">${hoardingRatePercent}%</span></td>
        `;
        
        // Highlight interesting patterns
        if (perf.avg_cooperation_received >= 7 && hoarding.hoarding_rate > 0.5) {
            row.classList.add('table-warning'); // False cooperator
        } else if (perf.avg_cooperation_received < 5 && perf.info_shared > 10) {
            row.classList.add('table-success'); // Undervalued cooperator
        }
        
        tbody.appendChild(row);
    });
    
    // Reinitialize tooltips for dynamically added content
    reinitializeTooltips();
}

// Display temporal cooperation evolution
function displayTemporalCooperationEvolution(temporalData) {
    if (!temporalData) return;
    
    // Display cooperation evolution chart
    displayCooperationEvolutionChart(temporalData.cooperation_by_round);
    
    // Display key events (alliances and betrayals)
    displayCooperationKeyEvents(temporalData);
}

// Display cooperation evolution chart
function displayCooperationEvolutionChart(cooperationByRound) {
    const canvas = document.getElementById('temporalCooperationChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Prepare data for chart
    const rounds = Object.keys(cooperationByRound).sort((a, b) => a - b);
    const datasets = [];
    
    // Calculate average cooperation for each round
    const avgCooperationByRound = rounds.map(round => {
        const scores = Object.values(cooperationByRound[round]);
        if (scores.length === 0) return 0;
        return scores.reduce((sum, score) => sum + score, 0) / scores.length;
    });
    
    // Add average cooperation line
    datasets.push({
        label: 'Average Cooperation',
        data: avgCooperationByRound,
        borderColor: '#0d6efd',
        backgroundColor: 'rgba(13, 110, 253, 0.1)',
        borderWidth: 3,
        fill: true,
        tension: 0.3
    });
    
    // Add volatility indicator (standard deviation)
    const volatilityByRound = rounds.map(round => {
        const scores = Object.values(cooperationByRound[round]);
        if (scores.length === 0) return 0;
        const avg = scores.reduce((sum, score) => sum + score, 0) / scores.length;
        const variance = scores.reduce((sum, score) => sum + Math.pow(score - avg, 2), 0) / scores.length;
        return Math.sqrt(variance);
    });
    
    datasets.push({
        label: 'Cooperation Volatility',
        data: volatilityByRound,
        borderColor: '#dc3545',
        backgroundColor: 'rgba(220, 53, 69, 0.1)',
        borderWidth: 2,
        borderDash: [5, 5],
        fill: false,
        yAxisID: 'y1'
    });
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: rounds,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Cooperation Score Evolution'
                },
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Round'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Average Cooperation Score'
                    },
                    min: 0,
                    max: 10
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Volatility (Std Dev)'
                    },
                    min: 0,
                    grid: {
                        drawOnChartArea: false
                    }
                }
            }
        }
    });
}

// Display cooperation key events
function displayCooperationKeyEvents(temporalData) {
    const eventsDiv = document.getElementById('cooperationEvents');
    if (!eventsDiv) return;
    
    let html = '';
    
    // Display alliance formations
    if (temporalData.alliance_formation && temporalData.alliance_formation.length > 0) {
        html += '<h6 class="text-success">Alliances Formed</h6><ul class="small">';
        temporalData.alliance_formation.forEach(alliance => {
            html += `<li>Round ${alliance.formed_round}: ${alliance.agents[0]} ↔ ${alliance.agents[1]} (strength: ${alliance.strength.toFixed(1)})</li>`;
        });
        html += '</ul>';
    }
    
    // Display betrayals
    if (temporalData.betrayal_events && temporalData.betrayal_events.length > 0) {
        html += '<h6 class="text-danger">Betrayals</h6><ul class="small">';
        temporalData.betrayal_events.forEach(betrayal => {
            html += `<li>Round ${betrayal.round}: ${betrayal.betrayer} → ${betrayal.victim} (drop: ${betrayal.score_drop.toFixed(1)})</li>`;
        });
        html += '</ul>';
    }
    
    // Display cooperation volatility
    if (temporalData.cooperation_volatility) {
        const volatileAgents = Object.entries(temporalData.cooperation_volatility)
            .filter(([agent, vol]) => vol > 2)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 3);
        
        if (volatileAgents.length > 0) {
            html += '<h6 class="text-warning">Most Volatile Agents</h6><ul class="small">';
            volatileAgents.forEach(([agent, volatility]) => {
                html += `<li>${agent}: ${volatility.toFixed(2)} avg change</li>`;
            });
            html += '</ul>';
        }
    }
    
    // Display convergence info
    if (temporalData.convergence_round) {
        html += `<div class="alert alert-info small mt-3">Cooperation patterns stabilized around round ${temporalData.convergence_round}</div>`;
    }
    
    eventsDiv.innerHTML = html || '<p class="text-muted">No significant events detected</p>';
}

// Display information value analysis
function displayInformationValueAnalysis() {
    const infoData = simulationData.information_value;
    if (!infoData) return;
    
    // Display high value information
    displayHighValueInformation(infoData.info_value_map);
    
    // Display timing strategies
    displayTimingStrategies(infoData.timing_strategies);
    
    // Display first mover advantage analysis
    displayFirstMoverAnalysis(infoData.first_mover_advantage);
    
    // Display strategic information management
    displayInfoManagementAnalysis(infoData.high_value_sharing_patterns);
}

// Display high value information pieces
function displayHighValueInformation(infoValueMap) {
    const infoDiv = document.getElementById('highValueInfo');
    const canvas = document.getElementById('infoValueChart');
    if (!infoDiv || !infoValueMap) return;
    
    // Sort info pieces by value
    const sortedInfo = Object.entries(infoValueMap)
        .sort((a, b) => b[1].total_value - a[1].total_value)
        .slice(0, 10); // Top 10
    
    // Display list
    let html = '<div class="list-group">';
    sortedInfo.forEach(([infoPiece, stats]) => {
        const avgValue = stats.avg_value.toFixed(1);
        const usage = stats.usage_count;
        html += `
            <div class="list-group-item">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${infoPiece}</strong>
                        <small class="text-muted d-block">Used ${usage} times</small>
                    </div>
                    <div class="text-end">
                        <span class="badge bg-primary">${avgValue} pts/use</span>
                        <span class="badge bg-success">${stats.total_value} total</span>
                    </div>
                </div>
            </div>
        `;
    });
    html += '</div>';
    infoDiv.innerHTML = html;
    
    // Create value distribution chart
    if (canvas) {
        const ctx = canvas.getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: sortedInfo.map(([info, _]) => info.substring(0, 20) + '...'),
                datasets: [{
                    label: 'Average Points per Use',
                    data: sortedInfo.map(([_, stats]) => stats.avg_value),
                    backgroundColor: 'rgba(13, 110, 253, 0.8)',
                    borderColor: '#0d6efd',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Information Value Distribution'
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            maxRotation: 45,
                            minRotation: 45
                        }
                    },
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Average Points'
                        }
                    }
                }
            }
        });
    }
}

// Display timing strategies
function displayTimingStrategies(timingStrategies) {
    const canvas = document.getElementById('timingStrategyChart');
    if (!canvas || !timingStrategies) return;
    
    const ctx = canvas.getContext('2d');
    
    // Prepare data for stacked bar chart
    const agents = Object.keys(timingStrategies).sort();
    const earlyData = agents.map(agent => timingStrategies[agent].early_shares);
    const midData = agents.map(agent => timingStrategies[agent].mid_shares);
    const lateData = agents.map(agent => timingStrategies[agent].late_shares);
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: agents,
            datasets: [
                {
                    label: 'Early Game (Rounds 1-5)',
                    data: earlyData,
                    backgroundColor: '#28a745',
                    stack: 'Stack 0'
                },
                {
                    label: 'Mid Game (Rounds 6-15)',
                    data: midData,
                    backgroundColor: '#ffc107',
                    stack: 'Stack 0'
                },
                {
                    label: 'Late Game (Rounds 16-20)',
                    data: lateData,
                    backgroundColor: '#dc3545',
                    stack: 'Stack 0'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Information Sharing Timing by Agent'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                x: {
                    stacked: true,
                    title: {
                        display: true,
                        text: 'Agent'
                    }
                },
                y: {
                    stacked: true,
                    title: {
                        display: true,
                        text: 'Information Pieces Shared'
                    }
                }
            }
        }
    });
}

// Display first mover advantage analysis
function displayFirstMoverAnalysis(firstMoverData) {
    const analysisDiv = document.getElementById('firstMoverAnalysis');
    if (!analysisDiv || !firstMoverData) return;
    
    // Sort agents by early task points
    const sortedAgents = Object.entries(firstMoverData)
        .sort((a, b) => b[1].early_task_points - a[1].early_task_points);
    
    let html = '<div class="small">';
    
    // Identify agents with significant first mover advantage
    const firstMovers = sortedAgents.filter(([agent, data]) => 
        data.early_task_points > data.late_task_points * 1.5
    );
    
    if (firstMovers.length > 0) {
        html += '<h6 class="text-success">First Mover Advantage</h6><ul>';
        firstMovers.slice(0, 3).forEach(([agent, data]) => {
            const advantage = ((data.early_task_points / (data.late_task_points || 1)) * 100 - 100).toFixed(0);
            html += `<li>${agent}: +${advantage}% early game benefit</li>`;
        });
        html += '</ul>';
    }
    
    // Identify late bloomers
    const lateBoomers = sortedAgents.filter(([agent, data]) => 
        data.late_task_points > data.early_task_points * 1.5
    );
    
    if (lateBoomers.length > 0) {
        html += '<h6 class="text-primary">Late Game Specialists</h6><ul>';
        lateBoomers.slice(0, 3).forEach(([agent, data]) => {
            html += `<li>${agent}: ${data.late_task_points} late points</li>`;
        });
        html += '</ul>';
    }
    
    html += '</div>';
    analysisDiv.innerHTML = html;
}

// Display strategic information management analysis
function displayInfoManagementAnalysis(sharingPatterns) {
    const analysisDiv = document.getElementById('infoManagementAnalysis');
    if (!analysisDiv) return;
    
    // This would analyze how agents strategically share or withhold high-value information
    // For now, create a placeholder visualization
    let html = '<div class="row">';
    
    html += `
        <div class="col-md-12">
            <div class="alert alert-info">
                <h6>Strategic Information Management Patterns</h6>
                <p>Analysis of how agents balance sharing high-value information with competitive advantage:</p>
                <ul>
                    <li><strong>Selective Sharers:</strong> Share low-value info freely but hoard high-value pieces</li>
                    <li><strong>Reciprocal Traders:</strong> Share high-value info only with trusted partners</li>
                    <li><strong>Information Brokers:</strong> Leverage position to control information flow</li>
                    <li><strong>Free Sharers:</strong> Share all information regardless of value</li>
                </ul>
            </div>
        </div>
    `;
    
    html += '</div>';
    analysisDiv.innerHTML = html;
}