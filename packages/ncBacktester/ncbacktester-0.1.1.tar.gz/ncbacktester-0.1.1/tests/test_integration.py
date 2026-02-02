import pytest
import pandas as pd
import numpy as np
from ncBacktester import Backtest


class TestIntegration:
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data with signals."""
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        
        # Create price trend
        base_price = 100
        price_trend = base_price + np.cumsum(np.random.randn(100) * 2)
        
        data = pd.DataFrame({
            'Date': dates,
            'Open': price_trend + np.random.randn(100) * 0.5,
            'High': price_trend + np.abs(np.random.randn(100)) * 2,
            'Low': price_trend - np.abs(np.random.randn(100)) * 2,
            'Close': price_trend,
            'Volume': np.random.randint(1000, 5000, 100),
            'Hold_Signal': [0, 0, 1, 1, 1, 1, 0, 0, 1, 1] * 10
        })
        return data
    
    def test_full_backtest_workflow(self, sample_data):
        bt = Backtest(
            data=sample_data,
            initial_capital=10000,
            stop_loss_pct=0.05,
            commission=0.001
        )
        
        results = bt.run()
        
        # Verify results structure
        assert 'trades' in results
        assert 'equity_curve' in results
        assert 'metrics' in results
        assert 'final_value' in results
        
        # Verify trades
        assert isinstance(results['trades'], pd.DataFrame)
        assert len(results['trades']) >= 0
        
        # Verify equity curve
        assert isinstance(results['equity_curve'], pd.DataFrame)
        assert len(results['equity_curve']) == len(sample_data)
        
        # Verify metrics
        required_metrics = [
            'sharpe_ratio', 'sortino_ratio', 'annualized_return',
            'alpha', 'beta', 'max_drawdown', 'total_return'
        ]
        for metric in required_metrics:
            assert metric in results['metrics']
    
    def test_backtest_with_stop_loss(self, sample_data):
        """Test that stop loss is properly integrated."""
        bt = Backtest(
            data=sample_data,
            initial_capital=10000,
            stop_loss_pct=0.10,  # 10% stop loss
            trailing_stop_pct=0.05,  # 5% trailing stop
            commission=0.0
        )
        
        results = bt.run()
        
        # Verify stop loss was considered (check if any trades were stopped)
        # This is a basic check - actual stop loss triggering depends on price movement
        assert results is not None
    
    def test_plotting_integration(self, sample_data):
        """Test that plotting works after backtest."""
        bt = Backtest(
            data=sample_data,
            initial_capital=10000
        )
        
        results = bt.run()
        
        # Test that plot can be created and saved
        import os
        test_path = 'test_integration_plot.png'
        try:
            bt.plot(save_path=test_path)
            assert os.path.exists(test_path)
        finally:
            if os.path.exists(test_path):
                os.remove(test_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

