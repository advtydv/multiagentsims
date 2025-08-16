// Simplified Batch Dashboard JavaScript

// Global variables
let currentBatch = null;
let batchData = null;
let agentColors = {};

// Color generation for agents
function generateAgentColors(numAgents) {
    const baseColors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#F7B731', '#5F27CD',
        '#00D2D3', '#FF9FF3', '#54A0FF', '#48DBFB', '#FD79A8'
    ];
    
    agentColors = {};
    for (let i = 1; i <= numAgents; i++) {
        const agentId = `agent_${i}`;
        if (i <= baseColors.length) {
            agentColors[agentId] = baseColors[i - 1];
        } else {
            const hue = ((i - 1) * 360 / numAgents) % 360;
            agentColors[agentId] = `hsl(${hue}, 70%, 60%)`;
        }
    }
    
    return agentColors;
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    loadBatches();
    
    // Set up batch selector
    document.getElementById('batchSelect').addEventListener('change', function(e) {
        if (e.target.value) {
            loadBatch(e.target.value);
        }
    });
});

// Load available batches
async function loadBatches() {
    try {
        const response = await fetch('/api/batches');
        const batches = await response.json();
        
        const select = document.getElementById('batchSelect');
        select.innerHTML = '<option value="">Select a batch simulation...</option>';
        
        batches.forEach(batch => {
            const option = document.createElement('option');
            option.value = batch.id;
            option.textContent = `${batch.id} (${batch.num_simulations} simulations)`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Failed to load batches:', error);
    }
}

// Load specific batch
async function loadBatch(batchId) {
    try {
        // Show loading indicator
        showLoading(true);
        
        // Fetch batch data
        const response = await fetch(`/api/batch/${batchId}/real`);
        
        if (!response.ok) {
            console.error('Failed to fetch batch data:', response.status);
            alert('Failed to load batch data. Check console for details.');
            showLoading(false);
            return;
        }
        
        batchData = await response.json();
        console.log('Loaded batch data:', batchData);
        
        currentBatch = batchId;
        
        // Generate colors for agents
        generateAgentColors(batchData.config.simulation.agents);
        
        // Update UI
        updateBatchInfo();
        
        // Load each tab's content
        loadOverview();
        loadAgentAnalysis();
        loadConsistencyAnalysis();
        loadRoundProgression();
        
        // Show main content
        document.getElementById('mainContent').classList.remove('d-none');
        document.getElementById('batchInfo').classList.remove('d-none');
        
        // Hide loading
        showLoading(false);
    } catch (error) {
        console.error('Failed to load batch:', error);
        showLoading(false);
    }
}

// Update batch information display
function updateBatchInfo() {
    document.getElementById('batchId').textContent = currentBatch;
    document.getElementById('numSimulations').textContent = batchData.num_simulations;
    document.getElementById('agentsPerSim').textContent = batchData.config.simulation.agents;
    document.getElementById('roundsPerSim').textContent = batchData.config.simulation.rounds;
}

// Overview Tab
function loadOverview() {
    // Update metric cards
    const taskStats = batchData.task_statistics;
    document.getElementById('avgTasksCompleted').textContent = taskStats.mean.toFixed(1);
    document.getElementById('taskRange').textContent = `${taskStats.min} - ${taskStats.max}`;
    
    const perfMetrics = batchData.performance_metrics;
    document.getElementById('avgScorePerAgent').textContent = perfMetrics.overall_mean_score.toFixed(1);
    document.getElementById('scoreSpread').textContent = `±${perfMetrics.overall_score_spread.toFixed(1)}`;
    
    document.getElementById('mostConsistent').textContent = perfMetrics.most_consistent_agent || '-';
    document.getElementById('topPerformer').textContent = perfMetrics.highest_avg_score || '-';
    
    // Create winner distribution chart
    createWinnerDistributionChart();
    
    // Create task variance chart
    createTaskVarianceChart();
}

// Agent Analysis Tab
function loadAgentAnalysis() {
    createAgentComparisonChart();
    fillAgentStatsTable();
}

// Consistency Tab
function loadConsistencyAnalysis() {
    createConsistencyChart();
    createScoreRangeChart();
    generateConsistencyInsights();
}

// Round Progression Tab
function loadRoundProgression() {
    createRoundProgressionChart();
    createTasksByRoundChart();
    generateRoundInsights();
}

// Chart creation functions
function createWinnerDistributionChart() {
    const ctx = document.getElementById('winnerDistributionChart').getContext('2d');
    
    const winnerDist = batchData.winner_distribution || {};
    const labels = Object.keys(winnerDist);
    const data = Object.values(winnerDist);
    
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: labels.map(agent => agentColors[agent] || '#999')
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Simulation Winners'
                },
                legend: {
                    position: 'right'
                }
            }
        }
    });
}

