from typing import Optional, Dict, Any
import pandas as pd

from ncBacktester.strategy_executor import StrategyExecutor
from ncBacktester.metrics import MetricsCalculator
from ncBacktester.stop_loss import StopLossManager
from ncBacktester.plotter import Plotter


class Backtest:
    
    def __init__(
        self,
        data: pd.DataFrame,
        initial_capital: float = 10000.0,
        stop_loss_pct: Optional[float] = None,
        trailing_stop_pct: Optional[float] = None,
        commission: float = 0.0
    ):
        
        self.data = data.copy()
        self.initial_capital = initial_capital
        self.stop_loss_pct = stop_loss_pct
        self.trailing_stop_pct = trailing_stop_pct
        self.commission = commission
        
        self.strategy_executor = None
        self.stop_loss_manager = None
        self.metrics_calculator = None
        self.plotter = None
        
        self.trades_df = None
        self.equity_curve = None
        self.metrics = None
        
    def run(self) -> Dict[str, Any]:
        self._validate_data()
        
        self.stop_loss_manager = StopLossManager(
            stop_loss_pct=self.stop_loss_pct,
            trailing_stop_pct=self.trailing_stop_pct
        )
        
        self.strategy_executor = StrategyExecutor(
            data=self.data,
            initial_capital=self.initial_capital,
            commission=self.commission,
            stop_loss_manager=self.stop_loss_manager
        )
        
        self.trades_df, self.equity_curve = self.strategy_executor.execute()
        
        self.metrics_calculator = MetricsCalculator(
            trades_df=self.trades_df,
            equity_curve=self.equity_curve,
            initial_capital=self.initial_capital
        )
        self.metrics = self.metrics_calculator.calculate_all_metrics()
        
        self.plotter = Plotter(
            data=self.data,
            trades_df=self.trades_df,
            equity_curve=self.equity_curve,
            metrics=self.metrics
        )
        
        return {
            'trades': self.trades_df,
            'equity_curve': self.equity_curve,
            'metrics': self.metrics,
            'final_value': self.equity_curve['Portfolio_Value'].iloc[-1] if len(self.equity_curve) > 0 else self.initial_capital
        }
    
    def plot(self, save_path: Optional[str] = None):
        
        if self.plotter is None:
            raise ValueError("Must run backtest (call .run()) before plotting")
        
        self.plotter.plot_all(save_path=save_path)
    
    def _validate_data(self):
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume', 'Hold_Signal']
        missing_cols = [col for col in required_cols if col not in self.data.columns]
        
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        critical_cols = ['Close', 'Hold_Signal']
        for col in critical_cols:
            if self.data[col].isna().any():
                raise ValueError(f"Column '{col}' contains NaN values")

