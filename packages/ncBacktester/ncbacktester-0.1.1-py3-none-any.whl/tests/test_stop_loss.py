import pytest
from ncBacktester.stop_loss import StopLossManager


class TestStopLossManager:
    
    def test_fixed_stop_loss_trigger(self):
        manager = StopLossManager(stop_loss_pct=0.05)  # 5% stop loss
        
        entry_price = 100.0
        current_price = 94.0  # 6% drop - should trigger
        
        should_trigger, stop_price = manager.check_stop_loss(
            entry_price=entry_price,
            current_price=current_price,
            highest_price_since_entry=100.0
        )
        
        assert should_trigger is True
        assert stop_price == entry_price * (1 - 0.05)  # Should be 95.0
    
    def test_fixed_stop_loss_no_trigger(self):
        
        manager = StopLossManager(stop_loss_pct=0.05)  # 5% stop loss
        
        entry_price = 100.0
        current_price = 96.0  # 4% drop - should NOT trigger
        
        should_trigger, stop_price = manager.check_stop_loss(
            entry_price=entry_price,
            current_price=current_price,
            highest_price_since_entry=100.0
        )
        
        assert should_trigger is False
    
    def test_trailing_stop_loss_trigger(self):
        
        manager = StopLossManager(trailing_stop_pct=0.05)  # 5% trailing stop
        
        entry_price = 100.0
        highest_price = 110.0  # Price went up 10%
        current_price = 104.0  # Dropped 5.45% from high (should trigger at 104.5)
        
        should_trigger, stop_price = manager.check_stop_loss(
            entry_price=entry_price,
            current_price=current_price,
            highest_price_since_entry=highest_price
        )
        
        assert should_trigger is True
        assert stop_price == highest_price * (1 - 0.05)  # Should be 104.5
    
    def test_trailing_stop_loss_no_trigger(self):
        
        manager = StopLossManager(trailing_stop_pct=0.05)
        
        entry_price = 100.0
        highest_price = 110.0
        current_price = 106.0  # Only 3.6% down from high - should NOT trigger
        
        should_trigger, stop_price = manager.check_stop_loss(
            entry_price=entry_price,
            current_price=current_price,
            highest_price_since_entry=highest_price
        )
        
        assert should_trigger is False
    
    def test_both_stops_more_restrictive(self):
        
        manager = StopLossManager(
            stop_loss_pct=0.05,  # Fixed: 95.0
            trailing_stop_pct=0.03  # Trailing from 110: 106.7
        )
        
        entry_price = 100.0
        highest_price = 110.0
        current_price = 104.0  # Below trailing stop (106.7)
        
        should_trigger, stop_price = manager.check_stop_loss(
            entry_price=entry_price,
            current_price=current_price,
            highest_price_since_entry=highest_price
        )
        
        # Should use trailing stop (106.7) since it's more restrictive
        assert should_trigger is True
        assert stop_price == highest_price * (1 - 0.03)  # 106.7
    
    def test_no_stop_loss_configured(self):
        
        manager = StopLossManager(stop_loss_pct=None, trailing_stop_pct=None)
        
        should_trigger, stop_price = manager.check_stop_loss(
            entry_price=100.0,
            current_price=50.0,  # Big drop
            highest_price_since_entry=100.0
        )
        
        assert should_trigger is False
    
    def test_stop_loss_calculation_accuracy(self):
        
        manager = StopLossManager(stop_loss_pct=0.10)  # 10% stop
        
        entry_price = 100.0
        stop_price = manager._calculate_fixed_stop_price(entry_price)
        
        assert stop_price == 90.0  # Exactly 10% below entry
    
    def test_trailing_stop_calculation_accuracy(self):
        
        manager = StopLossManager(trailing_stop_pct=0.08)  # 8% trailing stop
        
        highest_price = 120.0
        trailing_stop = manager._calculate_trailing_stop_price(highest_price)
        
        assert trailing_stop == 110.4  # Exactly 8% below highest


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

