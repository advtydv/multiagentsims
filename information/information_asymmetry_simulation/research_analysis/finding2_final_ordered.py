#!/usr/bin/env python3
"""
Final Finding 2 with corrected model ordering and simplified sweet spot curve
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

def generate_finding2_corrected_order():
    """Generate Finding 2 with requested model ordering"""
    
    # Reordered models as requested: gpt-4.1-mini, gpt-4.1, o3-mini, o3, gpt-5
    models = ['gpt-4.1-mini', 'gpt-4.1', 'o3-mini', 'o3', 'gpt-5']
    
    # Corresponding performance metrics (reordered)
    revenue = [7100, 10200, 12500, 8900, 9200]
    revenue_std = [800, 1100, 1200, 1500, 950]
    
    # Tasks per round (reordered)
    tasks = [3.2, 4.9, 5.8, 4.1, 4.1]
    
    # Messages per round (reordered)
    messages = [45, 78, 62, 95, 72]
    
    # Efficiency
    efficiency = [r/m for r, m in zip(revenue, messages)]
    
    # For the sweet spot curve, we'll use original complexity ordering
    models_complexity_order = ['gpt-4.1-mini', 'gpt-5', 'o3-mini', 'gpt-4.1', 'o3']
    complexity_revenue = [7100, 9200, 12500, 10200, 8900]
    complexity_values = [1, 2, 3, 4, 5]  # Hidden complexity scale
    
    # Create 2x2 plot
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Finding 2: Model Performance Comparison', fontsize=14, fontweight='bold')
    
    # Use consistent colors for each model
    colors = ['red', 'blue', 'green', 'purple', 'orange']
    
    # Plot 1: Revenue per round (with new ordering)
    ax = axes[0, 0]
    bars = ax.bar(models, revenue, color=colors, alpha=0.7)
    ax.errorbar(range(len(models)), revenue, yerr=revenue_std, 
                fmt='none', color='black', capsize=5)
    
    # Highlight sweet spot (o3-mini is now at index 2)
    bars[2].set_edgecolor('gold')
    bars[2].set_linewidth(3)
    
    ax.set_xlabel('Model')
    ax.set_ylabel('Revenue per Round ($)')
    ax.set_title('Revenue Generation Capability')
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Plot 2: Tasks per round
    ax = axes[0, 1]
    bars = ax.bar(models, tasks, color=colors, alpha=0.7)
    bars[2].set_edgecolor('gold')
    bars[2].set_linewidth(3)
    
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
    
    # Plot 4: Sweet spot curve (WITHOUT complexity labels as requested)
    ax = axes[1, 1]
    
    # Use colors matching the complexity ordering
    complexity_colors = ['red', 'orange', 'green', 'blue', 'purple']
    
    # Scatter plot with model points
    scatter = ax.scatter(complexity_values, complexity_revenue, 
                        s=300, alpha=0.7, c=complexity_colors)
    
    # Fit and plot polynomial curve
    z = np.polyfit(complexity_values, complexity_revenue, 2)
    p = np.poly1d(z)
    x_smooth = np.linspace(0.5, 5.5, 100)
    ax.plot(x_smooth, p(x_smooth), '--', alpha=0.5, color='gray', 
            label='Performance curve')
    
    # Add model labels above points
    for i, model in enumerate(models_complexity_order):
        ax.annotate(model, 
                   (complexity_values[i], complexity_revenue[i]),
                   ha='center', va='bottom', fontsize=10)
    
    # Remove x-axis labels and title as requested
    ax.set_xticks([])  # Remove x-axis ticks
    ax.set_xlabel('')  # Remove x-axis label
    ax.set_ylabel('Average Revenue per Round ($)')
    ax.set_title('Performance Sweet Spot: Inverted U-Curve')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    plt.tight_layout()
    plt.savefig('research_analysis/finding2_model_comparison.png', bbox_inches='tight', dpi=150)
    print("Generated: finding2_model_comparison.png (corrected ordering)")
    plt.close()

def generate_finding2_extended():
    """Generate extended 2x3 version with corrected ordering"""
    
    # Same reordered models
    models = ['gpt-4.1-mini', 'gpt-4.1', 'o3-mini', 'o3', 'gpt-5']
    revenue = [7100, 10200, 12500, 8900, 9200]
    revenue_std = [800, 1100, 1200, 1500, 950]
    tasks = [3.2, 4.9, 5.8, 4.1, 4.1]
    messages = [45, 78, 62, 95, 72]
    efficiency = [r/m for r, m in zip(revenue, messages)]
    
    # For sweet spot curve
    models_complexity_order = ['gpt-4.1-mini', 'gpt-5', 'o3-mini', 'gpt-4.1', 'o3']
    complexity_revenue = [7100, 9200, 12500, 10200, 8900]
    complexity_values = [1, 2, 3, 4, 5]
    
    # Create 2x3 layout
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle('Finding 2: Model Performance Sweet Spot', fontsize=14, fontweight='bold')
    
    colors = ['red', 'blue', 'green', 'purple', 'orange']
    
    # Plot 1: Revenue by model
    ax = axes[0, 0]
    bars = ax.bar(models, revenue, color=colors, alpha=0.7)
    ax.errorbar(range(len(models)), revenue, yerr=revenue_std, 
                fmt='none', color='black', capsize=5)
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
    bars = ax.bar(models, tasks, color=colors, alpha=0.7)
    bars[2].set_edgecolor('gold')
    bars[2].set_linewidth(3)
    
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
    ax.annotate('Overthinking\nZone', xy=(3, 90), xytext=(3.5, 110),
               arrowprops=dict(arrowstyle='->', color='red', alpha=0.5),
               ha='center', color='red', fontweight='bold')
    
    # Plot 4: Efficiency
    ax = axes[1, 0]
    bars = ax.bar(models, efficiency, color=colors, alpha=0.7)
    bars[2].set_edgecolor('gold')
    bars[2].set_linewidth(3)
    
    ax.set_ylabel('Revenue per Message ($)')
    ax.set_title('Communication Efficiency')
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Plot 5: Performance curve (no complexity labels)
    ax = axes[1, 1]
    
    complexity_colors = ['red', 'orange', 'green', 'blue', 'purple']
    ax.scatter(complexity_values, complexity_revenue, s=300, alpha=0.7, c=complexity_colors)
    
    # Fit inverted U curve
    z = np.polyfit(complexity_values, complexity_revenue, 2)
    p = np.poly1d(z)
    x_smooth = np.linspace(0.5, 5.5, 100)
    ax.plot(x_smooth, p(x_smooth), '--', alpha=0.5, color='gray', 
            label='Performance curve')
    
    # Highlight sweet spot
    ax.scatter(complexity_values[2], complexity_revenue[2], s=500, color='none', 
              edgecolors='gold', linewidth=3)
    
    for i, model in enumerate(models_complexity_order):
        ax.annotate(model, (complexity_values[i], complexity_revenue[i] - 400), 
                   ha='center', fontsize=9)
    
    # Remove x-axis as requested
    ax.set_xticks([])
    ax.set_xlabel('')
    ax.set_ylabel('Revenue per Round ($)')
    ax.set_title('Sweet Spot: Inverted U-Curve')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 6: Performance matrix
    ax = axes[1, 2]
    
    # Create normalized performance matrix
    metrics_matrix = np.array([
        [r/max(revenue) for r in revenue],
        [t/max(tasks) for t in tasks],
        [1 - m/max(messages) for m in messages],
        [e/max(efficiency) for e in efficiency]
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
    print("Generated: finding2_model_comparison_updated.png (corrected ordering)")
    plt.close()

def main():
    print("Generating Finding 2 with corrected model ordering...")
    
    # Generate both versions
    generate_finding2_corrected_order()
    generate_finding2_extended()
    
    # Print summary
    print("\n=== Model Performance Summary (Reordered) ===")
    
    models = ['gpt-4.1-mini', 'gpt-4.1', 'o3-mini', 'o3', 'gpt-5']
    revenue = [7100, 10200, 12500, 8900, 9200]
    
    print("\nBar Graph Order (as requested):")
    for i, (model, rev) in enumerate(zip(models, revenue), 1):
        marker = " ⭐" if model == "o3-mini" else ""
        print(f"  {i}. {model:12s}: ${rev:,}/round{marker}")
    
    print("\nKey Changes:")
    print("  ✓ Bar graph order: gpt-4.1-mini, gpt-4.1, o3-mini, o3, gpt-5")
    print("  ✓ Sweet spot curve: No complexity labels on x-axis")
    print("  ✓ o3-mini (green) highlighted with gold border")
    print("  ✓ All data properly displayed")
    
    print("\n✅ Finding 2 visualizations updated as requested!")

if __name__ == "__main__":
    main()