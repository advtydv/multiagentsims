// Batch Dashboard JavaScript
// Handles aggregated analysis across multiple simulations

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
    
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
    
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
        const response = await fetch(`/api/batch/${batchId}/summary`);
        
        if (!response.ok) {
            console.error('Failed to fetch batch data:', response.status);
            alert('Failed to load batch data. Check console for details.');
            showLoading(false);
            return;
        }
        
        batchData = await response.json();
        console.log('Loaded batch data:', batchData);
        
        // Check if we have the expected data structure
        if (!batchData.config || !batchData.config.simulation) {
            console.error('Invalid batch data structure:', batchData);
            alert('Batch data is missing configuration. Processing may have failed.');
            showLoading(false);
            return;
        }
        
        currentBatch = batchId;
        
        // Generate colors for agents
        generateAgentColors(batchData.config.simulation.agents);
        
        // Update UI
        updateBatchInfo();
        
        // Load each tab's content
        loadStatisticalOverview();
        loadPerformanceAnalysis();
        loadRankingDistributions();
        loadCooperationPatterns();
        loadStrategyEffectiveness();
        loadVarianceAnalysis();
        loadStatisticalTests();
        
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

// Statistical Overview Tab
function loadStatisticalOverview() {
    console.log('Loading statistical overview...');
    console.log('batchData:', batchData);
    
    // Check if we have the required data
    if (!batchData || !batchData.aggregate_metrics) {
        console.error('Missing aggregate_metrics in batchData');
        return;
    }
    
    // Calculate aggregate metrics
    const metrics = batchData.aggregate_metrics;
    console.log('Aggregate metrics:', metrics);
    
    // Update metric cards
    updateMetricCard('avgTasksPerAgent', metrics.avg_tasks_per_agent);
    updateMetricCard('avgPointsPerAgent', metrics.avg_points_per_agent);
    updateMetricCard('cooperationIndex', metrics.cooperation_index);
    updateMetricCard('systemEfficiency', metrics.system_efficiency);
    
    // Create distribution charts
    if (metrics.score_distribution) {
        createScoreDistributionChart(metrics.score_distribution);
    }
    if (metrics.task_distribution) {
        createTaskDistributionChart(metrics.task_distribution);
    }
}

// Performance Analysis Tab
function loadPerformanceAnalysis() {
    const perfData = batchData.performance_data || {};
    
    // Create agent performance comparison chart
    if (perfData.agent_comparisons) {
        createAgentPerformanceChart(perfData.agent_comparisons);
    }
    
    // Fill performance consistency table
    if (perfData.consistency_metrics) {
        fillPerformanceConsistencyTable(perfData.consistency_metrics);
        generateConsistencyInsights(perfData.consistency_metrics);
    }
    
    // Create score trajectory chart
    if (perfData.score_trajectories) {
        createScoreTrajectoryChart(perfData.score_trajectories);
    }
}

// Ranking Distributions Tab
function loadRankingDistributions() {
    const rankData = batchData.ranking_data;
    
    // Create ranking probability heatmap
    createRankingHeatmap(rankData.probability_matrix);
    
    // Show dominant rankings
    showDominantRankings(rankData.dominant_patterns);
    
    // Create average rank chart
    createAvgRankChart(rankData.average_ranks);
    
    // Create rank volatility chart
    createRankVolatilityChart(rankData.rank_volatility);
}

// Cooperation Patterns Tab
function loadCooperationPatterns() {
    const coopData = batchData.cooperation_data;
    
    // Create cooperation distribution chart
    createCooperationDistributionChart(coopData.score_distribution);
    
    // Create cooperation-performance correlation chart
    createCooperationCorrelationChart(coopData.performance_correlation);
    
    // Fill cooperation consistency table
    fillCooperationConsistencyTable(coopData.consistency_metrics);
    
    // Create alliance formation chart
    createAllianceFormationChart(coopData.alliance_rates);
    
    // Generate cooperation insights
    generateBatchCooperationInsights(coopData);
}

// Strategy Effectiveness Tab
function loadStrategyEffectiveness() {
    const stratData = batchData.strategy_data;
    
    // Create information sharing patterns chart
    createInfoSharingPatternsChart(stratData.sharing_patterns);
    
    // Create strategy performance chart
    createStrategyPerformanceChart(stratData.strategy_outcomes);
    
    // Analyze communication strategies
    analyzeCommunicationStrategies(stratData.communication_analysis);
}

// Variance Analysis Tab
function loadVarianceAnalysis() {
    const varData = batchData.variance_data;
    
    // Create outcome variance chart
    createOutcomeVarianceChart(varData.outcome_variance);
    
    // Generate variance insights
    generateVarianceInsights(varData);
    
    // Create simulation clustering chart
    createSimulationClusteringChart(varData.simulation_clusters);
    
    // Analyze outliers
    analyzeOutliers(varData.outlier_simulations);
}

