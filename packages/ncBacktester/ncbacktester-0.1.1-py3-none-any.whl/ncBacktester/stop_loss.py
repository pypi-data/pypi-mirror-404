from typing import Optional, Tuple


class StopLossManager:
    
    def __init__(
        self,
        stop_loss_pct: Optional[float] = None,
        trailing_stop_pct: Optional[float] = None
    ):
    
        self.stop_loss_pct = stop_loss_pct
        self.trailing_stop_pct = trailing_stop_pct
    
    def check_stop_loss(
        self,
        entry_price: float,
        current_price: float,
        highest_price_since_entry: float
    ) -> Tuple[bool, float]:
        
        fixed_stop = self._calculate_fixed_stop_price(entry_price)
        trailing_stop = self._calculate_trailing_stop_price(highest_price_since_entry)
        
        active_stops = []
        if fixed_stop is not None:
            active_stops.append(fixed_stop)
        if trailing_stop is not None:
            active_stops.append(trailing_stop)

        if not active_stops:
            # No stop loss is active
            return (False, 0.0)
            
        # The effective stop loss is the most restrictive (highest) price
        effective_stop_price = max(active_stops)
        
        # Check if the current price is at or below the stop level
        should_trigger = current_price <= effective_stop_price
        
        return (should_trigger, effective_stop_price)
    
    def _calculate_fixed_stop_price(self, entry_price: float) -> Optional[float]:
        
        if self.stop_loss_pct is None:
            return None
        return entry_price * (1.0 - self.stop_loss_pct)
        
    
    def _calculate_trailing_stop_price(
        self,
        highest_price: float
    ) -> Optional[float]:
        
        if self.trailing_stop_pct is None:
            return None
        return highest_price * (1.0 - self.trailing_stop_pct)
        

