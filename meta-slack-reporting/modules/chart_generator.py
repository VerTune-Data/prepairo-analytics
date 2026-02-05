"""
Chart generation for Meta Ads reports
Supports emoji bar charts and PNG images
"""

import logging
from typing import List, Dict
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


class ChartGenerator:
    """Generate emoji and PNG charts for Meta Ads data"""
    
    def generate_emoji_chart(self, data: List[Dict], metric: str = 'spend', max_items: int = 10) -> str:
        """
        Generate Unicode bar chart with trend indicators
        Example:
        Campaign A: ████████░░ 80% (₹8,000) ↑ 25%
        Campaign B: ██████░░░░ 60% (₹6,000) ↓ 15%
        """
        if not data:
            return "No data available"
        
        try:
            # Get top items by metric
            top_items = data[:max_items]
            if not top_items:
                return "No data available"
            
            # Find max value for normalization
            max_val = max(item.get(metric, 0) for item in top_items)
            if max_val == 0:
                return "No data available"
            
            lines = []
            for item in top_items:
                name = item.get('name', 'Unknown')[:30]
                value = item.get(metric, 0)
                
                # Calculate percentage of max
                pct = (value / max_val) * 100
                
                # Create bar (10 blocks total)
                filled = int(pct / 10)
                empty = 10 - filled
                bar = '█' * filled + '░' * empty
                
                # Get delta information
                delta_key = f'delta_{metric}'
                delta_info = item.get(delta_key, {})
                delta_pct = delta_info.get('percent', 0)
                
                # Get trend indicator
                trend = self.get_trend_indicator(delta_pct)
                
                # Format value
                if metric == 'spend':
                    value_str = f"₹{value:,.0f}"
                else:
                    value_str = f"{int(value):,}"
                
                # Build line
                if abs(delta_pct) > 1:  # Only show delta if > 1%
                    line = f"{name:30s} {bar} {pct:3.0f}% ({value_str}) {trend} {abs(delta_pct):.0f}%"
                else:
                    line = f"{name:30s} {bar} {pct:3.0f}% ({value_str}) {trend}"
                
                lines.append(line)
            
            return "\n".join(lines)
        
        except Exception as e:
            logger.error(f"Error generating emoji chart: {e}")
            return f"Error generating chart: {e}"
    
    def get_trend_indicator(self, delta_pct: float) -> str:
        """Return trend indicator based on delta percentage"""
        if delta_pct > 5:
            return "↑"
        elif delta_pct < -5:
            return "↓"
        else:
            return "→"
    
    def generate_png_bar_chart(self, data: List[Dict], title: str, output_path: str, metric: str = 'spend', max_items: int = 10):
        """
        Generate PNG horizontal bar chart
        Green for positive deltas, red for negative
        """
        try:
            # Get top items
            top_items = data[:max_items]
            if not top_items:
                logger.warning("No data to generate PNG chart")
                return
            
            # Extract data
            names = [item.get('name', 'Unknown')[:25] for item in top_items]
            values = [item.get(metric, 0) for item in top_items]
            
            # Get delta percentages for coloring
            delta_key = f'delta_{metric}'
            deltas = [item.get(delta_key, {}).get('percent', 0) for item in top_items]
            
            # Assign colors based on delta
            colors = []
            for delta in deltas:
                if delta > 5:
                    colors.append('#00D856')  # Green for increase
                elif delta < -5:
                    colors.append('#FF4444')  # Red for decrease
                else:
                    colors.append('#4A90E2')  # Blue for stable
            
            # Create figure
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Create horizontal bar chart
            y_pos = range(len(names))
            ax.barh(y_pos, values, color=colors, alpha=0.8)
            
            # Customize
            ax.set_yticks(y_pos)
            ax.set_yticklabels(names, fontsize=10)
            ax.set_xlabel(f'{metric.capitalize()} (₹)' if metric == 'spend' else metric.capitalize(), fontsize=12)
            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.grid(axis='x', alpha=0.3)
            
            # Invert y-axis so highest is on top
            ax.invert_yaxis()
            
            # Add value labels on bars
            for i, (value, delta) in enumerate(zip(values, deltas)):
                if metric == 'spend':
                    label = f'₹{value:,.0f}'
                else:
                    label = f'{int(value):,}'
                
                # Add delta if significant
                if abs(delta) > 1:
                    label += f' ({delta:+.0f}%)'
                
                ax.text(value, i, f' {label}', va='center', fontsize=9)
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()
            
            logger.info(f"PNG chart saved to {output_path}")
        
        except Exception as e:
            logger.error(f"Error generating PNG chart: {e}")
    
    def format_comparison_table(self, data: List[Dict], max_items: int = 10) -> str:
        """Format data as markdown comparison table"""
        if not data:
            return "No data available"
        
        try:
            lines = ["```"]
            lines.append(f"{'Campaign':<35} {'Spend':>12} {'Change':>10}")
            lines.append("-" * 60)
            
            for item in data[:max_items]:
                name = item.get('name', 'Unknown')[:33]
                spend = item.get('spend', 0)
                delta_pct = item.get('delta_spend', {}).get('percent', 0)
                
                trend = self.get_trend_indicator(delta_pct)
                delta_str = f"{trend} {abs(delta_pct):>5.1f}%" if abs(delta_pct) > 1 else "→ stable"
                
                lines.append(f"{name:<35} ₹{spend:>10,.0f} {delta_str:>10}")
            
            lines.append("```")
            return "\n".join(lines)
        
        except Exception as e:
            logger.error(f"Error generating comparison table: {e}")
            return f"Error generating table: {e}"