// Statistical Tests Tab
function loadStatisticalTests() {
    const testData = batchData.statistical_tests;
    
    // Show ANOVA results
    showPerformanceANOVA(testData.performance_anova);
    
    // Show pairwise comparisons
    showPairwiseComparisons(testData.pairwise_tests);
    
    // Fill correlation table
    fillCorrelationTable(testData.correlations);
    
    // Analyze effect sizes
    analyzeEffectSizes(testData.effect_sizes);
}

// Helper function to update metric cards with confidence intervals
function updateMetricCard(elementId, metricData) {
    console.log(`Updating metric card: ${elementId}`, metricData);
    
    if (!metricData) {
        console.warn(`No metric data for ${elementId}`);
        return;
    }
    
    const mainElement = document.getElementById(elementId);
    
    // Map the main element IDs to their corresponding CI element IDs
    const ciElementIdMap = {
        'avgTasksPerAgent': 'avgTasksCI',
        'avgPointsPerAgent': 'avgPointsCI',
        'cooperationIndex': 'cooperationCI',
        'systemEfficiency': 'efficiencyCI'
    };
    
    const ciElementId = ciElementIdMap[elementId] || (elementId + 'CI');
    const ciElement = document.getElementById(ciElementId);
    
    if (!mainElement) {
        console.error(`Element not found: ${elementId}`);
        return;
    }
    
    if (!ciElement) {
        console.error(`CI element not found: ${ciElementId}`);
        return;
    }
    
    // Handle different data structures
    if (typeof metricData === 'object' && 'mean' in metricData) {
        mainElement.textContent = metricData.mean.toFixed(2);
        ciElement.textContent = `±${(metricData.ci || 0).toFixed(2)} (95% CI)`;
    } else if (typeof metricData === 'number') {
        mainElement.textContent = metricData.toFixed(2);
        ciElement.textContent = '±0.00 (95% CI)';
    } else {
        console.error(`Invalid metric data structure for ${elementId}:`, metricData);
    }
}

// Chart creation functions
function createScoreDistributionChart(distributionData) {
    console.log('Creating score distribution chart:', distributionData);
    
    if (!distributionData || Object.keys(distributionData).length === 0) {
        console.warn('No distribution data provided for score distribution chart');
        return;
    }
    
    const canvas = document.getElementById('scoreDistributionChart');
    if (!canvas) {
        console.error('Score distribution chart canvas not found');
        return;
    }
    
    const ctx = canvas.getContext('2d');
    
    // Convert boxplot data to bar chart with error bars
    const agents = Object.keys(distributionData);
    const means = agents.map(a => distributionData[a].mean || distributionData[a].median);
    const mins = agents.map(a => distributionData[a].min);
    const maxs = agents.map(a => distributionData[a].max);
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: agents,
            datasets: [{
                label: 'Mean Score',
                data: means,
                backgroundColor: agents.map(a => agentColors[a] || 'rgba(54, 162, 235, 0.5)'),
                borderColor: agents.map(a => agentColors[a] || 'rgb(54, 162, 235)'),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Final Score Distribution by Agent'
                },
                tooltip: {
                    callbacks: {
                        afterLabel: function(context) {
                            const agent = agents[context.dataIndex];
                            const data = distributionData[agent];
                            return [
                                `Min: ${data.min.toFixed(2)}`,
                                `Max: ${data.max.toFixed(2)}`,
                                `Range: ${(data.max - data.min).toFixed(2)}`
                            ];
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Score'
                    }
                }
            }
        }
    });
}

function createTaskDistributionChart(distributionData) {
    const canvas = document.getElementById('taskDistributionChart');
    if (!canvas) {
        console.error('Task distribution chart canvas not found');
        return;
    }
    
    const ctx = canvas.getContext('2d');
    
    // Since we don't have detailed distribution data, create a simple bar chart
    // showing task completion statistics
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Task Completion'],
            datasets: [{
                label: 'Average Tasks',
                data: [distributionData.mean || 0],
                backgroundColor: 'rgba(75, 192, 192, 0.5)',
                borderColor: 'rgb(75, 192, 192)',
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
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Tasks'
                    }
                }
            }
        }
    });
}

function createAgentPerformanceChart(comparisonData) {
    const ctx = document.getElementById('agentPerformanceChart').getContext('2d');
    
    const agents = Object.keys(comparisonData);
    const datasets = [
        {
            label: 'Mean Score',
            data: agents.map(a => comparisonData[a].mean_score),
            backgroundColor: agents.map(a => agentColors[a]),
            borderWidth: 1
        }
    ];
    
    // Add error bars for standard deviation
    const errorBars = {
        type: 'scatter',
        label: 'Score Range (±1 SD)',
        data: agents.map((a, i) => ({
            x: i,
            y: comparisonData[a].mean_score,
            yMin: comparisonData[a].mean_score - comparisonData[a].std_dev,
            yMax: comparisonData[a].mean_score + comparisonData[a].std_dev
        })),
        showLine: false,
        pointRadius: 0
    };
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: agents,
            datasets: [...datasets, errorBars]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Agent Performance Comparison (Mean ± SD)'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Score'
                    }
                }
            }
        }
    });
}

