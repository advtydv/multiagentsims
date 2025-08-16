// Enhanced Batch Dashboard JavaScript
// Focus on meaningful metrics and actionable insights

let currentBatch = null;
let batchData = null;
let charts = {};

// Color schemes
const strategyColors = {
    'aggressive': '#FF6B6B',
    'collaborative': '#4ECDC4', 
    'selective': '#45B7D1',
    'passive': '#95A5A6'
};

const tierColors = {
    'top': '#FF6B6B',
    'middle': '#4ECDC4',
    'bottom': '#45B7D1'
};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    loadBatches();
    
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

// Load and analyze batch
async function loadBatch(batchId) {
    showLoading(true);
    currentBatch = batchId;
    
    try {
        const response = await fetch(`/api/batch/${batchId}/enhanced`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        batchData = await response.json();
        console.log('Enhanced batch data loaded:', batchData);
        
        // Check for errors in data
        if (batchData.error) {
            alert(`Warning: Some data could not be processed.\nError: ${batchData.error}\n\nShowing available data.`);
        }
        
        // Update UI
        updateBatchInfo();
        renderKeyInsights();
        
        // Render all tabs
        renderStrategyAnalysis();
        renderPerformancePatterns();
        renderInformationEconomics();
        renderBehavioralCorrelations();
        renderTemporalDynamics();
        renderStatisticalAnalysis();
        renderAdvancedInsights();
        
        // Show content
        document.getElementById('mainContent').classList.remove('d-none');
        document.getElementById('batchInfo').classList.remove('d-none');
        
    } catch (error) {
        console.error('Failed to load batch:', error);
        alert('Failed to load batch data. Please check the console for details.');
    } finally {
        showLoading(false);
    }
}

// Update batch information header
function updateBatchInfo() {
    document.getElementById('batchId').textContent = batchData.batch_id;
    document.getElementById('numSimulations').textContent = batchData.num_simulations;
    
    // Calculate total data points
    const agentCount = batchData.config?.simulation?.agents || 10;
    const dataPoints = batchData.num_simulations * agentCount;
    document.getElementById('dataPoints').textContent = dataPoints;
    
    // Determine confidence level based on sample size
    let confidence = 'Low';
    if (dataPoints > 100) confidence = 'High';
    else if (dataPoints > 50) confidence = 'Medium';
    
    const confidenceEl = document.getElementById('confidenceLevel');
    confidenceEl.textContent = confidence;
    confidenceEl.className = `badge bg-${confidence === 'High' ? 'success' : confidence === 'Medium' ? 'warning' : 'danger'}`;
}

// Render key insights summary
function renderKeyInsights() {
    const container = document.getElementById('insightsContainer');
    container.innerHTML = '';
    
    const insights = batchData.key_insights || [];
    
    insights.forEach(insight => {
        const col = document.createElement('div');
        col.className = 'col-md-3 mb-2';
        
        const card = document.createElement('div');
        card.className = `card insight-card ${insight.confidence}-confidence`;
        
        card.innerHTML = `
            <div class="card-body">
                <h6 class="card-subtitle mb-2 text-muted">${insight.category}</h6>
                <p class="card-text"><strong>${insight.finding}</strong></p>
                <small class="text-muted">${insight.evidence}</small>
            </div>
        `;
        
        col.appendChild(card);
        container.appendChild(col);
    });
    
    // Add placeholder if no insights
    if (insights.length === 0) {
        container.innerHTML = '<div class="col-12"><p class="text-muted">No key insights available yet.</p></div>';
    }
}

// Strategy Effectiveness Analysis
function renderStrategyAnalysis() {
    const strategies = batchData.strategy_effectiveness || {};
    
    // Check if we have data
    if (Object.keys(strategies).length === 0) {
        document.getElementById('strategyChart').innerHTML = '<p class="text-muted">No strategy data available</p>';
        document.getElementById('strategyCards').innerHTML = '<p class="text-muted">No strategies to display</p>';
        return;
    }
    
    // Strategy performance comparison chart
    const strategyData = Object.entries(strategies).map(([strategy, data]) => ({
        strategy: strategy,
        avgScore: data.avg_score || 0,
        winRate: (data.win_rate || 0) * 100,
        efficiency: data.avg_efficiency || 0,
        count: data.count || 0
    }));
    
    // Plotly bar chart
    const trace1 = {
        x: strategyData.map(d => d.strategy),
        y: strategyData.map(d => d.avgScore),
        name: 'Average Score',
        type: 'bar',
        marker: {
            color: strategyData.map(d => strategyColors[d.strategy] || '#999')
        }
    };
    
    const layout = {
        title: 'Average Score by Strategy',
        xaxis: { title: 'Strategy Type' },
        yaxis: { title: 'Average Score' },
        showlegend: false
    };
    
    Plotly.newPlot('strategyChart', [trace1], layout);
    
    // Strategy cards
    const cardsContainer = document.getElementById('strategyCards');
    cardsContainer.innerHTML = '';
    
    strategyData.sort((a, b) => b.avgScore - a.avgScore).forEach(strategy => {
        const card = document.createElement('div');
        card.className = 'strategy-card';
        card.style.background = `linear-gradient(135deg, ${strategyColors[strategy.strategy]}80 0%, ${strategyColors[strategy.strategy]} 100%)`;
        
        card.innerHTML = `
            <h6>${strategy.strategy.charAt(0).toUpperCase() + strategy.strategy.slice(1)}</h6>
            <div class="d-flex justify-content-between">
                <span>Avg Score:</span>
                <strong>${strategy.avgScore.toFixed(1)}</strong>
            </div>
            <div class="d-flex justify-content-between">
                <span>Win Rate:</span>
                <strong>${strategy.winRate.toFixed(1)}%</strong>
            </div>
            <div class="d-flex justify-content-between">
                <span>Efficiency:</span>
                <strong>${strategy.efficiency.toFixed(2)}</strong>
            </div>
            <small class="text-white-50">n=${strategy.count}</small>
        `;
        
        cardsContainer.appendChild(card);
    });
    
    // Win rate chart
    const ctx = document.getElementById('winRateChart');
    if (!ctx) return; // Safety check
    
    if (charts.winRate) charts.winRate.destroy();
    
    charts.winRate = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: strategyData.map(d => d.strategy),
            datasets: [{
                label: 'Win Rate (%)',
                data: strategyData.map(d => d.winRate),
                backgroundColor: strategyData.map(d => strategyColors[d.strategy] + '80'),
                borderColor: strategyData.map(d => strategyColors[d.strategy]),
                borderWidth: 2
            }]
        },
        options: {
            indexAxis: 'y',  // This makes it horizontal
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    beginAtZero: true,
                    max: 100
                }
            },
            plugins: {
                title: {
                    display: false
                }
            }
        }
    });
}

