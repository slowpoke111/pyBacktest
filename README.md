# Stock Trading Backtest Framework

A Python framework for backtesting trading strategies with support for multiple order types and technical indicators. Licensed under the LGPL.

> Email ben567755 [at] gmail[.]com with questions
>

---
## Install
#### pip install pyBacktest
> Docs can be found in the wiki tab. Docs are a work in progress.
---

## Features

### **Trading Operations**
- [x] **Market Orders** (Buy/Sell)
- [x] **Limit Orders**
- [x] **GTC (Good Till Canceled) Orders**
- [x] **Short Selling** (Sell and Cover Short Positions)
- [x] **Commission Handling**
    - [x] Flat Fee
    - [x] Percentage
    - [x] Per Share
- [x] **Order Expiry Handling**
    - [x] Automatically cancels expired orders
- [x] **Order Queue Management**
    - [x] Pending Orders handled by priority queue

### **Technical Indicators**
- [x] **Simple Moving Average** (SMA)
- [x] **Exponential Moving Average** (EMA)
- [x] **Relative Strength Index** (RSI)
- [x] **Bollinger Bands**
- [x] **MACD** (Moving Average Convergence Divergence)
- [x] **Crossover Detection** (SMA, EMA, MACD)
- [x] **Volume Weighted Average Price** (VWAP)
- [x] **Average True Range** (ATR)
- [x] **Indicator Calculation Integration**
    - [x] SMA, EMA, MACD available within strategy context

### **Portfolio Management**
- [x] **Position Tracking**
    - [x] Track open positions and entry points
- [x] **Transaction History**
    - [x] Records details of executed trades
- [x] **Portfolio Valuation**
    - [x] Calculates current portfolio value based on market prices
- [x] **Cash Management**
    - [x] Tracks available cash for trades
- [x] **Performance Metrics**
    - [x] Risk metrics, returns, and other performance statistics (e.g., Sharpe ratio, Drawdown, etc.)



## Example

```python
import pyBacktest as pbt
from pyBacktest.strategy import Strategy
from pyBacktest.utils import calculateSMA, analyzeResults, calculateMACD
from pyBacktest.tradeTypes import TradeType
from datetime import datetime
import pandas as pd

class SMACross(Strategy):
    def setup(self) -> None:
        self.has_position = False
        self.entry_price = 0
        self.sma20 = calculateSMA(self.data['Close'], 20)
        self.sma50 = calculateSMA(self.data['Close'], 50)

    def step(self, row: pd.Series) -> None:
        if row.name not in self.sma20.index or row.name not in self.sma50.index:
            return

        if self.backtest.cash>row['Close'] and self.sma20[row.name] > self.sma50[row.name]:
            self.has_position = True
            self.entry_price = row['Close']
            self.backtest.trade(TradeType.BUY, int(self.backtest.cash*0.95/row["Close"]), row['Close'], "DAY")
        elif self.has_position and self.sma20[row.name] < self.sma50[row.name]:
            self.has_position = False
            self.backtest.trade(TradeType.SELL, self.current_position, row['Close'], row.name)

class MACDStrategy(Strategy):
    def setup(self) -> None:
        self.macd, self.signal, self.histogram = calculateMACD(self.data['Close'])

    def step(self, row: pd.Series) -> None:
        if row.name not in self.macd.index:
            return

        if self.histogram[row.name] > 0:
            numShares = int(self.backtest.cash / row['Close'])
            trade_cost = self.backtest.calculate_trade_cost(TradeType.BUY, numShares, row['Close'])
            if self.backtest.cash >= trade_cost:
                self.backtest.trade(TradeType.BUY, numShares, row['Close'], "DAY")
        elif self.histogram[row.name] < 0 and self.backtest.getPosition() > 0:
            numShares = self.backtest.getPosition()
            trade_cost = self.backtest.calculate_trade_cost(TradeType.SELL, numShares, row['Close'])
            if self.backtest.cash >= trade_cost:
                self.backtest.trade(TradeType.SELL, numShares, row['Close'], row.name)

if __name__ == "__main__":
    sma_backtest = pbt.Backtest(
        strategy=SMACross(),
        ticker='AAPL',
        commision=1.00,
        startDate=datetime(2020, 1, 1),
        endDate=datetime(2024, 1, 1), 
        cash=10000
    )
    
    macd_backtest = pbt.Backtest(
        strategy=MACDStrategy(),
        ticker='AAPL',
        commision=1.00,
        startDate=datetime(2020, 1, 1),
        endDate=datetime(2024, 1, 1), 
        cash=10000
    )
    
    sma_results = sma_backtest.run()
    macd_results = macd_backtest.run()
    
    analyzeResults(sma_results)
    analyzeResults(macd_results)
    
    comparison = pbt.utils.compareBacktests(sma_results, macd_results)
    print("\nComparison of SMA and MACD Strategies:")
    print(f"Final Value Difference: ${comparison['final_value_diff']:,.2f}")
    print(f"Total Return Difference: {comparison['total_return_diff']:.2f}%")
    print(f"Number of Transactions Difference: {comparison['num_transactions_diff']}")
    print(f"Better Strategy: {comparison['better_strategy']}")
```

