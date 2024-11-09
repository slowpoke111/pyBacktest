# Stock Trading Backtest Framework

A Python framework for backtesting trading strategies with support for multiple order types and technical indicators.

## Features

### Trading Operations
- [x] Market Orders (Buy/Sell)
- [x] Limit Orders
- [x] GTC (Good Till Cancelled) Orders
- [x] Commission Handling
  - [x] Flat Fee
  - [x] Percentage
  - [x] Per Share

### Technical Indicators
- [x] Simple Moving Average (SMA)
- [x] Exponential Moving Average (EMA)
- [x] Relative Strength Index (RSI)
- [x] Bollinger Bands
- [x] MACD (Moving Average Convergence Divergence)
- [x] Crossover Detection

### Portfolio Management
- [x] Position Tracking
- [x] Transaction History
- [x] Portfolio Valuation
- [x] Cash Management

## Example

```python
import pyBacktest as pbt
from pyBacktest.strategy import Strategy
from pyBacktest.utils import calculateSMA, detectCrossover
from pyBacktest.types import TradeType
from datetime import datetime
import pandas as pd

def maxBuyableShares(price: float, cash: float) -> int:
    return int(cash / price)

class SimpleMovingAverageCrossover(Strategy):
    def setup(self) -> None:
        self.sma20:pd.Series = calculateSMA(self.data['Close'], 20)
        self.sma50:pd.Series = calculateSMA(self.data['Close'], 50)
    

    def next(self, row: pd.Series) -> None:
        if len(self.data['Close']) < 51:
            return

        current_price:float = row['Close']
        current_sma20:float = self.sma20[row.name]
        current_sma50:float = self.sma50[row.name]
        position:int = self.get_position()

        if current_sma20 > current_sma50:
            numShares = maxBuyableShares(current_price, self.backtest.cash)
            if numShares > 0:
                self.backtest.trade(TradeType.BUY, numShares, current_price)
    
        elif current_sma20 < current_sma50 and position > 0:
            sharesToSell = max(1, position // 3)
            self.backtest.trade(TradeType.SELL, sharesToSell, current_price)
    
if __name__ == "__main__":
    backtest = pbt.Backtest(
        "PG",
        1000.0,
        strategy=SimpleMovingAverageCrossover(),
        startDate=datetime(2023, 1, 1),
        endDate=datetime(2024, 1, 1)
    )
    results = backtest.run()
    print(f"Final Portfolio Value: ${results['final_value']:,.2f}")
```
