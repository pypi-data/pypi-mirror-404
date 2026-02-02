from typing import Tuple, Optional
import pandas as pd
import numpy as np

from ncBacktester.stop_loss import StopLossManager


class StrategyExecutor:

    def __init__(
        self,
        data: pd.DataFrame,
        initial_capital: float,
        commission: float = 0.0,
        stop_loss_manager: Optional['StopLossManager'] = None
    ):
        
        self.data = data.copy()
        self.initial_capital = initial_capital
        self.commission = commission
        self.stop_loss_manager = stop_loss_manager
        
        # Internal state tracking
        self.current_capital = initial_capital
        self.current_position = 0  # Number of shares held
        self.entry_price = None  # Average entry price of current position
        self.entry_date = None
        self._highest_price_since_entry = None
        
    def execute(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        
        trades_list = []
        equity_snapshots_list = []

        num_rows = len(self.data)
        for idx in range(num_rows):
            row = self.data.iloc[idx]
            current_signal = int(row['Hold_Signal'])
            previous_signal = int(self.data['Hold_Signal'].iloc[idx - 1]) if idx > 0 else current_signal

            signal_change = self._detect_signal_change(current_signal, previous_signal)

            if signal_change == 'buy':
                self._execute_buy(price=float(row['Close']), date=row['Date'])
            elif signal_change == 'sell':
                sell_result = self._execute_sell(price=float(row['Close']), date=row['Date'])
                if sell_result is not None:
                    # Map to required trades_df schema
                    trades_list.append({
                        'Entry_Date': sell_result['entry_date'],
                        'Exit_Date': sell_result['exit_date'],
                        'Entry_Price': sell_result['entry_price'],
                        'Exit_Price': sell_result['exit_price'],
                        'Quantity': sell_result['quantity'],
                        'P&L': sell_result['p&l'],
                        'Return_Pct': sell_result['return_pct'],
                        'Commission': sell_result['commission']
                    })

            # Track highest price since entry (for potential stop loss usage)
            if self.current_position > 0:
                current_price_for_high = float(row.get('High', row['Close']))
                if self._highest_price_since_entry is None:
                    self._highest_price_since_entry = current_price_for_high
                else:
                    self._highest_price_since_entry = max(self._highest_price_since_entry, current_price_for_high)


            equity_snapshots_list.append({
                'Date': row['Date'],
                'Portfolio_Value': self.current_capital + (self.current_position * float(row['Close'])),
                'Cash': self.current_capital,
                'Position_Value': self.current_position * float(row['Close']),
                'Hold_Signal': current_signal
            })

        trades_df = pd.DataFrame(trades_list)
        equity_curve_df = pd.DataFrame(equity_snapshots_list)
        return trades_df, equity_curve_df
        
        
    
    def _detect_signal_change(self, current_signal: int, previous_signal: int) -> Optional[str]:
        
        if current_signal == 0 and previous_signal == 1:
            return 'sell'
        elif current_signal == 1 and previous_signal == 0:
            return 'buy'
        else:
            return None
    
    def _execute_buy(self, price: float, date: pd.Timestamp) -> dict:
        quantity_to_buy = self._calculate_quantity(price)

        if quantity_to_buy <= 0:
            return {
                'quantity': 0,
                'price': price,
                'commission': 0.0,
                'success': False
            }

        total_cost = quantity_to_buy * price
        total_cost_with_commission = total_cost * (1.0 + self.commission)

        previous_position = self.current_position
        previous_cost_basis = (self.entry_price * previous_position) if self.entry_price is not None else 0.0

        # Update state
        self.current_capital -= total_cost_with_commission
        self.current_position += quantity_to_buy
        new_total_shares = self.current_position
        new_total_cost_basis = previous_cost_basis + total_cost
        self.entry_price = new_total_cost_basis / new_total_shares
        if previous_position == 0:
            self.entry_date = date
            self._highest_price_since_entry = price

        return {
            'quantity': quantity_to_buy,
            'price': price,
            'commission': self.commission,
            'success': True
        }
    
    def _execute_sell(self, price: float, date: pd.Timestamp) -> Optional[dict]:
        
        if self.current_position == 0 or self.entry_price is None or self.entry_date is None:
            return None

        quantity_to_sell = self.current_position

        gross_proceeds = quantity_to_sell * price
        sell_commission_cost = gross_proceeds * self.commission
        net_proceeds = gross_proceeds - sell_commission_cost

        pnl_gross = (price - self.entry_price) * quantity_to_sell
        # Approximate total commission across round-trip (buy already deducted from cash)
        round_trip_commission = (quantity_to_sell * self.entry_price * self.commission) + sell_commission_cost
        pnl_net = pnl_gross - sell_commission_cost  # buy commission already impacted cash at entry

        sell_record = {
            'quantity': int(quantity_to_sell),
            'entry_price': float(self.entry_price),
            'exit_price': float(price),
            'entry_date': self.entry_date,
            'exit_date': date,
            'p&l': float(pnl_net),
            'return_pct': float((price - self.entry_price) / self.entry_price),
            'commission': float(round_trip_commission)
        }

        # Update state
        self.current_capital += net_proceeds
        self.current_position = 0
        self.entry_price = None
        self.entry_date = None
        self._highest_price_since_entry = None

        return sell_record

    def _calculate_quantity(self, price: float) -> int:
        if price <= 0:
            return 0
        max_affordable = int(self.current_capital // (price * (1.0 + self.commission)))
        return max(0, max_affordable)
    
    def _check_stop_loss(self, current_price: float, date: pd.Timestamp) -> Optional[dict]:
        
        if self.stop_loss_manager is None or self.current_position == 0:
            return None
        
        # Check if stop loss should trigger
        should_trigger, stop_price = self.stop_loss_manager.check_stop_loss(
            entry_price=self.entry_price,
            current_price=current_price,
            highest_price_since_entry=self._get_highest_price_since_entry()
        )
        
        if should_trigger:
            return self._execute_sell(price=stop_price, date=date)
        
        return None
    
    def _get_highest_price_since_entry(self) -> float:
        return float(self._highest_price_since_entry) if self._highest_price_since_entry is not None else 0.0