function createTaskVarianceChart() {
    const ctx = document.getElementById('taskVarianceChart').getContext('2d');
    
    const taskStats = batchData.task_statistics;
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Tasks Completed'],
            datasets: [{
                label: 'Mean',
                data: [taskStats.mean],
                backgroundColor: 'rgba(54, 162, 235, 0.5)',
                borderColor: 'rgb(54, 162, 235)',
                borderWidth: 1
            }, {
                label: 'Std Dev',
                data: [taskStats.std],
                backgroundColor: 'rgba(255, 99, 132, 0.5)',
                borderColor: 'rgb(255, 99, 132)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Task Completion Statistics'
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function createAgentComparisonChart() {
    const ctx = document.getElementById('agentComparisonChart').getContext('2d');
    
    const agents = Object.keys(batchData.agent_stats);
    const meanScores = agents.map(a => batchData.agent_stats[a].mean_score);
    const stdScores = agents.map(a => batchData.agent_stats[a].std_score);
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: agents,
            datasets: [{
                label: 'Mean Score',
                data: meanScores,
                backgroundColor: agents.map(a => agentColors[a]),
                borderColor: agents.map(a => agentColors[a]),
                borderWidth: 1,
                yAxisID: 'y'
            }, {
                type: 'line',
                label: 'Std Dev',
                data: stdScores,
                borderColor: 'rgba(255, 99, 132, 1)',
                backgroundColor: 'rgba(255, 99, 132, 0.1)',
                borderWidth: 2,
                fill: false,
                yAxisID: 'y1'
            }]
        },
        options: {
            responsive: true,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Agent Performance Across Simulations'
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Mean Score'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Standard Deviation'
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                }
            }
        }
    });
}

function fillAgentStatsTable() {
    const tbody = document.getElementById('agentStatsBody');
    tbody.innerHTML = '';
    
    const winnerDist = batchData.winner_distribution || {};
    
    Object.entries(batchData.agent_stats).forEach(([agent, stats]) => {
        const row = tbody.insertRow();
        row.innerHTML = `
            <td style="color: ${agentColors[agent]}">${agent}</td>
            <td>${stats.mean_score.toFixed(2)}</td>
            <td>${stats.std_score.toFixed(2)}</td>
            <td>${stats.min_score}</td>
            <td>${stats.max_score}</td>
            <td>${stats.mean_rank.toFixed(1)}</td>
            <td>${stats.best_rank}</td>
            <td>${winnerDist[agent] || 0}</td>
        `;
    });
}

function createConsistencyChart() {
    const ctx = document.getElementById('consistencyChart').getContext('2d');
    
    const agents = Object.keys(batchData.agent_stats);
    const consistencies = agents.map(a => batchData.agent_stats[a].consistency * 100);
    
    new Chart(ctx, {
        type: 'horizontalBar',
        data: {
            labels: agents,
            datasets: [{
                label: 'Consistency Score (%)',
                data: consistencies,
                backgroundColor: agents.map(a => {
                    const c = batchData.agent_stats[a].consistency;
                    if (c > 0.8) return 'rgba(75, 192, 192, 0.6)';
                    if (c > 0.6) return 'rgba(255, 205, 86, 0.6)';
                    return 'rgba(255, 99, 132, 0.6)';
                }),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Agent Consistency Scores'
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Consistency %'
                    }
                }
            }
        }
    });
}