function createRankingHeatmap(probabilityMatrix) {
    const canvas = document.getElementById('rankingHeatmap');
    if (!canvas) {
        console.error('Ranking heatmap canvas not found');
        return;
    }
    
    const ctx = canvas.getContext('2d');
    
    // Convert probability matrix to stacked bar chart
    const agents = Object.keys(probabilityMatrix);
    const ranks = Object.keys(probabilityMatrix[agents[0]]);
    
    // Create datasets for each rank
    const datasets = ranks.map((rank, rankIndex) => {
        const colors = [
            'rgba(255, 99, 132, 0.8)',    // Rank 1 - Red
            'rgba(255, 159, 64, 0.8)',    // Rank 2 - Orange
            'rgba(255, 205, 86, 0.8)',    // Rank 3 - Yellow
            'rgba(75, 192, 192, 0.8)',    // Rank 4 - Teal
            'rgba(54, 162, 235, 0.8)',    // Rank 5 - Blue
            'rgba(153, 102, 255, 0.8)',   // Rank 6 - Purple
            'rgba(201, 203, 207, 0.8)',   // Rank 7+ - Gray
            'rgba(201, 203, 207, 0.6)',
            'rgba(201, 203, 207, 0.4)',
            'rgba(201, 203, 207, 0.2)'
        ];
        
        return {
            label: `Rank ${rank}`,
            data: agents.map(agent => probabilityMatrix[agent][rank] * 100),
            backgroundColor: colors[rankIndex] || colors[colors.length - 1],
            borderColor: 'white',
            borderWidth: 1
        };
    });
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: agents,
            datasets: datasets
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Probability of Achieving Each Rank (%)'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y.toFixed(1)}%`;
                        }
                    }
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
                    min: 0,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Probability (%)'
                    }
                }
            }
        }
    });
}

// Table filling functions
function fillPerformanceConsistencyTable(consistencyData) {
    const tbody = document.getElementById('performanceConsistencyBody');
    tbody.innerHTML = '';
    
    Object.entries(consistencyData).forEach(([agent, metrics]) => {
        const row = tbody.insertRow();
        row.innerHTML = `
            <td class="agent-${agent.split('_')[1]}">${agent}</td>
            <td>${metrics.mean.toFixed(2)}</td>
            <td>${metrics.std_dev.toFixed(2)}</td>
            <td>${metrics.cv_percent.toFixed(1)}%</td>
            <td>${metrics.min.toFixed(2)}</td>
            <td>${metrics.max.toFixed(2)}</td>
            <td>${metrics.range.toFixed(2)}</td>
        `;
    });
}

function fillCooperationConsistencyTable(consistencyData) {
    const tbody = document.getElementById('cooperationConsistencyBody');
    tbody.innerHTML = '';
    
    Object.entries(consistencyData).forEach(([agent, metrics]) => {
        const row = tbody.insertRow();
        row.innerHTML = `
            <td class="agent-${agent.split('_')[1]}">${agent}</td>
            <td>${metrics.mean_given.toFixed(2)}</td>
            <td>${metrics.std_given.toFixed(2)}</td>
            <td>${metrics.mean_received.toFixed(2)}</td>
            <td>${metrics.std_received.toFixed(2)}</td>
            <td>${metrics.reciprocity.toFixed(2)}</td>
        `;
    });
}

function fillCorrelationTable(correlationData) {
    const tbody = document.getElementById('correlationBody');
    tbody.innerHTML = '';
    
    correlationData.forEach(corr => {
        const row = tbody.insertRow();
        const significance = corr.p_value < 0.001 ? '***' : 
                           corr.p_value < 0.01 ? '**' : 
                           corr.p_value < 0.05 ? '*' : 'n.s.';
        
        row.innerHTML = `
            <td>${corr.var1}</td>
            <td>${corr.var2}</td>
            <td>${corr.correlation.toFixed(3)}</td>
            <td>${corr.p_value.toFixed(4)}</td>
            <td>${significance}</td>
        `;
    });
}

