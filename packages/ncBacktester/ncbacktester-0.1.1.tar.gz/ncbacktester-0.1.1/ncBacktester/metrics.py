from typing import Dict, Any, Optional
import pandas as pd
import numpy as np


class MetricsCalculator:
   
    def __init__(
        self,
        trades_df: pd.DataFrame,
        equity_curve: pd.DataFrame,
        initial_capital: float,
        risk_free_rate: float = 0.02
    ):
        
        self.trades_df = trades_df.copy()
        self.equity_curve = equity_curve.copy()
        self.initial_capital = initial_capital
        self.risk_free_rate = risk_free_rate
    
    def calculate_all_metrics(
        self,
        benchmark_returns: Optional[pd.Series] = None,
        periods_per_year: int = 252
    ) -> Dict[str, Any]:
        
        metrics = {}

        metrics['sharpe_ratio'] = self.calculate_sharpe_ratio(
            periods_per_year=periods_per_year
        )
        metrics['sortino_ratio'] = self.calculate_sortino_ratio(
            periods_per_year=periods_per_year
        )
        metrics['annualized_return'] = self.calculate_annualized_return()
        metrics['max_drawdown'] = self.calculate_max_drawdown()
        metrics['total_return'] = self.calculate_total_return()

        metrics['beta'] = self.calculate_beta(
            benchmark_returns=benchmark_returns
        )
        metrics['alpha'] = self.calculate_alpha(
            benchmark_returns=benchmark_returns, 
            periods_per_year=periods_per_year
        )

        trade_stats = self.calculate_trade_statistics()

        metrics.update(trade_stats)

        return metrics

    def calculate_sharpe_ratio(self, periods_per_year: int = 252) -> float:
        """
        Calculate Sharpe Ratio.
        """
        daily_returns = self.equity_curve['Portfolio_Value'].pct_change().dropna()
        
        if daily_returns.empty:
            return np.nan

        #mean and std 
        mean_daily_returns = daily_returns.mean()
        std_daily_returns = daily_returns.std()

        # Handle zero standard deviation
        if std_daily_returns == 0:
            return np.nan

        #daily risk free rate 
        daily_risk_free_rate = self.risk_free_rate / periods_per_year

        #Daily sharpe ratio 
        daily_sharpe = (mean_daily_returns - daily_risk_free_rate) / std_daily_returns

        #Yearly sharpe ratio 
        annualized_sharpe = daily_sharpe * np.sqrt(periods_per_year)

        return annualized_sharpe
        
    
    def calculate_sortino_ratio(self, periods_per_year: int = 252) -> float:
        """
        Calculate Sortino Ratio.
        """
        daily_returns = self.equity_curve['Portfolio_Value'].pct_change().dropna()
        
        if daily_returns.empty:
            return np.nan

        #mean
        mean_daily_returns = daily_returns.mean()

        #daily risk free rate 
        daily_risk_free_rate = self.risk_free_rate / periods_per_year 
        
        # Use daily risk-free rate as the target
        target = daily_risk_free_rate

        #filtering for low returns 
        target_deviations = daily_returns - target 

        #set all positive values to 0 
        downside_diffs = target_deviations.clip(upper=0)

        #Downside Deviation
        squared_deviations = downside_diffs**2
        downside_variance = squared_deviations.mean()
        
        # Handle zero downside deviation
        if downside_variance == 0:
            # If numerator is positive, ratio is infinite (infinitely good)
            if (mean_daily_returns - target) > 0:
                return np.inf
            # If numerator is also zero, ratio is 0
            else:
                return 0.0
            
        down_side_deviation = np.sqrt(downside_variance)

        daily_sortino = (mean_daily_returns - target) / down_side_deviation

        annualized_sortino = daily_sortino * np.sqrt(periods_per_year)

        return annualized_sortino

    def calculate_annualized_return(self) -> float:
        """
        Calculate Annualized Return.
        
        Formula: Annualized Return = (Final Value / Initial Value) ^ (1 / years) - 1
        """
        final_value = self.equity_curve['Portfolio_Value'].iloc[-1]
        initial_value = self.initial_capital
        
        # Ensure dates are datetime objects for subtraction
        start_date = pd.to_datetime(self.equity_curve['Date'].iloc[0])
        end_date = pd.to_datetime(self.equity_curve['Date'].iloc[-1])
        
        num_days = (end_date - start_date).days
        
        # Handle cases with no duration or single day
        if num_days <= 0:
            # Return simple total return if no time has passed
            return (final_value / initial_value) - 1 

        num_years = num_days / 365.25
        
        total_return_factor = final_value / initial_value
        
        # (Final / Initial) ^ (1 / years) - 1
        annualized_return = (total_return_factor ** (1 / num_years)) - 1
        
        return annualized_return
    
    
    def calculate_beta(
        self,
        benchmark_returns: Optional[pd.Series] = None
    ) -> float:
        """
        Calculate Beta (sensitivity to benchmark).
        """
        if benchmark_returns is None:
            return np.nan

        daily_returns = self.equity_curve['Portfolio_Value'].pct_change().dropna()
        
        if daily_returns.empty:
            return np.nan

        #inner join benchmark and our returns 
        aligned_portfolio, aligned_benchmark = daily_returns.align(benchmark_returns, join = 'inner')
        
        if aligned_portfolio.empty or aligned_benchmark.empty:
            return np.nan

        #find covariance and variance of benchmark 
        covariance = aligned_portfolio.cov(aligned_benchmark)
        benchmark_variance = aligned_benchmark.var()
        
        if benchmark_variance == 0:
            return np.nan

        #beta calculation
        beta = covariance / benchmark_variance

        return beta 

    def calculate_alpha(
        self,
        benchmark_returns: Optional[pd.Series] = None,
        periods_per_year: int = 252
    ) -> float:
        """
        Calculate Alpha (excess return vs benchmark).
        """
        if benchmark_returns is None:
            return np.nan

        daily_returns = self.equity_curve['Portfolio_Value'].pct_change().dropna()
        
        #beta 
        beta = self.calculate_beta(benchmark_returns=benchmark_returns)
        
        # Handle case where beta couldn't be calculated
        if pd.isna(beta):
            return np.nan

        #inner join benchmark and our returns 
        aligned_portfolio, aligned_benchmark = daily_returns.align(benchmark_returns, join = 'inner')
        
        if aligned_portfolio.empty or aligned_benchmark.empty:
            return np.nan

        #portfolio and benchmark returns 
        mean_portfolio_returns = aligned_portfolio.mean()
        mean_benchmark_returns = aligned_benchmark.mean()
        
        #risk free rate
        daily_risk_free_rate = self.risk_free_rate / periods_per_year

        #alpha
        daily_alpha = mean_portfolio_returns - (daily_risk_free_rate + beta * (mean_benchmark_returns - daily_risk_free_rate))

        #annualized alpha
        annualized_alpha = daily_alpha * periods_per_year

        return annualized_alpha

    
    def calculate_max_drawdown(self) -> float:
        """
        Calculate Maximum Drawdown.
        """
        equity_series = self.equity_curve['Portfolio_Value']
        
        #running maximum 
        running_max = equity_series.cummax()

        #Drawdown at each point
        drawdown = (running_max - equity_series) / running_max

        #max draw down
        max_drawdown = drawdown.max()

        return max_drawdown

    def calculate_total_return(self) -> float:
        """
        Calculate Total Return (simple return from start to end).
        """
        final_value = self.equity_curve['Portfolio_Value'].iloc[-1]
        initial_value = self.initial_capital
        
        if initial_value == 0:
            return np.nan

        total_return = (final_value / initial_value) - 1

        return total_return 
        
    
    def calculate_trade_statistics(self) -> Dict[str, Any]:
        """
        Calculate basic trade statistics.
        """
        trades_df = self.trades_df

        total_trades = trades_df.shape[0]

        if total_trades == 0:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0
            }

        winning_trades = int((trades_df['P&L'] > 0).sum())
        losing_trades = int((trades_df['P&L'] < 0).sum())

        if total_trades > 0:
            win_rate = winning_trades / total_trades
        else:
            win_rate = 0.0

        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate
        }