// Performance Patterns Analysis
function renderPerformancePatterns() {
    const patterns = batchData.performance_patterns || {};
    
    // Render tier cards
    const tiersContainer = document.getElementById('performanceTiers');
    tiersContainer.innerHTML = '';
    
    ['top', 'middle', 'bottom'].forEach(tier => {
        if (patterns[tier]) {
            const col = document.createElement('div');
            col.className = 'col-md-4';
            
            const card = document.createElement('div');
            card.className = `performance-tier tier-${tier}`;
            
            card.innerHTML = `
                <h5>${tier.charAt(0).toUpperCase() + tier.slice(1)} Performers</h5>
                <div class="row">
                    <div class="col-6">
                        <div class="metric-label">Avg Score</div>
                        <div class="metric-value">${patterns[tier].avg_score.toFixed(0)}</div>
                    </div>
                    <div class="col-6">
                        <div class="metric-label">Avg Tasks</div>
                        <div class="metric-value">${patterns[tier].avg_tasks.toFixed(1)}</div>
                    </div>
                </div>
                <hr>
                <div class="small">
                    <div>First Completions: ${patterns[tier].avg_first_completions.toFixed(1)}</div>
                    <div>Share Ratio: ${patterns[tier].avg_share_ratio.toFixed(2)}</div>
                    <div>Efficiency: ${patterns[tier].avg_efficiency.toFixed(2)}</div>
                    <div>Messages: ${patterns[tier].avg_messages.toFixed(0)}</div>
                </div>
            `;
            
            col.appendChild(card);
            tiersContainer.appendChild(col);
        }
    });
    
    // Key differentiators chart
    if (patterns.key_differentiators) {
        const diff = patterns.key_differentiators;
        const ctx = document.getElementById('differentiatorsChart');
        
        if (!ctx) return; // Safety check
        
        if (charts.differentiators) charts.differentiators.destroy();
        
        charts.differentiators = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['Task Completion', 'Efficiency', 'First Mover', 'Sharing'],
                datasets: [{
                    label: 'Top vs Bottom Gap',
                    data: [
                        diff.task_completion_gap,
                        diff.efficiency_gap,
                        diff.first_mover_advantage,
                        diff.sharing_difference
                    ],
                    backgroundColor: 'rgba(255, 107, 107, 0.2)',
                    borderColor: 'rgb(255, 107, 107)',
                    pointBackgroundColor: 'rgb(255, 107, 107)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgb(255, 107, 107)'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: false
                    }
                }
            }
        });
    }
    
    // Performance distribution box plot
    const distributionData = [];
    ['top', 'middle', 'bottom'].forEach(tier => {
        if (patterns[tier]) {
            distributionData.push({
                y: Array(patterns[tier].count).fill(patterns[tier].avg_score),
                type: 'box',
                name: tier,
                marker: { color: tierColors[tier] }
            });
        }
    });
    
    Plotly.newPlot('performanceDistribution', distributionData, {
        title: 'Score Distribution by Tier',
        yaxis: { title: 'Score' }
    });
}

