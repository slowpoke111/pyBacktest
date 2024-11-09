from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TYPE_CHECKING
import pandas as pd
from pyBacktest.utils import calculateSMA

if TYPE_CHECKING:
    from pyBacktest.backtest import Backtest

class Strategy(ABC):
    def __init__(self) -> None:
        self.data: Optional[pd.DataFrame] = None
        self.current_position: int = 0
        self.backtest: Optional['Backtest'] = None

    def initialize(self, backtest: 'Backtest') -> None:
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
