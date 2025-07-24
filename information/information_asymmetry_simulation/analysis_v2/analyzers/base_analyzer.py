"""
Base Analyzer Class

Abstract base class for all analyzers providing common functionality
and enforcing consistent interfaces.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd
from ..core import EventProcessor, MetricsCalculator


class BaseAnalyzer(ABC):
    """Abstract base class for all analyzers"""
    
    def __init__(self, event_processor: EventProcessor):
        """
        Initialize the analyzer.
        
        Args:
            event_processor: Processed event data
        """
        self.processor = event_processor
        self.metrics_calc = MetricsCalculator()
        self._results = None
        
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this analyzer"""
        pass
        
    @abstractmethod
    def analyze(self) -> Dict[str, Any]:
        """
        Perform the analysis.
        
        Returns:
            Dictionary containing analysis results
        """
        pass
        
    @abstractmethod
    def get_metrics(self) -> Dict[str, float]:
        """
        Get key metrics from this analysis.
        
        Returns:
            Dictionary of metric names to values
        """
        pass
        
    def get_results(self) -> Dict[str, Any]:
        """Get cached results or perform analysis"""
        if self._results is None:
            self._results = self.analyze()
        return self._results
        
    def get_summary(self) -> str:
        """
        Get a text summary of the analysis results.
        
        Returns:
            Formatted string summary
        """
        results = self.get_results()
        metrics = self.get_metrics()
        
        summary_lines = [
            f"\n{self.name} Analysis Summary",
            "=" * (len(self.name) + 18),
            ""
        ]
        
        # Add metrics
        if metrics:
            summary_lines.append("Key Metrics:")
            for metric, value in metrics.items():
                if isinstance(value, float):
                    summary_lines.append(f"  - {metric}: {value:.3f}")
                else:
                    summary_lines.append(f"  - {metric}: {value}")
            summary_lines.append("")
            
        # Add any additional summary info from results
        if 'summary' in results:
            summary_lines.append("Summary:")
            summary_lines.append(results['summary'])
            
        return "\n".join(summary_lines)
        
    def export_results(self, format: str = 'dict') -> Any:
        """
        Export results in specified format.
        
        Args:
            format: Output format ('dict', 'json', 'dataframe')
            
        Returns:
            Results in requested format
        """
        results = self.get_results()
        
        if format == 'dict':
            return results
        elif format == 'json':
            import json
            return json.dumps(results, indent=2, default=str)
        elif format == 'dataframe':
            # Convert results to DataFrame where applicable
            dfs = {}
            for key, value in results.items():
                if isinstance(value, pd.DataFrame):
                    dfs[key] = value
                elif isinstance(value, dict) and all(isinstance(v, (int, float, str)) for v in value.values()):
                    dfs[key] = pd.DataFrame([value])
                    
            return dfs
        else:
            raise ValueError(f"Unsupported format: {format}")
            
    def _safe_divide(self, numerator: float, denominator: float, default: float = 0.0) -> float:
        """Safely divide two numbers, returning default if denominator is zero"""
        return numerator / denominator if denominator != 0 else default