// Information Economics Analysis
function renderInformationEconomics() {
    const economics = batchData.information_economics || {};
    
    // Update summary cards
    if (economics.sharing_strategy) {
        document.getElementById('sharingAvgScore').textContent = 
            economics.sharing_strategy.avg_score.toFixed(0);
        document.getElementById('sharingROI').textContent = 
            economics.sharing_strategy.avg_roi.toFixed(2);
    }
    
    if (economics.hoarding_strategy) {
        document.getElementById('hoardingAvgScore').textContent = 
            economics.hoarding_strategy.avg_score.toFixed(0);
        document.getElementById('hoardingKept').textContent = 
            economics.hoarding_strategy.avg_kept.toFixed(1);
    }
    
    if (economics.optimal_sharing) {
        document.getElementById('optimalRange').textContent = 
            economics.optimal_sharing.range;
        document.getElementById('optimalScore').textContent = 
            economics.optimal_sharing.avg_score.toFixed(0);
    }
    
    // ROI comparison chart
    const roiData = [{
        x: ['Sharing', 'Hoarding'],
        y: [
            economics.sharing_strategy?.avg_score || 0,
            economics.hoarding_strategy?.avg_score || 0
        ],
        type: 'bar',
        marker: {
            color: ['#4ECDC4', '#FF6B6B']
        }
    }];
    
    Plotly.newPlot('sharingROIChart', roiData, {
        title: 'Strategy Performance Comparison',
        yaxis: { title: 'Average Score' }
    });
    
    // Optimal sharing visualization
    if (economics.optimal_sharing) {
        const optimalData = [{
            x: [economics.optimal_sharing.range],
            y: [economics.optimal_sharing.avg_score],
            type: 'scatter',
            mode: 'markers',
            marker: {
                size: 15,
                color: '#28a745'
            },
            name: 'Optimal'
        }];
        
        Plotly.newPlot('optimalSharingChart', optimalData, {
            title: 'Optimal Sharing Range',
            xaxis: { title: 'Sharing Rate Range' },
            yaxis: { title: 'Average Score' },
            annotations: [{
                x: economics.optimal_sharing.range,
                y: economics.optimal_sharing.avg_score,
                text: 'Peak Performance',
                showarrow: true,
                arrowhead: 2,
                ax: 0,
                ay: -40
            }]
        });
    }
}

