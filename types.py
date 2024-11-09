from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class TradeType(Enum):
    BUY = 1
    SELL = 2
    SHORT = 3
    STOP = 4
    COVER = 5
    LIMIT = 6
    GTC = 7
    Cancel = 8
    MARKET_BUY = 9
    MARKET_SELL = 10


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