---

## Diagrams
> Diagrams are not guaranteed to be up to date.
### Structure
```mermaid
classDiagram
    class Backtest {
        - strategy: Strategy
        - ticker: str
        - commission: float
        - startDate: datetime
        - endDate: datetime
        - cash: float
        + run() BacktestResult
        + trade(tradeType: TradeType, numShares: int, price: float, duration: str)
        + getPosition() int
        + calculate_trade_cost(tradeType: TradeType, numShares: int, price: float) float
    }

    class Strategy {
        # backtest: Backtest
        + setup() void
        + step(row: pd.Series) void
    }

    class SMACross {
        + setup() void
        + step(row: pd.Series) void
    }

    class MACDStrategy {
        + setup() void
        + step(row: pd.Series) void
    }

    Strategy <|-- SMACross
    Strategy <|-- MACDStrategy
    Backtest o--> Strategy
    Backtest o--> TradeType
    Backtest o--> Holding
    Backtest o--> Transaction
    Backtest o--> Order

    class TradeType {
        <<Enumeration>>
        + BUY
        + SELL
        + SHORT_SELL
        + STOP
        + COVER
        + GTC
        + MARKET_BUY
        + MARKET_SELL
        + SHORT_COVER
        + LIMIT_BUY
        + LIMIT_SELL
    }

    class Holding {
        - tradeType: TradeType
        - ticker: str
        - commission: float
        - executedSuccessfully: bool
        - numShares: int
        - totalCost: float
        - entryPrice: float
        - shortPosition: bool
    }

    class Transaction {
        - tradeType: TradeType
        - ticker: str
        - commission: float
        - executedSuccessfully: bool
        - numShares: int
        - pricePerShare: float
        - totalCost: float
        - date: datetime
        - profitLoss: float
        - notes: str
    }

    class Order {
        - tradeType: TradeType
        - ticker: str
        - numShares: int
        - targetPrice: float
        - duration: str
        - orderDate: datetime
        - active: bool
        - limitPrice: float
    }

    class Utils {
        + calculateSMA(data: pd.Series, period: int) pd.Series
        + calculateMACD(data: pd.Series, fastPeriod: int, slowPeriod: int, signalPeriod: int) tuple
        + analyzeResults(result: BacktestResult) dict
        + compareBacktests(result1: BacktestResult, result2: BacktestResult) dict
    }

    Backtest --> Utils

```

