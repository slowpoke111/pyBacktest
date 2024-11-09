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
from pyBacktest.utils import calculateSMA
from datetime import datetime
import pandas as pd

def maxBuyableShares(price: float, cash: float) -> int:
    return int(cash / price)

class SimpleMovingAverageCrossover(Strategy):
    def setup(self) -> None:
        self.sma20 = calculateSMA(self.data['Close'], 20)
    

    def next(self, row: pd.Series) -> None:
        if len(self.data) < 20:
            return
        current_price = row['Close']
        current_sma = self.sma20[row.name]
        position = self.get_position()
        if position == 0 and current_price > current_sma:
            self.backtest.trade(pbt.TradeType.MARKET_BUY, maxBuyableShares(current_price, self.backtest.cash))
        elif position > 0 and current_price < current_sma:
            self.backtest.trade(pbt.TradeType.MARKET_SELL, self.get_position())

if __name__ == "__main__":
    backtest = pbt.Backtest(
        "AAPL",
        1000.0,
        strategy=SimpleMovingAverageCrossover(),
        startDate=datetime(2023, 1, 1),
        endDate=datetime(2024, 1, 1)
    )
    results = backtest.run()
    print(f"Final Portfolio Value: ${results['final_value']:,.2f}")
```
