import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from ncBacktester.metrics import MetricsCalculator


class TestMetricsCalculator:
    
    @pytest.fixture
    def sample_trades_df(self):
        return pd.DataFrame({
            'Entry_Date': pd.date_range('2023-01-01', periods=5, freq='D'),
            'Exit_Date': pd.date_range('2023-01-02', periods=5, freq='D'),
            'Entry_Price': [100, 105, 110, 95, 100],
            'Exit_Price': [110, 100, 115, 100, 105],
            'Quantity': [10, 10, 10, 10, 10],
            'P&L': [100, -50, 50, 50, 50],
            'Return_Pct': [0.10, -0.048, 0.045, 0.053, 0.05],
            'Commission': [1.1, 1.05, 1.15, 0.95, 1.0]
        })
    
    @pytest.fixture
    def sample_equity_curve(self):
        dates = pd.date_range(start='2023-01-01', periods=252, freq='D')
        # Create equity curve with 10% annual return (approximately)
        initial_value = 10000
        daily_return = 0.10 / 252  # Annual return / trading days
        portfolio_values = [initial_value * (1 + daily_return) ** i for i in range(252)]
        
        return pd.DataFrame({
            'Date': dates,
            'Portfolio_Value': portfolio_values,
            'Cash': [0] * 252,
            'Position_Value': portfolio_values,
            'Hold_Signal': [1] * 252
        })
    
    def test_sharpe_ratio_calculation(self, sample_trades_df, sample_equity_curve):
        
        calculator = MetricsCalculator(
            sample_trades_df,
            sample_equity_curve,
            initial_capital=10000
        )
        
        sharpe = calculator.calculate_sharpe_ratio()
        
        assert isinstance(sharpe, (int, float))
        assert not np.isnan(sharpe)
        assert sharpe > 0  # Should be positive for positive returns
    
    def test_sortino_ratio_calculation(self, sample_trades_df, sample_equity_curve):
       
        calculator = MetricsCalculator(
            sample_trades_df,
            sample_equity_curve,
            initial_capital=10000
        )
        
        sortino = calculator.calculate_sortino_ratio()
        sharpe = calculator.calculate_sharpe_ratio()
        
        assert isinstance(sortino, (int, float))
        assert not np.isnan(sortino)
        assert sortino >= sharpe  # Sortino should be >= Sharpe
    
    def test_annualized_return_calculation(self, sample_trades_df, sample_equity_curve):
        
        calculator = MetricsCalculator(
            sample_trades_df,
            sample_equity_curve,
            initial_capital=10000
        )
        
        annual_return = calculator.calculate_annualized_return()
        
        assert isinstance(annual_return, (int, float))
        assert not np.isnan(annual_return)
        # For the sample data with ~10% daily return, annualized should be positive
        assert annual_return > 0
    
    def test_max_drawdown_calculation(self, sample_trades_df, sample_equity_curve):
      
        calculator = MetricsCalculator(
            sample_trades_df,
            sample_equity_curve,
            initial_capital=10000
        )
        
        max_dd = calculator.calculate_max_drawdown()
        
        assert isinstance(max_dd, (int, float))
        assert 0 <= max_dd <= 1  # Drawdown should be between 0 and 100%
    
    def test_max_drawdown_with_known_data(self):
       
        # Create equity curve with known drawdown
        dates = pd.date_range('2023-01-01', periods=10, freq='D')
        # Peak at 10000, drops to 8000 (20% drawdown), recovers
        portfolio_values = [9000, 9500, 10000, 9800, 8500, 8000, 8200, 8800, 9200, 9500]
        
        equity_curve = pd.DataFrame({
            'Date': dates,
            'Portfolio_Value': portfolio_values,
            'Cash': [0] * 10,
            'Position_Value': portfolio_values,
            'Hold_Signal': [1] * 10
        })
        
        trades_df = pd.DataFrame({
            'Entry_Date': [dates[0]],
            'Exit_Date': [dates[-1]],
            'Entry_Price': [100],
            'Exit_Price': [105],
            'Quantity': [100],
            'P&L': [500],
            'Return_Pct': [0.05],
            'Commission': [1]
        })
        
        calculator = MetricsCalculator(trades_df, equity_curve, initial_capital=9000)
        max_dd = calculator.calculate_max_drawdown()
        
        assert abs(max_dd - 0.20) < 0.05, f"Expected ~0.20, got {max_dd}"
    
    def test_total_return_calculation(self, sample_trades_df, sample_equity_curve):
       
        calculator = MetricsCalculator(
            sample_trades_df,
            sample_equity_curve,
            initial_capital=10000
        )
        
        total_return = calculator.calculate_total_return()
        
        assert isinstance(total_return, (int, float))
        assert total_return > 0
    
    def test_trade_statistics(self, sample_trades_df, sample_equity_curve):
        
        calculator = MetricsCalculator(
            sample_trades_df,
            sample_equity_curve,
            initial_capital=10000
        )
        
        stats = calculator.calculate_trade_statistics()
        
        assert 'total_trades' in stats
        assert 'winning_trades' in stats
        assert 'losing_trades' in stats
        assert 'win_rate' in stats
        
        assert stats['total_trades'] == len(sample_trades_df)
        assert stats['winning_trades'] + stats['losing_trades'] == stats['total_trades']
        assert 0 <= stats['win_rate'] <= 1
    
    def test_alpha_beta_optional(self, sample_trades_df, sample_equity_curve):
        
        calculator = MetricsCalculator(
            sample_trades_df,
            sample_equity_curve,
            initial_capital=10000
        )
        
        beta = calculator.calculate_beta(benchmark_returns=None)
        alpha = calculator.calculate_alpha(benchmark_returns=None)
        
        assert beta is not None or np.isnan(beta)
        assert alpha is not None or np.isnan(alpha)
    
    def test_calculate_all_metrics(self, sample_trades_df, sample_equity_curve):
       
        calculator = MetricsCalculator(
            sample_trades_df,
            sample_equity_curve,
            initial_capital=10000
        )
        
        metrics = calculator.calculate_all_metrics()
        
        required_metrics = [
            'sharpe_ratio', 'sortino_ratio', 'annualized_return',
            'alpha', 'beta', 'max_drawdown', 'total_return',
            'total_trades', 'winning_trades', 'losing_trades', 'win_rate'
        ]
        
        for metric in required_metrics:
            assert metric in metrics, f"Missing metric: {metric}"
            assert metrics[metric] is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

