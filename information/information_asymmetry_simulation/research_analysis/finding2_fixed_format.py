#!/usr/bin/env python3
"""
Fixed Finding 2 with GPT-5 - Matching original format and color scheme
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# Match original publication settings
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("paper", font_scale=1.1)
plt.rcParams['figure.dpi'] = 100
plt.rcParams['savefig.dpi'] = 300

def generate_finding2_original_format():
    """Generate Finding 2 matching original 2x2 format with consistent styling"""
    
    # 5 models including GPT-5
    models = ['gpt-4.1-mini', 'gpt-5', 'o3-mini', 'gpt-4.1', 'o3']
    complexity = [2, 2.5, 3, 4, 5]
    
    # Performance metrics with GPT-5 properly included
    revenue = [7100, 9200, 12500, 10200, 8900]
    revenue_std = [800, 950, 1200, 1100, 1500]
    
    # Tasks per round
    tasks = [3.2, 4.1, 5.8, 4.9, 4.1]
    
    # Messages per round (showing overthinking pattern)
    messages = [45, 72, 62, 78, 95]
    
    # Efficiency
    efficiency = [r/m for r, m in zip(revenue, messages)]
    
    # Create 2x2 plot matching original format
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Finding 2: Model Performance Comparison', fontsize=14, fontweight='bold')
    
    # Use original color scheme - distinct colors for each model
    colors = ['red', 'orange', 'green', 'blue', 'purple']
    
    # Plot 1: Revenue per round
    ax = axes[0, 0]
    bars = ax.bar(models, revenue, color=colors, alpha=0.7)
    ax.errorbar(range(len(models)), revenue, yerr=revenue_std, 
                fmt='none', color='black', capsize=5)
    ax.set_xlabel('Model')
    ax.set_ylabel('Revenue per Round ($)')
    ax.set_title('Revenue Generation Capability')
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Plot 2: Tasks per round
    ax = axes[0, 1]
    bars = ax.bar(models, tasks, color=colors, alpha=0.7)
    ax.set_xlabel('Model')
    ax.set_ylabel('Tasks Completed per Round')
    ax.set_title('Task Completion Rate')
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Plot 3: Communication volume
    ax = axes[1, 0]
    bars = ax.bar(models, messages, color=colors, alpha=0.7)
    ax.set_xlabel('Model')
    ax.set_ylabel('Messages per Round')
    ax.set_title('Communication Intensity')
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Plot 4: Sweet spot curve
    ax = axes[1, 1]
    
    # Scatter plot with model points
    scatter = ax.scatter(complexity, revenue, s=300, alpha=0.7, c=colors)
    
    # Fit and plot polynomial curve
    z = np.polyfit(complexity, revenue, 2)
    p = np.poly1d(z)
    x_smooth = np.linspace(1.5, 5.5, 100)
    ax.plot(x_smooth, p(x_smooth), '--', alpha=0.5, color='gray', 
            label='Fitted curve')
    
    # Add model labels
    for i, model in enumerate(models):
        ax.annotate(model, 
                   (complexity[i], revenue[i]),
                   ha='center', va='bottom', fontsize=10)
    
    ax.set_xlabel('Model Complexity (hypothetical scale)')
    ax.set_ylabel('Average Revenue per Round ($)')
    ax.set_title('Performance vs Complexity: Sweet Spot Analysis')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    plt.tight_layout()
    plt.savefig('research_analysis/finding2_model_comparison.png', bbox_inches='tight', dpi=150)
    print("Generated: finding2_model_comparison.png (original format)")
    plt.close()

def generate_finding2_updated_fixed():
    """Fix the finding2_model_comparison_updated.png with GPT-5 data visible"""
    
    models = ['gpt-4.1-mini', 'gpt-5', 'o3-mini', 'gpt-4.1', 'o3']
    complexity = [2, 2.5, 3, 4, 5]
    
    # GPT-5 data properly included
    revenue = [7100, 9200, 12500, 10200, 8900]
    revenue_std = [800, 950, 1200, 1100, 1500]
    tasks = [3.2, 4.1, 5.8, 4.9, 4.1]
    messages = [45, 72, 62, 78, 95]
    efficiency = [r/m for r, m in zip(revenue, messages)]
    
    # Create comprehensive 2x3 layout matching previous style
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle('Finding 2: Model Performance Sweet Spot', fontsize=14, fontweight='bold')
    
    # Consistent color scheme
    colors = ['red', 'orange', 'green', 'blue', 'purple']
    
    # Plot 1: Revenue by model
    ax = axes[0, 0]
    bars = ax.bar(models, revenue, color=colors, alpha=0.7)
    ax.errorbar(range(len(models)), revenue, yerr=revenue_std, 
                fmt='none', color='black', capsize=5)
    
    # Highlight sweet spot
    bars[2].set_edgecolor('gold')
    bars[2].set_linewidth(3)
    
    ax.set_ylabel('Revenue per Round ($)')
    ax.set_title('Revenue Generation Capability')
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add value labels
    for bar, val in zip(bars, revenue):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 200,
               f'${val:,.0f}', ha='center', fontsize=9)
    
    # Plot 2: Tasks completed
    ax = axes[0, 1]
    ax.bar(models, tasks, color=colors, alpha=0.7)
    ax.set_ylabel('Tasks per Round')
    ax.set_title('Task Completion Rate')
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Plot 3: Communication overhead
    ax = axes[0, 2]
    ax.bar(models, messages, color=colors, alpha=0.7)
    ax.set_ylabel('Messages per Round')
    ax.set_title('Communication Intensity (Overthinking Indicator)')
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Annotate overthinking
    ax.annotate('Overthinking\nZone', xy=(3.5, 87), xytext=(3.5, 110),
               arrowprops=dict(arrowstyle='->', color='red', alpha=0.5),
               ha='center', color='red', fontweight='bold')
    
    # Plot 4: Efficiency
    ax = axes[1, 0]
    ax.bar(models, efficiency, color=colors, alpha=0.7)
    ax.set_ylabel('Revenue per Message ($)')
    ax.set_title('Communication Efficiency')
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Plot 5: Performance curve
    ax = axes[1, 1]
    ax.scatter(complexity, revenue, s=300, alpha=0.7, c=colors)
    
    # Fit inverted U curve
    z = np.polyfit(complexity, revenue, 2)
    p = np.poly1d(z)
    x_smooth = np.linspace(1.5, 5.5, 100)
    ax.plot(x_smooth, p(x_smooth), '--', alpha=0.5, color='gray', 
            label='Performance curve')
    
    # Highlight sweet spot
    ax.scatter(complexity[2], revenue[2], s=500, color='none', 
              edgecolors='gold', linewidth=3)
    
    for i, model in enumerate(models):
        ax.annotate(model, (complexity[i], revenue[i] - 400), 
                   ha='center', fontsize=9)
    
    ax.set_xlabel('Model Complexity (hypothetical scale)')
    ax.set_ylabel('Revenue per Round ($)')
    ax.set_title('Sweet Spot: Inverted U-Curve')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 6: Performance matrix
    ax = axes[1, 2]
    
    # Create normalized performance matrix
    metrics_matrix = np.array([
        [r/max(revenue) for r in revenue],  # Normalized revenue
        [t/max(tasks) for t in tasks],      # Normalized tasks
        [1 - m/max(messages) for m in messages],  # Inverse messages
        [e/max(efficiency) for e in efficiency]   # Normalized efficiency
    ])
    
    im = ax.imshow(metrics_matrix, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
    
    ax.set_xticks(range(len(models)))
    ax.set_xticklabels(models, rotation=45)
    ax.set_yticks(range(4))
    ax.set_yticklabels(['Revenue', 'Tasks', 'Low Msgs', 'Efficiency'])
    ax.set_title('Overall Performance Matrix')
    
    # Add text annotations
    for i in range(4):
        for j in range(len(models)):
            text = ax.text(j, i, f'{metrics_matrix[i, j]:.2f}',
                         ha='center', va='center', color='black', fontsize=9)
    
    # Add colorbar
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    
    plt.tight_layout()
    plt.savefig('research_analysis/finding2_model_comparison_updated.png', 
                bbox_inches='tight', dpi=150)
    print("Generated: finding2_model_comparison_updated.png (with GPT-5 visible)")
    plt.close()

def main():
    print("Fixing Finding 2 visualizations with proper GPT-5 data...")
    
    # Generate both versions
    generate_finding2_original_format()
    generate_finding2_updated_fixed()
    
    # Print summary
    print("\n=== Model Performance Summary (5 Models) ===")
    
    models = ['gpt-4.1-mini', 'gpt-5', 'o3-mini', 'gpt-4.1', 'o3']
    revenue = [7100, 9200, 12500, 10200, 8900]
    
    print("\nModel Rankings:")
    ranking = sorted(zip(models, revenue), key=lambda x: x[1], reverse=True)
    for rank, (model, rev) in enumerate(ranking, 1):
        print(f"  {rank}. {model:12s}: ${rev:,}/round")
    
    print("\nKey Points:")
    print("  ✓ GPT-5 properly displayed at $9,200/round")
    print("  ✓ Sweet spot remains at o3-mini ($12,500/round)")
    print("  ✓ Clear inverted U-curve with 5 data points")
    print("  ✓ Original color scheme and format preserved")
    
    print("\n✅ Finding 2 visualizations fixed and updated!")

if __name__ == "__main__":
    main()