// Behavioral Correlations Analysis
function renderBehavioralCorrelations() {
    const correlations = batchData.behavioral_correlations || {};
    
    // Correlation chart
    const corrData = [];
    const labels = [];
    const colors = [];
    const strengths = [];
    
    Object.entries(correlations).forEach(([metric, data]) => {
        if (metric !== 'most_impactful' && data.correlation !== undefined) {
            labels.push(metric.replace(/_/g, ' '));
            corrData.push(data.correlation);
            colors.push(data.significant ? '#28a745' : '#dc3545');
            strengths.push(data.strength);
        }
    });
    
    const trace = {
        x: labels,
        y: corrData,
        type: 'bar',
        marker: {
            color: colors
        },
        text: strengths,
        textposition: 'outside'
    };
    
    Plotly.newPlot('correlationChart', [trace], {
        title: 'Behavior-Performance Correlations',
        yaxis: { 
            title: 'Correlation Coefficient',
            range: [-1, 1]
        },
        xaxis: {
            tickangle: -45
        }
    });
    
    // Most impactful behaviors list
    const impactfulContainer = document.getElementById('impactfulBehaviors');
    impactfulContainer.innerHTML = '';
    
    if (correlations.most_impactful && correlations.most_impactful.length > 0) {
        const list = document.createElement('ul');
        list.className = 'list-group';
        
        correlations.most_impactful.forEach(([metric, correlation], index) => {
            const item = document.createElement('li');
            item.className = 'list-group-item d-flex justify-content-between align-items-center';
            
            const badgeClass = Math.abs(correlation) > 0.7 ? 'correlation-strong' :
                               Math.abs(correlation) > 0.4 ? 'correlation-moderate' :
                               'correlation-weak';
            
            item.innerHTML = `
                <div>
                    <strong>${index + 1}.</strong> ${metric.replace(/_/g, ' ')}
                </div>
                <span class="correlation-badge ${badgeClass}">
                    r = ${correlation.toFixed(3)}
                </span>
            `;
            
            list.appendChild(item);
        });
        
        impactfulContainer.appendChild(list);
    } else {
        impactfulContainer.innerHTML = '<p class="text-muted">No significant correlations found.</p>';
    }
    
    // Correlation matrix heatmap
    const matrixData = [];
    const matrixLabels = [];
    
    Object.entries(correlations).forEach(([metric, data]) => {
        if (metric !== 'most_impactful' && data.correlation !== undefined) {
            matrixLabels.push(metric);
            matrixData.push([data.correlation]);
        }
    });
    
    if (matrixData.length > 0) {
        const heatmap = [{
            z: matrixData,
            x: ['Performance'],
            y: matrixLabels,
            type: 'heatmap',
            colorscale: 'RdBu',
            reversescale: true,
            zmin: -1,
            zmax: 1
        }];
        
        Plotly.newPlot('correlationMatrix', heatmap, {
            title: 'Correlation Heatmap',
            xaxis: { side: 'top' },
            yaxis: { automargin: true }
        });
    }
}

