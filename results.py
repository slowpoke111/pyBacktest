from dataclasses import dataclass
from typing import List
from pyBacktest.tradeTypes import Holding
import pandas as pd

@dataclass
class BacktestResult:
    final_value: float
    transactions: List[Holding]
    strategy: 'Strategy'

    def returns(self) -> pd.Series:
        prices = [t.pricePerShare for t in self.transactions]
        return pd.Series(prices).pct_change().dropna()