function createScoreRangeChart() {
    const ctx = document.getElementById('scoreRangeChart').getContext('2d');
    
    const agents = Object.keys(batchData.agent_stats);
    const data = agents.map(agent => {
        const stats = batchData.agent_stats[agent];
        return {
            x: agent,
            y: [stats.min_score, stats.max_score]
        };
    });
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: agents,
            datasets: [{
                label: 'Score Range',
                data: agents.map(a => {
                    const stats = batchData.agent_stats[a];
                    return stats.max_score - stats.min_score;
                }),
                backgroundColor: agents.map(a => agentColors[a] + '80'),
                borderColor: agents.map(a => agentColors[a]),
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Agent Score Ranges'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const agent = agents[context.dataIndex];
                            const stats = batchData.agent_stats[agent];
                            return `Range: ${stats.min_score} - ${stats.max_score}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Score Range'
                    }
                }
            }
        }
    });
}

function createRoundProgressionChart() {
    const ctx = document.getElementById('roundProgressionChart').getContext('2d');
    
    const roundAvgs = batchData.round_averages || {};
    const rounds = Object.keys(roundAvgs).sort((a, b) => parseInt(a) - parseInt(b));
    const avgScores = rounds.map(r => roundAvgs[r].mean_score);
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: rounds.map(r => `Round ${r}`),
            datasets: [{
                label: 'Average Score',
                data: avgScores,
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.1)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Average Score Progression by Round'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Average Score'
                    }
                }
            }
        }
    });
}

function createTasksByRoundChart() {
    const ctx = document.getElementById('tasksByRoundChart').getContext('2d');
    
    const roundAvgs = batchData.round_averages || {};
    const rounds = Object.keys(roundAvgs).sort((a, b) => parseInt(a) - parseInt(b));
    const completions = rounds.map(r => roundAvgs[r].total_completions / batchData.num_simulations);
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: rounds.map(r => `R${r}`),
            datasets: [{
                label: 'Avg Completions',
                data: completions,
                backgroundColor: 'rgba(54, 162, 235, 0.5)',
                borderColor: 'rgb(54, 162, 235)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Task Completions per Round'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Completions'
                    }
                }
            }
        }
    });
}

function generateConsistencyInsights() {
    const insights = [];
    const perfMetrics = batchData.performance_metrics;
    
    insights.push(`<strong>Most Consistent:</strong> ${perfMetrics.most_consistent_agent || 'N/A'}`);
    insights.push(`<strong>Least Consistent:</strong> ${perfMetrics.least_consistent_agent || 'N/A'}`);
    insights.push(`<strong>Avg Consistency:</strong> ${(perfMetrics.avg_consistency * 100).toFixed(1)}%`);
    
    // Find high variance agents
    const highVariance = Object.entries(batchData.agent_stats)
        .filter(([_, stats]) => stats.consistency < 0.6)
        .map(([agent, _]) => agent);
    
    if (highVariance.length > 0) {
        insights.push(`<strong>High Variance:</strong> ${highVariance.join(', ')}`);
    }
    
    document.getElementById('consistencyInsights').innerHTML = 
        '<ul class="list-unstyled">' + 
        insights.map(i => `<li>${i}</li>`).join('') + 
        '</ul>';
}

function generateRoundInsights() {
    const insights = [];
    const roundAvgs = batchData.round_averages || {};
    const rounds = Object.keys(roundAvgs).sort((a, b) => parseInt(a) - parseInt(b));
    
    if (rounds.length > 0) {
        // Find peak activity round
        let maxCompletions = 0;
        let peakRound = 1;
        rounds.forEach(r => {
            if (roundAvgs[r].total_completions > maxCompletions) {
                maxCompletions = roundAvgs[r].total_completions;
                peakRound = r;
            }
        });
        
        insights.push(`<strong>Peak Activity:</strong> Round ${peakRound}`);
        insights.push(`<strong>Total Rounds:</strong> ${rounds.length}`);
        
        // Early vs late game comparison
        const earlyRounds = rounds.slice(0, Math.floor(rounds.length / 3));
        const lateRounds = rounds.slice(Math.floor(2 * rounds.length / 3));
        
        const earlyAvg = earlyRounds.reduce((sum, r) => sum + roundAvgs[r].mean_score, 0) / earlyRounds.length;
        const lateAvg = lateRounds.reduce((sum, r) => sum + roundAvgs[r].mean_score, 0) / lateRounds.length;
        
        insights.push(`<strong>Early Game Avg:</strong> ${earlyAvg.toFixed(1)}`);
        insights.push(`<strong>Late Game Avg:</strong> ${lateAvg.toFixed(1)}`);
    }
    
    document.getElementById('roundInsights').innerHTML = 
        '<ul class="list-unstyled">' + 
        insights.map(i => `<li class="mb-2">${i}</li>`).join('') + 
        '</ul>';
}

// Loading indicator
function showLoading(show) {
    if (show) {
        let loadingDiv = document.getElementById('batchLoadingOverlay');
        if (!loadingDiv) {
            loadingDiv = document.createElement('div');
            loadingDiv.id = 'batchLoadingOverlay';
            loadingDiv.className = 'batch-loading';
            loadingDiv.innerHTML = `
                <div class="text-center">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <div class="mt-3">
                        <h5>Processing Batch Data...</h5>
                        <p>Analyzing simulation results</p>
                    </div>
                </div>
            `;
            document.body.appendChild(loadingDiv);
        }
        loadingDiv.style.display = 'block';
    } else {
        const loadingDiv = document.getElementById('batchLoadingOverlay');
        if (loadingDiv) {
            loadingDiv.style.display = 'none';
        }
    }
}