// Temporal Dynamics Analysis
function renderTemporalDynamics() {
    const temporal = batchData.temporal_dynamics || {};
    
    // Activity over time chart
    if (temporal.round_metrics) {
        const rounds = Object.keys(temporal.round_metrics).sort((a, b) => parseInt(a) - parseInt(b));
        
        const traces = [
            {
                x: rounds,
                y: rounds.map(r => temporal.round_metrics[r].avg_tasks),
                name: 'Tasks',
                type: 'scatter',
                mode: 'lines+markers'
            },
            {
                x: rounds,
                y: rounds.map(r => temporal.round_metrics[r].avg_messages / 10), // Scale for visibility
                name: 'Messages (÷10)',
                type: 'scatter',
                mode: 'lines+markers'
            },
            {
                x: rounds,
                y: rounds.map(r => temporal.round_metrics[r].avg_info_exchanges),
                name: 'Info Exchanges',
                type: 'scatter',
                mode: 'lines+markers'
            }
        ];
        
        Plotly.newPlot('temporalChart', traces, {
            title: 'Activity Metrics Over Rounds',
            xaxis: { title: 'Round' },
            yaxis: { title: 'Average Count' }
        });
    }
    
    // Phase metrics
    if (temporal.phases) {
        ['early_game', 'mid_game', 'late_game'].forEach(phase => {
            const phaseData = temporal.phases[phase];
            if (phaseData) {
                const containerId = phase.replace('_game', 'GameMetrics');
                const container = document.getElementById(containerId);
                
                container.innerHTML = `
                    <div class="metric-label">Rounds</div>
                    <div class="small">${phaseData.rounds.join(', ')}</div>
                    <div class="metric-label mt-2">Avg Activity</div>
                    <div class="h5">${phaseData.avg_activity.toFixed(1)}</div>
                `;
            }
        });
    }
    
    // Temporal pattern
    if (temporal.trends) {
        document.getElementById('temporalPattern').textContent = 
            temporal.trends.pattern || 'Unknown';
        document.getElementById('activityChange').textContent = 
            `${(temporal.trends.activity_change * 100).toFixed(1)}%`;
    }
}

// Statistical Analysis
function renderStatisticalAnalysis() {
    const stats = batchData.statistical_analysis || {};
    const container = document.getElementById('statisticalTests');
    container.innerHTML = '';
    
    // Agent differences test
    if (stats.agent_differences) {
        const test = stats.agent_differences;
        const card = createStatTestCard(
            'Agent Performance Differences',
            test.test,
            test.f_statistic,
            test.p_value,
            test.significant,
            test.interpretation
        );
        container.appendChild(card);
    }
    
    // Strategy comparison test
    if (stats.strategy_comparison) {
        const test = stats.strategy_comparison;
        const card = createStatTestCard(
            'Strategy Effectiveness Comparison',
            test.test,
            test.t_statistic,
            test.p_value,
            test.significant,
            `${test.better_strategy} strategy performs better (mean: ${test[test.better_strategy + '_mean'].toFixed(1)})`
        );
        container.appendChild(card);
    }
}

// Helper function to create statistical test card
function createStatTestCard(title, testType, statistic, pValue, significant, interpretation) {
    const card = document.createElement('div');
    card.className = 'row mb-3';
    
    card.innerHTML = `
        <div class="col-12">
            <div class="${significant ? 'stat-significant' : 'card'}">
                <div class="card-body">
                    <h6>${title}</h6>
                    <div class="row">
                        <div class="col-md-3">
                            <span class="text-muted">Test:</span> <strong>${testType}</strong>
                        </div>
                        <div class="col-md-3">
                            <span class="text-muted">Statistic:</span> <strong>${statistic.toFixed(3)}</strong>
                        </div>
                        <div class="col-md-3">
                            <span class="text-muted">p-value:</span> 
                            <strong class="${significant ? 'text-success' : 'text-danger'}">
                                ${pValue.toFixed(4)}
                            </strong>
                        </div>
                        <div class="col-md-3">
                            <span class="badge bg-${significant ? 'success' : 'secondary'}">
                                ${significant ? 'Significant' : 'Not Significant'}
                            </span>
                        </div>
                    </div>
                    <div class="mt-2">
                        <small class="text-muted">
                            <i class="bi bi-info-circle"></i> ${interpretation}
                        </small>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    return card;
}

// Export data functionality
function exportData() {
    if (!batchData) return;
    
    const dataStr = JSON.stringify(batchData, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `${batchData.batch_id}_analysis.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
}

