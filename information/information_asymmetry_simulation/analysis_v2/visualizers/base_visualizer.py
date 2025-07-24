"""
Base Visualizer Class

Provides common functionality for all visualization modules.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Professional color scheme
COLORS = {
    'primary': '#2E86AB',      # Blue
    'secondary': '#A23B72',    # Purple
    'success': '#27AE60',      # Green
    'warning': '#F39C12',      # Orange
    'danger': '#E74C3C',       # Red
    'info': '#3498DB',         # Light Blue
    'dark': '#2C3E50',         # Dark Gray
    'light': '#ECF0F1',        # Light Gray
    'accent1': '#9B59B6',      # Purple
    'accent2': '#1ABC9C'       # Turquoise
}

# Color palettes for different visualizations
PALETTES = {
    'sequential': ['#E8F4F8', '#B8E0E8', '#88CDD8', '#58B9C8', '#2E86AB'],
    'diverging': ['#E74C3C', '#F39C12', '#F7DC6F', '#27AE60', '#1ABC9C'],
    'categorical': [COLORS['primary'], COLORS['secondary'], COLORS['success'], 
                   COLORS['warning'], COLORS['accent1'], COLORS['accent2']]
}


class BaseVisualizer:
    """Base class for all visualizers"""
    
    def __init__(self, output_dir: Path, style: str = 'seaborn-v0_8-darkgrid'):
        """
        Initialize the visualizer.
        
        Args:
            output_dir: Directory to save visualizations
            style: Matplotlib style to use
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Set style
        try:
            plt.style.use(style)
        except:
            plt.style.use('seaborn-darkgrid')
            
        # Configure default settings
        self._configure_matplotlib()
        
    def _configure_matplotlib(self):
        """Configure matplotlib default settings"""
        plt.rcParams['figure.dpi'] = 100
        plt.rcParams['savefig.dpi'] = 300
        plt.rcParams['figure.figsize'] = (10, 6)
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.labelsize'] = 12
        plt.rcParams['axes.titlesize'] = 14
        plt.rcParams['legend.fontsize'] = 10
        plt.rcParams['xtick.labelsize'] = 10
        plt.rcParams['ytick.labelsize'] = 10
        
    def save_figure(self, fig: plt.Figure, filename: str, **kwargs):
        """
        Save a figure with consistent settings.
        
        Args:
            fig: Matplotlib figure to save
            filename: Name of the file (without extension)
            **kwargs: Additional arguments for savefig
        """
        default_kwargs = {
            'bbox_inches': 'tight',
            'facecolor': 'white',
            'edgecolor': 'none'
        }
        default_kwargs.update(kwargs)
        
        filepath = self.output_dir / f"{filename}.png"
        fig.savefig(filepath, **default_kwargs)
        plt.close(fig)
        
    def create_figure(
        self, 
        figsize: Tuple[float, float] = (10, 6),
        title: Optional[str] = None
    ) -> Tuple[plt.Figure, plt.Axes]:
        """
        Create a new figure with consistent styling.
        
        Args:
            figsize: Size of the figure
            title: Optional title for the figure
            
        Returns:
            Figure and axes objects
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        if title:
            fig.suptitle(title, fontsize=16, fontweight='bold', y=0.98)
            
        return fig, ax
        
    def create_subplots(
        self,
        nrows: int,
        ncols: int,
        figsize: Tuple[float, float] = (12, 8),
        title: Optional[str] = None
    ) -> Tuple[plt.Figure, np.ndarray]:
        """
        Create subplots with consistent styling.
        
        Args:
            nrows: Number of rows
            ncols: Number of columns
            figsize: Size of the figure
            title: Optional title for the figure
            
        Returns:
            Figure and axes array
        """
        fig, axes = plt.subplots(nrows, ncols, figsize=figsize)
        
        if title:
            fig.suptitle(title, fontsize=16, fontweight='bold', y=0.98)
            
        # Adjust spacing
        plt.tight_layout()
        
        return fig, axes
        
    def format_axis(
        self,
        ax: plt.Axes,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        title: Optional[str] = None,
        grid: bool = True,
        remove_spines: List[str] = ['top', 'right']
    ):
        """
        Format an axis with consistent styling.
        
        Args:
            ax: Matplotlib axes object
            xlabel: X-axis label
            ylabel: Y-axis label
            title: Axis title
            grid: Whether to show grid
            remove_spines: Which spines to remove
        """
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=12)
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=12)
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold', pad=10)
            
        # Grid settings
        if grid:
            ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
            
        # Remove spines
        for spine in remove_spines:
            ax.spines[spine].set_visible(False)
            
    def add_value_labels(
        self,
        ax: plt.Axes,
        bars: Any,
        format_string: str = '{:.1f}',
        offset: float = 0.02
    ):
        """
        Add value labels to bar chart.
        
        Args:
            ax: Matplotlib axes object
            bars: Bar container from ax.bar()
            format_string: Format string for values
            offset: Offset for label placement
        """
        for bar in bars:
            height = bar.get_height()
            if height != 0:  # Only label non-zero bars
                ax.annotate(
                    format_string.format(height),
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3 if height > 0 else -15),
                    textcoords="offset points",
                    ha='center',
                    va='bottom' if height > 0 else 'top',
                    fontsize=9
                )
                
    def truncate_labels(self, labels: List[str], max_length: int = 15) -> List[str]:
        """
        Truncate long labels for better display.
        
        Args:
            labels: List of label strings
            max_length: Maximum length before truncation
            
        Returns:
            List of truncated labels
        """
        return [
            label[:max_length] + '...' if len(str(label)) > max_length else str(label)
            for label in labels
        ]