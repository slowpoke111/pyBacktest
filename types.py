from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

class TradeType(Enum):
    BUY = 1
    SELL = 2
    SHORT = 3
    STOP = 4
    COVER = 5
    GTC = 6
    Cancel = 7
    MARKET_BUY = 8
    MARKET_SELL = 9
    SHORT_COVER = 10
    LIMIT_BUY = 11
    LIMIT_SELL = 12


@dataclass
class Holding:
    tradeType: TradeType
    ticker: str
    commission: float
    executedSuccessfully: bool
    numShares: int
    totalCost: float


@dataclass
class Transaction:
    tradeType: TradeType
    ticker: str
    commission: float
    executedSuccessfully: bool
    numShares: int
    pricePerShare: float
    totalCost: float
    date: datetime
    profitLoss: float = 0.0
    notes: str = ""


@dataclass
class Order:
    tradeType: TradeType
    ticker: str
    numShares: int
    targetPrice: float
    duration: str  # 'DAY' or 'GTC'
    orderDate: datetime
    active: bool = True
    limitPrice: Optional[float] = None