// Refresh analysis
function refreshAnalysis() {
    if (currentBatch) {
        loadBatch(currentBatch);
    }
}

// Advanced Insights Tab
function renderAdvancedInsights() {
    // Strategic Recommendations
    renderStrategicRecommendations();
    
    // Variance Analysis
    renderVarianceAnalysis();
    
    // Agent Trajectories
    renderAgentTrajectories();
    
    // Meta Insights
    renderMetaInsights();
}

function renderStrategicRecommendations() {
    const recommendations = batchData.strategic_recommendations || [];
    const container = document.getElementById('strategicRecommendations');
    
    if (recommendations.length === 0) {
        container.innerHTML = '<p class="text-muted">No recommendations available.</p>';
        return;
    }
    
    container.innerHTML = '';
    recommendations.forEach((rec, index) => {
        const priorityColor = {
            'high': 'danger',
            'medium': 'warning', 
            'low': 'info'
        }[rec.priority] || 'secondary';
        
        const card = document.createElement('div');
        card.className = 'card mb-3';
        card.innerHTML = `
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <span class="badge bg-${priorityColor} me-2">${rec.priority.toUpperCase()}</span>
                        <strong>${rec.category}</strong>
                    </div>
                    <small class="text-muted">Confidence: ${(rec.confidence * 100).toFixed(0)}%</small>
                </div>
                <h6 class="mt-2">${rec.recommendation}</h6>
                <p class="text-muted mb-0"><i class="bi bi-info-circle"></i> ${rec.rationale}</p>
            </div>
        `;
        container.appendChild(card);
    });
}

function renderVarianceAnalysis() {
    const variance = batchData.variance_analysis || {};
    
    // Outcome Stability
    const stabilityContainer = document.getElementById('outcomeStability');
    if (variance.outcome_stability) {
        const stability = variance.outcome_stability;
        stabilityContainer.innerHTML = `
            <div class="mb-3">
                <h6>Task Completion Stability</h6>
                <div class="progress mb-1">
                    <div class="progress-bar ${stability.task_completion?.stable ? 'bg-success' : 'bg-warning'}" 
                         style="width: ${100 - (stability.task_completion?.cv || 0) * 100}%">
                        ${stability.task_completion?.stable ? 'Stable' : 'Variable'}
                    </div>
                </div>
                <small>Mean: ${stability.task_completion?.mean?.toFixed(1) || 0}, CV: ${(stability.task_completion?.cv || 0).toFixed(2)}</small>
            </div>
            <div class="mb-3">
                <h6>Winner Diversity</h6>
                <p class="mb-1">Unique Winners: ${stability.winner_concentration?.unique_winners || 0}</p>
                ${stability.winner_concentration?.dominant_winner ? 
                    `<p class="mb-0">Dominant: ${stability.winner_concentration.dominant_winner[0]} (${stability.winner_concentration.dominant_winner[1]} wins)</p>` : ''}
            </div>
        `;
    }
    
    // Agent Consistency
    const consistencyContainer = document.getElementById('agentConsistency');
    if (variance.agent_consistency) {
        const consistency = variance.agent_consistency;
        let html = '<ul class="list-unstyled mb-0">';
        html += `<li><strong>Most Consistent:</strong> ${consistency.most_consistent || 'N/A'}</li>`;
        html += `<li><strong>Least Consistent:</strong> ${consistency.least_consistent || 'N/A'}</li>`;
        html += `<li><strong>Overall Consistency:</strong> ${((1 - (consistency.overall_consistency || 0)) * 100).toFixed(1)}%</li>`;
        html += '</ul>';
        consistencyContainer.innerHTML = html;
    }
}