// Insight generation functions
function generateConsistencyInsights(consistencyData) {
    const insights = [];
    
    // Find most and least consistent agents
    const agents = Object.entries(consistencyData)
        .sort((a, b) => a[1].cv_percent - b[1].cv_percent);
    
    const mostConsistent = agents[0];
    const leastConsistent = agents[agents.length - 1];
    
    insights.push(`<strong>Most Consistent:</strong> ${mostConsistent[0]} (CV: ${mostConsistent[1].cv_percent.toFixed(1)}%)`);
    insights.push(`<strong>Least Consistent:</strong> ${leastConsistent[0]} (CV: ${leastConsistent[1].cv_percent.toFixed(1)}%)`);
    
    // Check for high variance agents
    const highVariance = agents.filter(([_, data]) => data.cv_percent > 30);
    if (highVariance.length > 0) {
        insights.push(`<strong>High Variance Alert:</strong> ${highVariance.length} agents show CV > 30%`);
    }
    
    document.getElementById('consistencyInsights').innerHTML = 
        '<ul class="list-unstyled">' + 
        insights.map(i => `<li>${i}</li>`).join('') + 
        '</ul>';
}

function generateBatchCooperationInsights(coopData) {
    const insights = [];
    
    // Analyze cooperation-performance relationship
    if (coopData.performance_correlation.r > 0.5) {
        insights.push(`<strong>Cooperation Pays:</strong> Strong positive correlation (r=${coopData.performance_correlation.r.toFixed(2)}) between cooperation and performance`);
    }
    
    // Check alliance formation rate
    const allianceRate = coopData.alliance_rates.overall_rate;
    insights.push(`<strong>Alliance Formation:</strong> ${(allianceRate * 100).toFixed(1)}% of agent pairs form stable alliances`);
    
    // Identify cooperation strategies
    if (coopData.strategy_clusters) {
        insights.push(`<strong>Strategy Diversity:</strong> ${coopData.strategy_clusters.length} distinct cooperation strategies identified`);
    }
    
    document.getElementById('batchCooperationInsights').innerHTML = 
        '<ul class="list-unstyled">' + 
        insights.map(i => `<li class="mb-2">${i}</li>`).join('') + 
        '</ul>';
}

// Loading indicator
function showLoading(show) {
    if (show) {
        // Create loading overlay if it doesn't exist
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
                        <p>Aggregating results from multiple simulations</p>
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

// Stub implementations for missing chart functions
function createScoreTrajectoryChart(trajectoryData) {
    console.log('Score trajectory chart - not yet implemented');
}

function showDominantRankings(patterns) {
    const container = document.getElementById('dominantRankings');
    if (!container || !patterns || patterns.length === 0) return;
    
    let html = '<ul class="list-unstyled">';
    patterns.forEach(p => {
        html += `<li><strong>${p.agent}</strong> - Rank ${p.rank} (${(p.frequency * 100).toFixed(1)}%)</li>`;
    });
    html += '</ul>';
    container.innerHTML = html;
}

function createAvgRankChart(rankData) {
    console.log('Average rank chart - not yet implemented');
}

function createRankVolatilityChart(volatilityData) {
    console.log('Rank volatility chart - not yet implemented');
}

function createCooperationDistributionChart(distributionData) {
    console.log('Cooperation distribution chart - not yet implemented');
}

function createCooperationCorrelationChart(correlationData) {
    console.log('Cooperation correlation chart - not yet implemented');
}

function createAllianceFormationChart(allianceData) {
    console.log('Alliance formation chart - not yet implemented');
}

function createInfoSharingPatternsChart(sharingData) {
    console.log('Info sharing patterns chart - not yet implemented');
}

function createStrategyPerformanceChart(strategyData) {
    console.log('Strategy performance chart - not yet implemented');
}

function analyzeCommunicationStrategies(commData) {
    console.log('Communication strategies analysis - not yet implemented');
}

function createOutcomeVarianceChart(varianceData) {
    console.log('Outcome variance chart - not yet implemented');
}

function generateVarianceInsights(varData) {
    const container = document.getElementById('varianceInsights');
    if (!container) return;
    container.innerHTML = '<p>Variance analysis insights will be displayed here.</p>';
}

function createSimulationClusteringChart(clusterData) {
    console.log('Simulation clustering chart - not yet implemented');
}

function analyzeOutliers(outlierData) {
    const container = document.getElementById('outlierAnalysis');
    if (!container) return;
    container.innerHTML = '<p>Outlier analysis will be displayed here.</p>';
}

function showPerformanceANOVA(anovaData) {
    const container = document.getElementById('performanceANOVA');
    if (!container || !anovaData) return;
    container.innerHTML = `<p>${anovaData.interpretation || 'ANOVA analysis not available.'}</p>`;
}

function showPairwiseComparisons(pairwiseData) {
    const container = document.getElementById('pairwiseComparisons');
    if (!container) return;
    container.innerHTML = '<p>Pairwise comparisons will be displayed here.</p>';
}

function analyzeEffectSizes(effectData) {
    const container = document.getElementById('effectSizeAnalysis');
    if (!container) return;
    container.innerHTML = '<p>Effect size analysis will be displayed here.</p>';
}