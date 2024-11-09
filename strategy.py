from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd
from pyBacktest.backtest import Backtest, TradeType
from pyBacktest.utils import calculateSMA

class Strategy(ABC):
    def __init__(self) -> None:
        self.data: Optional[pd.DataFrame] = None
        self.current_position: int = 0
        self.backtest: Optional[Backtest] = None

    def initialize(self, backtest: Backtest) -> None:
        self.backtest = backtest
        self.data = backtest.hist
        self.setup()

    def setup(self) -> None:
        pass

    @abstractmethod
    def next(self, row: pd.Series) -> None:
        pass

    def get_position(self) -> int:
        return sum(h.numShares for h in self.backtest.holdings)

    def get_market_state(self) -> Dict[str, Any]:
        return {
            'cash': self.backtest.cash,
            'position': self.get_position(),
            'total_value': self.backtest.totalValue()
        }

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
            self.backtest.trade(TradeType.MARKET_BUY, 100)
        
        elif position > 0 and current_price < current_sma:
            self.backtest.trade(TradeType.MARKET_SELL, 100)

if __name__ == "__main__":
    from datetime import datetime
    
    backtest = Backtest(
        "AAPL",
        100000.0,
        strategy=SimpleMovingAverageCrossover(),
        startDate=datetime(2023, 1, 1),
        endDate=datetime(2024, 1, 1)
    )
    
    results = backtest.run()
    print(f"Final Portfolio Value: ${results['final_value']:,.2f}")