function renderAgentTrajectories() {
    const trajectories = batchData.agent_trajectories || {};
    const container = document.getElementById('trajectoryChart');
    
    if (!trajectories.trajectory_patterns || Object.keys(trajectories.trajectory_patterns).length === 0) {
        container.innerHTML = '<p class="text-muted">No trajectory data available.</p>';
        return;
    }
    
    // Create trajectory visualization
    const patterns = trajectories.trajectory_patterns;
    const traces = [];
    
    Object.entries(patterns).forEach(([agent, data]) => {
        if (data.scores && data.scores.length > 0) {
            traces.push({
                x: data.scores.map((_, i) => `Sim ${i+1}`),
                y: data.scores,
                name: agent,
                type: 'scatter',
                mode: 'lines+markers',
                line: {
                    dash: data.pattern === 'volatile' ? 'dash' : 'solid',
                    width: data.pattern === 'improving' ? 3 : 2
                }
            });
        }
    });
    
    if (traces.length > 0) {
        Plotly.newPlot(container, traces, {
            title: 'Agent Score Trajectories Across Simulations',
            xaxis: { title: 'Simulation' },
            yaxis: { title: 'Score' },
            showlegend: true
        });
    }
}

function renderMetaInsights() {
    const meta = batchData.meta_insights || {};
    
    // Simulation Quality
    if (meta.simulation_quality) {
        const quality = meta.simulation_quality;
        document.getElementById('simulationQuality').innerHTML = `
            <ul class="list-unstyled mb-0">
                <li>Sample Size: ${quality.sample_size}</li>
                <li>Power: <span class="badge bg-${quality.statistical_power === 'high' ? 'success' : quality.statistical_power === 'medium' ? 'warning' : 'danger'}">${quality.statistical_power}</span></li>
                <li>Confidence: ${(quality.confidence_level * 100).toFixed(0)}%</li>
                ${quality.findings_reliability !== undefined ? 
                    `<li>Reliability: ${(quality.findings_reliability * 100).toFixed(0)}%</li>` : ''}
            </ul>
        `;
    }
    
    // Strategic Diversity
    if (meta.strategic_diversity) {
        const diversity = meta.strategic_diversity;
        document.getElementById('strategicDiversity').innerHTML = `
            <ul class="list-unstyled mb-0">
                <li>Strategies: ${diversity.num_strategies}</li>
                <li>Balance: ${(diversity.strategy_balance * 100).toFixed(0)}%</li>
                <li>Dominant: ${diversity.dominant_strategy || 'None'}</li>
            </ul>
        `;
    }
    
    // Competitive Dynamics
    if (meta.competitive_dynamics) {
        const dynamics = meta.competitive_dynamics;
        document.getElementById('competitiveDynamics').innerHTML = `
            <ul class="list-unstyled mb-0">
                <li>Competition: ${dynamics.competition_intensity}</li>
                <li>Gaps: ${dynamics.performance_gaps}</li>
                <li>Predictability: ${dynamics.winner_predictability}</li>
            </ul>
        `;
    }
}

// Loading overlay
function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (show) {
        overlay.classList.remove('d-none');
        overlay.style.position = 'fixed';
        overlay.style.top = '50%';
        overlay.style.left = '50%';
        overlay.style.transform = 'translate(-50%, -50%)';
        overlay.style.zIndex = '9999';
        overlay.style.backgroundColor = 'rgba(255, 255, 255, 0.95)';
        overlay.style.padding = '2rem';
        overlay.style.borderRadius = '10px';
        overlay.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.1)';
        
        if (batchData) {
            document.getElementById('processingCount').textContent = batchData.num_simulations || '0';
        }
    } else {
        overlay.classList.add('d-none');
    }
}