### Backtest callchain
```mermaid
sequenceDiagram
    participant User as User
    participant Backtest as Backtest
    participant Strategy as Strategy
    participant Utils as Utils
    participant TradeTypes as TradeType
    participant DataLoader as DataLoader
    participant Results as BacktestResult

    User->>Backtest: Initialize Backtest(ticker, strategy, dates, cash)
    Backtest->>DataLoader: Load Historical Data
    DataLoader-->>Backtest: Return Historical Data
    Backtest->>Strategy: Instantiate Strategy
    Backtest->>Strategy: Call setup()
    Strategy-->>Backtest: Initialize Strategy Variables

    loop For each data row
        Backtest->>Strategy: Call step(row)
        Strategy->>TradeTypes: Create Trade (if conditions met)
        TradeTypes-->>Backtest: Return Trade Details
        Backtest->>Backtest: Update Portfolio & Cash
    end

    Backtest->>Results: Generate Backtest Results
    Results-->>Backtest: Return BacktestResult Object

    User->>Utils: Analyze Results(BacktestResult)
    Utils-->>User: Return Metrics and Insights
    User->>Backtest: Compare Strategies(optional)
    Backtest->>Utils: CompareBacktests(results1, results2)
    Utils-->>User: Return Comparison Summary
```

### Components
```mermaid
graph TD
    A[Backtest Framework] --> B[Strategy Module]
    A --> C[Utils Module]
    A --> D[tradeTypes Module]
    A --> E[Data Handling]
    B --> F[Custom Strategies]
    C --> G[Indicator Calculations]
    C --> H[Risk Metrics]
    E --> I[Data Loader]
    E --> J[Data Validator]
    D --> K[TradeType Enum]
    D --> L[Order Class]
```

### State Diagram
```mermaid
stateDiagram-v2
    state Backtest {
        [*] --> Initialized
        Initialized --> Running : run()
        Running --> Paused : pause()
        Running --> Completed : all data processed
        Paused --> Running : resume()
        Completed --> Archived : save results
    }

    state Order {
        [*] --> Pending
        Pending --> Executed : conditions met
        Pending --> Expired : time elapsed
        Executed --> Completed : trade settled
        Completed --> Archived : recorded in transactions
    }
```
### Data Flow
```mermaid
graph TD
    A[Input Data] -->|Load| B[DataFrame]
    B -->|Validate| C[Backtest Engine]
    C -->|Feed| D[Strategy Execution]
    D -->|Generate| E[Trades]
    E -->|Record| F[Transactions]
    F -->|Summarize| G[Performance Analysis]
    G -->|Output| H[Results]
```
### Interaction Overview
```mermaid
sequenceDiagram
    participant User
    participant Backtest
    participant Strategy
    participant Utils
    User->>Backtest: Initialize Backtest
    Backtest->>Utils: Load and validate data
    Backtest->>Strategy: Setup
    loop For each data point
        Backtest->>Strategy: step()
        Strategy->>Backtest: trade()
    end
    Backtest->>Utils: Analyze Results
    Backtest->>User: Return Results
```

### Error Handling
```mermaid
flowchart TD
    A[Run Backtest] --> B[Trade Attempt]
    B -->|Funds Available| C[Execute Trade]
    B -->|Funds Insufficient| D[Raise InsufficientFundsError]
    C -->|Valid Trade| E[Update Transactions]
    C -->|Invalid Trade| F[Raise InvalidOrderError]
    E --> G[Continue Backtest]
    F --> G
    D --> G
```

### Dependincies 
```mermaid
graph TD
    A[SPDX Document: com.github.slowpoke111/pyBacktest] --> B[Numpy]
    A --> C[Pandas]
    A --> D[YFinance]
    A --> E[Typing Extensions]
    A --> F[GH Action: PyPI Publish]
    A --> G[GH Action: Checkout]
    A --> H[GH Action: Setup Python]

    B -->|Package Manager| P1[pypi/numpy]
    C -->|Package Manager| P2[pypi/pandas]
    D -->|Package Manager| P3[pypi/yfinance]
    E -->|Package Manager| P4[pypi/typing-extensions]
    F -->|Package Manager| P5[githubactions/pypa/gh-action-pypi-publish]
    G -->|Package Manager| P6[githubactions/actions/checkout]
    H -->|Package Manager| P7[githubactions/actions/setup-python]
```
