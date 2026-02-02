from typing import Optional
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter


class Plotter:
    
    def __init__(
        self,
        data: pd.DataFrame,
        trades_df: pd.DataFrame,
        equity_curve: pd.DataFrame,
        metrics: dict
    ):

        self.data = data.copy()
        self.trades_df = trades_df.copy()
        self.equity_curve = equity_curve.copy()
        self.metrics = metrics
    
    def plot_all(self, save_path: Optional[str] = None):
        
        fig, axes = plt.subplots(
            nrows=3, 
            ncols=1, 
            figsize=(15, 20), 
            sharex=True,
            gridspec_kw={'height_ratios': [2, 1, 1]} # Give price chart more space
        )
        
        self.plot_price_with_trades(ax=axes[0])
        
        self.plot_equity_curve(ax=axes[1])
        
        self.plot_drawdown(ax=axes[2])
        
        total_return = self.metrics.get('Total Return', 0)
        sharpe = self.metrics.get('Sharpe Ratio', 0)
        max_dd = self.metrics.get('Max Drawdown', 0)
        win_rate = self.metrics.get('Win Rate', 0)
        
        title_str = (
            f"Backtest Results\n"
            f"Total Return: {total_return:.2%} | "
            f"Sharpe Ratio: {sharpe:.2f} | "
            f"Max Drawdown: {max_dd:.2%} | "
            f"Win Rate: {win_rate:.2%}"
        )
        fig.suptitle(title_str, fontsize=16, y=1.0) # y > 1 to avoid overlap
        
        fig.tight_layout(rect=[0, 0.03, 1, 0.96]) # rect to make room for suptitle
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Plot saved to {save_path}")
            plt.close(fig) # Close figure to free memory
        else:
            plt.show()
    
    def plot_price_with_trades(self, ax: Optional[plt.Axes] = None):
        
        if ax is None:
            fig, ax = plt.subplots(figsize=(15, 7))
            
        ax.plot(self.data.index, self.data['Close'], label='Close Price', color='blue', alpha=0.7)
        
        buys = self.trades_df
        ax.scatter(
            buys['Entry_Date'], 
            buys['Entry_Price'], 
            color='green', 
            marker='^', 
            s=60, 
            label='Buy', 
            zorder=5 # Plot on top
        )
        
        sells = self.trades_df
        ax.scatter(
            sells['Exit_Date'], 
            sells['Exit_Price'], 
            color='red', 
            marker='v', 
            s=60, 
            label='Sell', 
            zorder=5 # Plot on top
        )
        
        ax.set_title('Price Chart with Trades')
        ax.set_ylabel('Price')
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.5)
        
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        
        return ax
    
    def plot_equity_curve(self, ax: Optional[plt.Axes] = None):
        
        if ax is None:
            fig, ax = plt.subplots(figsize=(15, 7))
        
        ax.plot(
            self.equity_curve.index, 
            self.equity_curve['Portfolio_Value'], 
            label='Equity Curve', 
            color='purple'
        )
        
        initial_capital = self.equity_curve['Portfolio_Value'].iloc[0]
        ax.axhline(
            y=initial_capital, 
            color='grey', 
            linestyle='--', 
            label=f'Initial Capital (${initial_capital:,.2f})'
        )
        
        ax.set_title('Portfolio Equity Curve')
        ax.set_ylabel('Portfolio Value ($)')
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.5)
        
        ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f'${y:,.0f}'))
        
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        
        return ax
    
    def plot_drawdown(self, ax: Optional[plt.Axes] = None):
        
        if ax is None:
            fig, ax = plt.subplots(figsize=(15, 7))
            
        equity = self.equity_curve['Portfolio_Value']
        # Calculate running peak (cumulative max)
        peak = equity.expanding(min_periods=1).max()
        # Calculate drawdown (as a positive percentage)
        drawdown = (peak - equity) / peak
        
        ax.fill_between(drawdown.index, 0, drawdown, color='red', alpha=0.3)
        # Add a line plot for clarity
        ax.plot(drawdown.index, drawdown, color='red', alpha=0.7, label='Drawdown')
        
        max_dd_val = self.metrics.get('Max Drawdown', drawdown.max())
        ax.set_title(f'Portfolio Drawdown (Max: {max_dd_val:.2%})')
        ax.set_ylabel('Drawdown')
        ax.set_xlabel('Date')
        
        ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f'{y:.0%}'))
        ax.set_ylim(bottom=0) # Ensure y-axis starts at 0
        
        ax.grid(True, linestyle='--', alpha=0.5)
        
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))

        return ax
    
    def plot_metrics_summary(self, ax: Optional[plt.Axes] = None):
        
        if ax is None:
            fig, ax = plt.subplots(figsize=(8, 6))

        # Turn off axes
        ax.axis('off')
        
        # Build metrics string
        metrics_str = "Backtest Metrics Summary\n"
        metrics_str += "-" * 26 + "\n\n"
        
        for key, value in self.metrics.items():
            if isinstance(value, float):
                # Format percentages and floats differently
                if "Return" in key or "Drawdown" in key or "Rate" in key:
                    metrics_str += f"{key:<18}: {value: >8.2%}\n"
                else:
                    metrics_str += f"{key:<18}: {value: >8.2f}\n"
            else:
                metrics_str += f"{key:<18}: {str(value): >8}\n"

        ax.text(
            0.05, 0.95, 
            metrics_str, 
            va='top', 
            ha='left', 
            fontsize=12, 
            family='monospace' 
        )
        
        return ax

