import pytest
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

from ncBacktester.plotter import Plotter


class TestPlotter:
    
    @pytest.fixture
    def sample_data(self):
        """Create sample OHLCV data."""
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        return pd.DataFrame({
            'Date': dates,
            'Open': np.random.uniform(100, 110, 100),
            'High': np.random.uniform(105, 115, 100),
            'Low': np.random.uniform(95, 105, 100),
            'Close': np.random.uniform(100, 110, 100),
            'Volume': np.random.randint(1000, 5000, 100),
            'Hold_Signal': np.random.choice([0, 1], 100)
        })
    
    @pytest.fixture
    def sample_trades_df(self):
        """Create sample trades DataFrame."""
        return pd.DataFrame({
            'Entry_Date': pd.date_range('2023-01-05', periods=5, freq='10D'),
            'Exit_Date': pd.date_range('2023-01-10', periods=5, freq='10D'),
            'Entry_Price': [100, 105, 110, 95, 100],
            'Exit_Price': [110, 100, 115, 100, 105],
            'Quantity': [10, 10, 10, 10, 10],
            'P&L': [100, -50, 50, 50, 50],
            'Return_Pct': [0.10, -0.048, 0.045, 0.053, 0.05],
            'Commission': [1.1, 1.05, 1.15, 0.95, 1.0]
        })
    
    @pytest.fixture
    def sample_equity_curve(self):
        """Create sample equity curve."""
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        return pd.DataFrame({
            'Date': dates,
            'Portfolio_Value': np.linspace(10000, 12000, 100),
            'Cash': [0] * 100,
            'Position_Value': np.linspace(10000, 12000, 100),
            'Hold_Signal': [1] * 100
        })
    
    @pytest.fixture
    def sample_metrics(self):
        """Create sample metrics dictionary."""
        return {
            'sharpe_ratio': 1.5,
            'sortino_ratio': 2.0,
            'annualized_return': 0.15,
            'alpha': 0.02,
            'beta': 1.1,
            'max_drawdown': 0.10,
            'total_return': 0.20,
            'total_trades': 5,
            'winning_trades': 4,
            'losing_trades': 1,
            'win_rate': 0.8
        }
    
    def test_plotter_initialization(self, sample_data, sample_trades_df, 
                                   sample_equity_curve, sample_metrics):
        
        plotter = Plotter(
            sample_data,
            sample_trades_df,
            sample_equity_curve,
            sample_metrics
        )
        
        assert plotter.data is not None
        assert plotter.trades_df is not None
        assert plotter.equity_curve is not None
        assert plotter.metrics is not None
    
    def test_plot_all_creates_figure(self, sample_data, sample_trades_df,
                                     sample_equity_curve, sample_metrics):
        
        plotter = Plotter(
            sample_data,
            sample_trades_df,
            sample_equity_curve,
            sample_metrics
        )
        
        # Test saving to file
        test_path = 'test_plot.png'
        try:
            plotter.plot_all(save_path=test_path)
            # Check that file was created
            assert os.path.exists(test_path), "Plot file should be created"
        finally:
            # Cleanup
            if os.path.exists(test_path):
                os.remove(test_path)
    
    def test_plot_price_with_trades(self, sample_data, sample_trades_df,
                                   sample_equity_curve, sample_metrics):
        
        plotter = Plotter(
            sample_data,
            sample_trades_df,
            sample_equity_curve,
            sample_metrics
        )
        
        ax = plotter.plot_price_with_trades()
        assert ax is not None
        plt.close()  # Clean up
    
    def test_plot_equity_curve(self, sample_data, sample_trades_df,
                              sample_equity_curve, sample_metrics):
        
        plotter = Plotter(
            sample_data,
            sample_trades_df,
            sample_equity_curve,
            sample_metrics
        )
        
        ax = plotter.plot_equity_curve()
        assert ax is not None
        plt.close()  # Clean up
    
    def test_plot_drawdown(self, sample_data, sample_trades_df,
                          sample_equity_curve, sample_metrics):
       
        plotter = Plotter(
            sample_data,
            sample_trades_df,
            sample_equity_curve,
            sample_metrics
        )
        
        ax = plotter.plot_drawdown()
        assert ax is not None
        plt.close()  # Clean up


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

