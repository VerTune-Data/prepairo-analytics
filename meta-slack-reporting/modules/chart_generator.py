"""
Chart generation for Meta Ads reports
Supports emoji bar charts and PNG images
"""

import logging
from typing import List, Dict
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server
import matplotlib.pyplot as plt
import numpy as np

logger = logging.getLogger(__name__)


class ChartGenerator:
    """Generate emoji and PNG charts for Meta Ads data"""
    
    def generate_emoji_chart(self, data: List[Dict], metric: str = 'spend', max_items: int = 10) -> str:
        """
        Generate Unicode bar chart with trend indicators
        """
        if not data:
            return "No data available"
        
        try:
            top_items = data[:max_items]
            if not top_items:
                return "No data available"
            
            max_val = max(item.get(metric, 0) for item in top_items)
            if max_val == 0:
                return "No data available"
            
            lines = []
            for item in top_items:
                name = item.get('name', 'Unknown')[:30]
                value = item.get(metric, 0)
                
                pct = (value / max_val) * 100
                filled = int(pct / 10)
                empty = 10 - filled
                bar = '█' * filled + '░' * empty
                
                delta_key = f'delta_{metric}'
                delta_info = item.get(delta_key, {})
                delta_pct = delta_info.get('percent', 0)
                
                trend = self.get_trend_indicator(delta_pct)
                
                if metric == 'spend':
                    value_str = f"₹{value:,.0f}"
                else:
                    value_str = f"{int(value):,}"
                
                if abs(delta_pct) > 1:
                    line = f"{name:30s} {bar} {pct:3.0f}% ({value_str}) {trend} {abs(delta_pct):.0f}%"
                else:
                    line = f"{name:30s} {bar} {pct:3.0f}% ({value_str}) {trend}"
                
                lines.append(line)
            
            return "\\n".join(lines)
        
        except Exception as e:
            logger.error(f"Error generating emoji chart: {e}")
            return f"Error generating chart: {e}"
    
    def get_trend_indicator(self, delta_pct: float) -> str:
        """Get trend arrow based on percentage change"""
        if abs(delta_pct) < 1:
            return "→"
        elif delta_pct > 0:
            return "↑"
        else:
            return "↓"
    
    def generate_png_bar_chart(self, data: List[Dict], title: str, output_path: str, metric: str = 'spend') -> None:
        """
        Generate horizontal bar chart PNG
        Shows top 10 campaigns with proper labels
        """
        try:
            if not data:
                logger.warning("No data to generate chart")
                return
            
            # Get top 10 items
            top_data = data[:10]
            
            # Extract data
            names = [item.get('name', 'Unknown')[:25] for item in top_data]
            values = [float(item.get(metric, 0)) for item in top_data]
            
            # Reverse for top-to-bottom display
            names = names[::-1]
            values = values[::-1]
            
            # Create figure
            fig, ax = plt.subplots(figsize=(12, max(6, len(names) * 0.5)))
            
            # Color gradient based on value
            colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(values)))
            
            # Create horizontal bar chart
            y_pos = np.arange(len(names))
            bars = ax.barh(y_pos, values, color=colors, edgecolor='black', linewidth=0.5)
            
            # Customize
            ax.set_yticks(y_pos)
            ax.set_yticklabels(names, fontsize=10)
            ax.set_xlabel('Spend (₹)', fontsize=12, fontweight='bold')
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            
            # Add value labels on bars
            for i, (bar, value) in enumerate(zip(bars, values)):
                width = bar.get_width()
                ax.text(width, bar.get_y() + bar.get_height()/2,
                       f' ₹{value:,.0f}',
                       ha='left', va='center', fontsize=9, fontweight='bold')
            
            # Grid
            ax.grid(axis='x', alpha=0.3, linestyle='--')
            ax.set_axisbelow(True)
            
            # Tight layout
            plt.tight_layout()
            
            # Save
            plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()
            
            logger.info(f"PNG chart saved to {output_path}")
            
        except Exception as e:
            logger.error(f"Error generating PNG chart: {e}", exc_info=True)
