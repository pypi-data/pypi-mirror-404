import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from ncBacktester.strategy_executor import StrategyExecutor


class TestStrategyExecutor:
    
    @pytest.fixture
    def sample_data(self):
        """Create sample OHLCV data with hold signals."""
        dates = pd.date_range(start='2023-01-01', periods=20, freq='D')
        data = pd.DataFrame({
            'Date': dates,
            'Open': np.random.uniform(100, 110, 20),
            'High': np.random.uniform(105, 115, 20),
            'Low': np.random.uniform(95, 105, 20),
            'Close': np.random.uniform(100, 110, 20),
            'Volume': np.random.randint(1000, 5000, 20),
            'Hold_Signal': [0, 0, 1, 1, 1, 0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0]
        })
        return data
    
    def test_buy_signal_detection(self, sample_data):
        
        executor = StrategyExecutor(sample_data, initial_capital=10000)
        
        # Test buy signal
        assert executor._detect_signal_change(1, 0) == 'buy'
        assert executor._detect_signal_change(0, 0) is None
        assert executor._detect_signal_change(1, 1) is None
    
    def test_sell_signal_detection(self, sample_data):
       
        executor = StrategyExecutor(sample_data, initial_capital=10000)
        
        # Test sell signal
        assert executor._detect_signal_change(0, 1) == 'sell'
        assert executor._detect_signal_change(1, 1) is None
        assert executor._detect_signal_change(0, 0) is None
    
    def test_execute_buy(self, sample_data):
        
        executor = StrategyExecutor(sample_data, initial_capital=10000, commission=0.001)
        
        buy_result = executor._execute_buy(price=100.0, date=sample_data['Date'].iloc[0])
        
        assert buy_result['success'] is True
        assert buy_result['quantity'] > 0
        assert buy_result['price'] == 100.0
        assert executor.current_position == buy_result['quantity']
        assert executor.current_capital < 10000  # Should have decreased
        
        # Verify total cost (including commission)
        expected_cost = buy_result['quantity'] * 100.0 * (1 + 0.001)
        assert abs(executor.current_capital - (10000 - expected_cost)) < 0.01
    
    def test_execute_sell(self, sample_data):
        
        executor = StrategyExecutor(sample_data, initial_capital=10000, commission=0.001)
        
        # First buy a position
        executor._execute_buy(price=100.0, date=sample_data['Date'].iloc[0])
        initial_position = executor.current_position
        initial_capital = executor.current_capital
        
        # Then sell
        sell_result = executor._execute_sell(price=110.0, date=sample_data['Date'].iloc[1])
        
        assert sell_result is not None
        assert sell_result['quantity'] == initial_position
        assert sell_result['p&l'] > 0  # Profit if selling higher
        assert executor.current_position == 0
        assert executor.current_capital > initial_capital  # Should have increased
    
    def test_full_execution(self, sample_data):
       
        executor = StrategyExecutor(sample_data, initial_capital=10000, commission=0.001)
        
        trades_df, equity_curve = executor.execute()
        
        # Verify trades_df structure
        assert isinstance(trades_df, pd.DataFrame)
        required_cols = ['Entry_Date', 'Exit_Date', 'Entry_Price', 'Exit_Price', 
                        'Quantity', 'P&L', 'Return_Pct', 'Commission']
        for col in required_cols:
            assert col in trades_df.columns, f"Missing column: {col}"
        
        # Verify equity_curve structure
        assert isinstance(equity_curve, pd.DataFrame)
        required_cols = ['Date', 'Portfolio_Value', 'Cash', 'Position_Value', 'Hold_Signal']
        for col in required_cols:
            assert col in equity_curve.columns, f"Missing column: {col}"
        
        # Verify we have trades when signals change
        # Signal changes: 0->1 at index 2, 1->0 at index 5, 0->1 at index 7, etc.
        assert len(trades_df) > 0, "Should have executed some trades"
    
    def test_capital_management(self, sample_data):
        
        executor = StrategyExecutor(sample_data, initial_capital=1000, commission=0.0)
        
        # Try to buy with limited capital
        buy_result = executor._execute_buy(price=100.0, date=sample_data['Date'].iloc[0])
        
        # Should not be able to buy more shares than capital allows
        total_cost = buy_result['quantity'] * 100.0
        assert total_cost <= executor.initial_capital
    
    def test_no_duplicate_positions(self, sample_data):
        
        executor = StrategyExecutor(sample_data, initial_capital=10000, commission=0.001)
        
        # Execute first buy
        executor._execute_buy(price=100.0, date=sample_data['Date'].iloc[0])
        first_position = executor.current_position
        
        # Execute second buy (should either add to position or skip)
        executor._execute_buy(price=105.0, date=sample_data['Date'].iloc[1])
        
        assert executor.current_position >= first_position


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

